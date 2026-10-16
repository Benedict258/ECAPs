"""Discovery/routing tests. Everything runs on 127.0.0.1 only; nothing here proves behaviour on a real LAN."""
import json
import os
import select
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
import pytest
from ecaps import cluster
from ecaps.backend import MockBackend
from ecaps.cluster import ClusterNode, Discovery, PeerTable, make_server

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def free_udp_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def wait_for(cond, timeout=10.0, step=0.05):
    end = time.time() + timeout
    while time.time() < end:
        if cond(): return True
        time.sleep(step)
    return False


def post(port, body, headers=None, path="/generate", timeout=30):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", json.dumps(body).encode() if not isinstance(body, bytes) else body,
                                 {"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def getj(port, path):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5) as r:
        return json.loads(r.read())


# ---------------------------------------------------------------- peer table / discovery
def test_peer_table_ttl_and_ignores_self():
    t = PeerTable("A", ttl=5)
    t.update("A", "127.0.0.1", 1, {"active": 0}, now=0)
    t.update("B", "127.0.0.1", 2, {"active": 1}, now=0)
    assert [p["id"] for p in t.live(now=1)] == ["B"]
    assert t.live(now=6) == []


def test_discovery_two_nodes_find_each_other_and_ignore_garbage():
    pa, pb = free_udp_port(), free_udp_port()
    ta, tb = PeerTable("A", 5), PeerTable("B", 5)
    da = Discovery("A", 9001, pa, ta, lambda: {"active": 0, "capacity": 1}, [("127.0.0.1", pb)], 0.1, "127.0.0.1").start()
    db = Discovery("B", 9002, pb, tb, lambda: {"active": 2, "capacity": 1}, [("127.0.0.1", pa)], 0.1, "127.0.0.1").start()
    try:
        junk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for payload in (b"not json", b'{"magic":"other"}', b'{"magic":"ecaps-node/1","id":"X","port":70000,"load":{"active":0}}',
                        b'{"magic":"ecaps-node/1","id":"Y","port":1,"load":{"active":"many"}}'):
            junk.sendto(payload, ("127.0.0.1", pa))
        assert wait_for(lambda: [p["id"] for p in ta.live()] == ["B"] and [p["id"] for p in tb.live()] == ["A"])
        b = ta.live()[0]
        assert b["port"] == 9002 and b["load"]["active"] == 2 and b["host"] == "127.0.0.1"
        assert [p["id"] for p in ta.live()] == ["B"]          # garbage never became a peer
    finally:
        da.stop(); db.stop()


def test_discovery_via_real_udp_broadcast_on_loopback():
    """Uses the loopback broadcast address; needs SO_REUSEPORT so two nodes can share one port."""
    if not hasattr(socket, "SO_REUSEPORT"):
        pytest.skip("SO_REUSEPORT not available on this platform (typical on Windows): broadcast-on-one-host test not run")
    port = free_udp_port()
    ta, tb = PeerTable("A", 5), PeerTable("B", 5)
    tgt = [("127.255.255.255", port)]
    da = Discovery("A", 9101, port, ta, lambda: {"active": 0, "capacity": 1}, tgt, 0.1, "0.0.0.0").start()
    db = Discovery("B", 9102, port, tb, lambda: {"active": 0, "capacity": 1}, tgt, 0.1, "0.0.0.0").start()
    try:
        assert wait_for(lambda: [p["id"] for p in ta.live()] == ["B"] and [p["id"] for p in tb.live()] == ["A"], timeout=8)
    finally:
        da.stop(); db.stop()


# ---------------------------------------------------------------- routing decisions
class SlowBackend(MockBackend):
    def __init__(self, delay): super().__init__(lambda p: "ok"); self.delay = delay
    def generate(self, *a, **k):
        time.sleep(self.delay); return super().generate(*a, **k)


def node_with_peer(peer_active, delay=0.0):
    peers = PeerTable("A")
    if peer_active is not None: peers.update("B", "127.0.0.1", 9, {"active": peer_active, "capacity": 1})
    n = ClusterNode("A", SlowBackend(delay), peers)
    calls = []
    n._forward = lambda peer, req: calls.append(peer["id"]) or {"text": "remote", "served_by": "B"}
    return n, calls


def test_idle_node_serves_locally():
    n, calls = node_with_peer(0)
    r = n.generate({"prompt": "x"})
    assert r["served_by"] == "A" and calls == []


def test_busy_node_hands_off_to_idle_peer():
    n, calls = node_with_peer(0, delay=0.3)
    t = threading.Thread(target=n.generate, args=({"prompt": "first"},)); t.start()
    assert wait_for(lambda: n.load()["active"] == 1)
    r = n.generate({"prompt": "second"})
    t.join()
    assert calls == ["B"] and r["served_by"] == "B" and r["forwarded_from"] == "A"


def test_busy_node_keeps_request_if_peer_is_not_less_busy():
    n, calls = node_with_peer(1, delay=0.3)
    t = threading.Thread(target=n.generate, args=({"prompt": "first"},)); t.start()
    assert wait_for(lambda: n.load()["active"] == 1)
    r = n.generate({"prompt": "second"}); t.join()
    assert calls == [] and r["served_by"] == "A"


def test_forwarded_request_is_never_forwarded_again():
    n, calls = node_with_peer(0, delay=0.3)
    t = threading.Thread(target=n.generate, args=({"prompt": "first"},)); t.start()
    assert wait_for(lambda: n.load()["active"] == 1)
    r = n.generate({"prompt": "second"}, hops=1); t.join()
    assert calls == [] and r["served_by"] == "A"


def test_forward_failure_falls_back_to_local_and_drops_peer():
    n, _ = node_with_peer(0, delay=0.3)
    def boom(peer, req): raise ConnectionError("down")
    n._forward = boom
    t = threading.Thread(target=n.generate, args=({"prompt": "first"},)); t.start()
    assert wait_for(lambda: n.load()["active"] == 1)
    r = n.generate({"prompt": "second"}); t.join()
    assert r["served_by"] == "A" and n.stats["forward_failures"] == 1 and n.peers.live() == []
    assert n.load()["active"] == 0


def test_http_validation_and_token():
    n = ClusterNode("A", SlowBackend(0), PeerTable("A"), token="s3cret")
    srv = make_server(n, port=0); threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    try:
        with pytest.raises(urllib.error.HTTPError) as e: post(port, {"prompt": "x"})
        assert e.value.code == 401
        ok = post(port, {"prompt": "x"}, {"X-ECAPS-Token": "s3cret"})
        assert ok["served_by"] == "A" and ok["is_mock"] is True
        with pytest.raises(urllib.error.HTTPError) as e: post(port, {"nope": 1}, {"X-ECAPS-Token": "s3cret"})
        assert e.value.code == 400
        with pytest.raises(urllib.error.HTTPError) as e: post(port, b"not json", {"X-ECAPS-Token": "s3cret"})
        assert e.value.code == 400
        assert getj(port, "/load")["active"] == 0
    finally:
        srv.shutdown(); srv.server_close()


# ---------------------------------------------------------------- real multi-process test on localhost
class Proc:
    def __init__(self, node_id, udp, peer_udps, delay):
        args = [sys.executable, "-m", "ecaps.cluster", "--id", node_id, "--port", "0", "--discovery-port", str(udp),
                "--interval", "0.15", "--ttl", "2", "--mock", "--mock-delay", str(delay)]
        for pu in peer_udps: args += ["--peer", f"127.0.0.1:{pu}"]
        self.p = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.port = None
        end = time.time() + 15
        while time.time() < end and self.port is None:
            if select.select([self.p.stdout], [], [], 0.5)[0]:
                line = self.p.stdout.readline()
                if line.startswith("READY"):
                    self.port = int(line.split("http=")[1].split()[0])
            if self.p.poll() is not None: break
        assert self.port, f"node {node_id} did not start"

    def stop(self):
        self.p.terminate()
        try: self.p.wait(5)
        except subprocess.TimeoutExpired: self.p.kill()


@pytest.fixture
def three_nodes():
    udp = {k: free_udp_port() for k in "ABC"}
    procs = {k: Proc(k, udp[k], [udp[o] for o in "ABC" if o != k], 0.4 if k == "A" else 0.1) for k in "ABC"}
    try:
        assert wait_for(lambda: all(len(getj(p.port, "/peers")["peers"]) == 2 for p in procs.values()),
                        timeout=10), "discovery did not converge"
        yield procs
    finally:
        for p in procs.values(): p.stop()


def test_multiprocess_discovery_and_handoff(three_nodes):
    A = three_nodes["A"]
    for k in "BC":
        assert sorted(p["id"] for p in getj(three_nodes[k].port, "/peers")["peers"]) == sorted(set("ABC") - {k})
    with ThreadPoolExecutor(6) as ex:
        results = list(ex.map(lambda i: post(A.port, {"prompt": f"req {i}", "max_tokens": 8}), range(6)))
    assert len(results) == 6 and all(r["text"] for r in results)
    served = {r["served_by"] for r in results}
    assert served & {"B", "C"}, f"A never handed anything to a peer: {served}"
    assert all(r["forwarded_from"] == "A" for r in results if r["served_by"] != "A")
    assert all(r["is_mock"] for r in results)                    # dummy backend, never a measurement


def test_multiprocess_peer_dies_requests_still_served(three_nodes):
    A = three_nodes["A"]
    three_nodes["B"].stop(); three_nodes["C"].stop()
    with ThreadPoolExecutor(4) as ex:
        results = list(ex.map(lambda i: post(A.port, {"prompt": f"req {i}", "max_tokens": 8}), range(4)))
    assert len(results) == 4 and {r["served_by"] for r in results} == {"A"}
    assert wait_for(lambda: getj(A.port, "/peers")["peers"] == [], timeout=6)    # TTL expiry removes the dead peers
