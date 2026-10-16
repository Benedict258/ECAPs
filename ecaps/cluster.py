"""LAN node discovery and request routing. PROTOTYPE, tested on localhost only (several processes on 127.0.0.1).

Scope: more nodes serve more users. A request is served whole by ONE node; a busy node may hand it to a less-busy
peer. A single model is never split across nodes. Not implemented: mDNS, authentication of announcements,
encryption, load prediction, fairness. Peer load comes from periodic UDP announcements, so it can be a second or so stale.

Security notes: the generate endpoint is unauthenticated unless a shared token is set; it binds to 127.0.0.1 by
default (pass --host 0.0.0.0 deliberately to serve a LAN). A peer's address is taken from the UDP packet's source IP,
never from the address the packet claims, so an announcement cannot redirect traffic to a third host.
"""
from __future__ import annotations

import argparse
import json
import socket
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Optional

MAGIC = "ecaps-node/1"
MAX_BODY = 1 << 20
MAX_TOKENS_CAP = 512
HOP_HEADER = "X-ECAPS-Hops"
TOKEN_HEADER = "X-ECAPS-Token"


# ------------------------------------------------------------------ peers + discovery
class PeerTable:
    def __init__(self, self_id: str, ttl: float = 5.0):
        self.self_id, self.ttl = self_id, ttl
        self._peers: dict[str, dict] = {}
        self._lock = threading.Lock()

    def update(self, node_id: str, host: str, port: int, load: dict, now: float | None = None):
        if node_id == self.self_id:
            return
        with self._lock:
            self._peers[node_id] = {"id": node_id, "host": host, "port": port, "load": load,
                                    "seen": time.monotonic() if now is None else now}

    def live(self, now: float | None = None) -> list[dict]:
        now = time.monotonic() if now is None else now
        with self._lock:
            return [dict(p) for p in self._peers.values() if now - p["seen"] <= self.ttl]

    def drop(self, node_id: str):
        with self._lock:
            self._peers.pop(node_id, None)


class Discovery:
    """UDP announce/listen. `targets` defaults to the broadcast address; tests pass explicit localhost ports."""

    def __init__(self, node_id: str, service_port: int, discovery_port: int, peers: PeerTable,
                 get_load: Callable[[], dict], targets: Optional[list[tuple[str, int]]] = None,
                 interval: float = 1.0, bind_host: str = "0.0.0.0"):
        self.id, self.service_port, self.port, self.peers, self.get_load = node_id, service_port, discovery_port, peers, get_load
        self.targets = targets or [("255.255.255.255", discovery_port)]
        self.interval, self.bind_host = interval, bind_host
        self._stop = threading.Event()
        self.rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rx.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            try: self.rx.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError: pass
        self.rx.bind((bind_host, discovery_port))
        self.rx.settimeout(0.2)
        self.tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tx.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._threads: list[threading.Thread] = []

    def announce_once(self):
        msg = json.dumps({"magic": MAGIC, "id": self.id, "port": self.service_port, "load": self.get_load()}).encode()
        for t in self.targets:
            try: self.tx.sendto(msg, t)
            except OSError: pass          # no route / network down: keep running, announce again later

    def _send_loop(self):
        while not self._stop.is_set():
            self.announce_once()
            self._stop.wait(self.interval)

    def _recv_loop(self):
        while not self._stop.is_set():
            try:
                data, (src_ip, _) = self.rx.recvfrom(4096)
            except (socket.timeout, OSError):
                continue
            try:
                m = json.loads(data)
                if m.get("magic") != MAGIC:
                    continue
                port, load = int(m["port"]), m.get("load") or {}
                if not (0 < port < 65536) or not isinstance(load.get("active"), int):
                    continue
                self.peers.update(str(m["id"])[:64], src_ip, port, {"active": load["active"], "capacity": int(load.get("capacity", 1))})
            except (ValueError, KeyError, TypeError):
                continue                   # malformed packet: ignore

    def start(self):
        for fn in (self._send_loop, self._recv_loop):
            t = threading.Thread(target=fn, daemon=True); t.start(); self._threads.append(t)
        return self

    def stop(self):
        self._stop.set()
        for t in self._threads: t.join(1)
        self.rx.close(); self.tx.close()


