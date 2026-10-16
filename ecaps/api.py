"""Read-only management API for monitoring a node: GET /status, /models, /metrics (JSON).
Binds to 127.0.0.1 by default and has NO authentication: do not expose it to an untrusted network."""
from __future__ import annotations

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import psutil

from . import __version__
from .model_manager import CATALOG, required_gb
from .node import Node


def status(node: Node) -> dict:
    with node.lock:
        return {"version": __version__, "stage": "research prototype", "uptime_s": round(time.time() - node.started, 3),
                "backend": {"is_mock": bool(getattr(node._backend, "is_mock", False))},
                "power": {"battery_pct": node.battery_pct, "solar": node.solar, "plan": node.plan.as_dict()},
                "memory_budget_gb": node.power.budget_gb,
                "memory_budget_note": "software setting, not physical RAM",
                "device": type(node.sensors).__name__,
                "last_sensors": dict(node.agent.last_snapshot),
                "cloud_fallback": "off (stub)"}


def models(node: Node, models_dir: str | Path = "models", quant: str = "q4") -> dict:
    rows = []
    for t in sorted(CATALOG, key=lambda t: t.params_b):
        need = required_gb(t, quant)["required_gb"]
        rows.append({"name": t.name, "params_b": t.params_b, "licence": t.licence,
                     "estimated_required_gb": round(need, 2), "fits_budget": need <= node.power.budget_gb,
                     "active": t.name == node.plan.tier,
                     "gguf_present": (Path(models_dir) / f"{t.name}-Q4_K_M.gguf").exists()})
    return {"quant": quant, "budget_gb": node.power.budget_gb, "models": rows,
            "note": "Sizes are estimates from the model manager formula, not measurements."}


def metrics(node: Node) -> dict:
    with node.lock:
        m = dict(node.metrics)
    steps = m["steps"]
    p = psutil.Process()
    return {**m, "mean_latency_s": (m["latency_s_total"] / steps) if steps else None,
            "mode_switches": m["mode_switches"],
            "process": {"rss_gb": p.memory_info().rss / 2**30, "cpu_seconds": sum(p.cpu_times()[:2])},
            "note": "process.cpu_seconds is an energy PROXY only; no watts are measured."}


def make_server(node: Node, host: str = "127.0.0.1", port: int = 8700, models_dir: str = "models") -> ThreadingHTTPServer:
    routes = {"/status": lambda: status(node), "/models": lambda: models(node, models_dir),
              "/metrics": lambda: metrics(node)}

    class H(BaseHTTPRequestHandler):
        def _send(self, code, obj):
            body = json.dumps(obj, indent=2).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            fn = routes.get(self.path.split("?")[0].rstrip("/") or "/")
            self._send(200, fn()) if fn else self._send(404, {"error": "not found", "routes": sorted(routes)})

        def _no(self): self._send(405, {"error": "read-only API: GET only"})
        do_POST = do_PUT = do_DELETE = do_PATCH = _no

        def log_message(self, *a): pass

    return ThreadingHTTPServer((host, port), H)


def main(argv=None):
    from .devices import make_sensors
    from .model_manager import load_config
    from .backend import LlamaServerBackend, MockBackend
    from .environment import capture
    from .power import PowerManager
    ap = argparse.ArgumentParser(description="Run a node with its management API.")
    ap.add_argument("--host", default="127.0.0.1"); ap.add_argument("--port", type=int, default=8700)
    ap.add_argument("--battery", type=float, default=100.0, help="simulated battery %%")
    ap.add_argument("--solar", action="store_true")
    ap.add_argument("--llama-url", default="http://127.0.0.1:8080")
    ap.add_argument("--mock", action="store_true", help="DUMMY backend, for trying the API without a model")
    ap.add_argument("--interval", type=float, default=0, help="seconds between agent steps (0 = API only)")
    a = ap.parse_args(argv)
    cfg = load_config()
    env = capture()
    if a.mock:
        from bench.mock_responder import responder
        factory = lambda plan: (MockBackend(responder), lambda: None)
        print("WARNING: --mock is a DUMMY backend; nothing it reports is a measurement.")
    else:
        factory = lambda plan: (LlamaServerBackend(a.llama_url), lambda: None)
    node = Node(factory, PowerManager(cfg["budget_gb"], env["physical_cores"] or env["logical_threads"], cfg["quant"]),
                sensors=make_sensors(cfg), battery_pct=a.battery, solar=a.solar)
    if a.interval > 0:
        def loop():
            while True:
                try: node.step()
                except Exception as e: print("step failed:", e)
                time.sleep(a.interval)
        threading.Thread(target=loop, daemon=True).start()
    srv = make_server(node, a.host, a.port)
    print(f"management API on http://{a.host}:{srv.server_address[1]}  (GET /status /models /metrics)")
    srv.serve_forever()


if __name__ == "__main__":
    main()