# ------------------------------------------------------------------ serving + routing
class ClusterNode:
    def __init__(self, node_id: str, backend, peers: PeerTable, capacity: int = 1,
                 token: Optional[str] = None, forward_timeout: float = 120.0):
        self.id, self.backend, self.peers, self.capacity = node_id, backend, peers, capacity
        self.token, self.forward_timeout = token, forward_timeout
        self._active = 0
        self._lock = threading.Lock()
        self._sem = threading.Semaphore(capacity)
        self.stats = {"served_local": 0, "forwarded": 0, "forward_failures": 0}

    def load(self) -> dict:
        with self._lock:
            return {"active": self._active, "capacity": self.capacity}

    def _pick_peer(self, local_active: int) -> Optional[dict]:
        """Forward only to a peer that announced strictly less load than this node currently has."""
        cands = [p for p in self.peers.live() if p["load"]["active"] < local_active]
        return min(cands, key=lambda p: (p["load"]["active"], p["id"])) if cands else None

    def generate(self, req: dict, hops: int = 0) -> dict:
        peer = None
        with self._lock:
            local_active = self._active
            if hops == 0 and local_active > 0:         # a forwarded request (hops >= 1) is never forwarded again
                peer = self._pick_peer(local_active)
            if peer is None:
                self._active += 1                       # counted while queued or running
        if peer is not None:
            try:
                out = self._forward(peer, req)
                with self._lock: self.stats["forwarded"] += 1
                out["forwarded_from"] = self.id
                return out
            except Exception:                           # peer gone or erroring: serve it here instead
                self.peers.drop(peer["id"])
                with self._lock:
                    self.stats["forward_failures"] += 1
                    self._active += 1
        try:
            with self._sem:
                g = self.backend.generate(str(req["prompt"]), max_tokens=min(int(req.get("max_tokens", 64)), MAX_TOKENS_CAP),
                                          temperature=0.0, seed=int(req.get("seed", 0)), json_schema=req.get("json_schema"))
            with self._lock: self.stats["served_local"] += 1
            return {"text": g.text, "n_tokens": g.n_tokens, "ttft_s": g.ttft_s, "total_s": g.total_s,
                    "served_by": self.id, "forwarded_from": None, "is_mock": bool(getattr(g, "is_mock", False))}
        finally:
            with self._lock: self._active -= 1

    def _forward(self, peer: dict, req: dict) -> dict:
        headers = {"Content-Type": "application/json", HOP_HEADER: "1"}
        if self.token: headers[TOKEN_HEADER] = self.token
        r = urllib.request.Request(f"http://{peer['host']}:{peer['port']}/generate", json.dumps(req).encode(), headers)
        with urllib.request.urlopen(r, timeout=self.forward_timeout) as resp:
            return json.loads(resp.read())


def make_server(node: ClusterNode, host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    class H(BaseHTTPRequestHandler):
        def _send(self, code, obj):
            b = json.dumps(obj).encode()
            self.send_response(code); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

        def do_GET(self):
            if self.path == "/load": self._send(200, {"id": node.id, **node.load()})
            elif self.path == "/peers": self._send(200, {"id": node.id, "peers": node.peers.live(), "stats": node.stats})
            else: self._send(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/generate": return self._send(404, {"error": "not found"})
            if node.token and self.headers.get(TOKEN_HEADER) != node.token:
                return self._send(401, {"error": "bad or missing token"})
            try:
                n = int(self.headers.get("Content-Length", "0"))
                if n <= 0 or n > MAX_BODY: return self._send(413, {"error": "bad body size"})
                req = json.loads(self.rfile.read(n))
                if not isinstance(req, dict) or not isinstance(req.get("prompt"), str): raise ValueError("prompt required")
                hops = int(self.headers.get(HOP_HEADER, "0"))
            except (ValueError, TypeError) as e:
                return self._send(400, {"error": str(e)})
            try:
                self._send(200, node.generate(req, hops))
            except Exception as e:
                self._send(500, {"error": f"{type(e).__name__}: {e}"})

        def log_message(self, *a): pass

    return ThreadingHTTPServer((host, port), H)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run a cluster-capable node (PROTOTYPE, localhost-tested).")
    ap.add_argument("--id", required=True); ap.add_argument("--host", default="127.0.0.1"); ap.add_argument("--port", type=int, default=8800)
    ap.add_argument("--discovery-port", type=int, default=47800)
    ap.add_argument("--peer", action="append", default=[], help="host:udp_port to announce to (default: LAN broadcast)")
    ap.add_argument("--interval", type=float, default=1.0); ap.add_argument("--ttl", type=float, default=5.0)
    ap.add_argument("--token", default=None); ap.add_argument("--capacity", type=int, default=1)
    ap.add_argument("--llama-url", default="http://127.0.0.1:8080")
    ap.add_argument("--mock", action="store_true", help="DUMMY backend")
    ap.add_argument("--mock-delay", type=float, default=0.0, help="seconds per request for the mock backend")
    a = ap.parse_args(argv)
    from .backend import LlamaServerBackend, MockBackend
    if a.mock:
        print("WARNING: --mock is a DUMMY backend.", flush=True)
        be = MockBackend(lambda p: "dummy output " * 4, tokens_per_s=4 / a.mock_delay if a.mock_delay > 0 else 2000.0)
    else:
        be = LlamaServerBackend(a.llama_url)
    peers = PeerTable(a.id, a.ttl)
    node = ClusterNode(a.id, be, peers, a.capacity, a.token)
    srv = make_server(node, a.host, a.port)
    targets = [(h, int(p)) for h, p in (x.rsplit(":", 1) for x in a.peer)] or None
    Discovery(a.id, srv.server_address[1], a.discovery_port, peers, node.load, targets, a.interval).start()
    print(f"READY id={a.id} http={srv.server_address[1]} udp={a.discovery_port}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
