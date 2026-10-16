"""Offline-first outbox. Events and actions are always written to a local SQLite queue; nothing is sent
anywhere unless a cloud endpoint is explicitly configured AND reachable. Delivery is at-least-once: every
record has a unique id so a receiver can de-duplicate. The cloud endpoint here is a pluggable stub (OFF by default);
it has only been tested against localhost."""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import urllib.parse
import urllib.request
import uuid
from typing import Optional, Protocol


class ConfigError(ValueError):
    pass


class OutboxQueue:
    def __init__(self, path: str = "ecaps_outbox.sqlite"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        self.db.execute("""CREATE TABLE IF NOT EXISTS outbox(
            seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE, ts REAL, kind TEXT, payload TEXT,
            attempts INTEGER DEFAULT 0, last_error TEXT, sent_at REAL)""")
        self.db.commit()

    def enqueue(self, kind: str, payload: dict) -> str:
        rid = uuid.uuid4().hex
        with self._lock:
            self.db.execute("INSERT INTO outbox(id,ts,kind,payload) VALUES(?,?,?,?)",
                            (rid, time.time(), kind, json.dumps(payload)))
            self.db.commit()
        return rid

    def pending(self, limit: int = 50) -> list[dict]:
        with self._lock:
            rows = self.db.execute("SELECT id,ts,kind,payload,attempts FROM outbox WHERE sent_at IS NULL "
                                   "ORDER BY seq LIMIT ?", (limit,)).fetchall()
        return [{"id": i, "ts": t, "kind": k, "payload": json.loads(p), "attempts": a} for i, t, k, p, a in rows]

    def mark_sent(self, ids: list[str]):
        with self._lock:
            self.db.executemany("UPDATE outbox SET sent_at=? WHERE id=?", [(time.time(), i) for i in ids])
            self.db.commit()

    def mark_failed(self, ids: list[str], error: str):
        with self._lock:
            self.db.executemany("UPDATE outbox SET attempts=attempts+1, last_error=? WHERE id=?",
                                [(error[:200], i) for i in ids])
            self.db.commit()

    def counts(self) -> dict:
        with self._lock:
            p = self.db.execute("SELECT COUNT(*) FROM outbox WHERE sent_at IS NULL").fetchone()[0]
            s = self.db.execute("SELECT COUNT(*) FROM outbox WHERE sent_at IS NOT NULL").fetchone()[0]
        return {"pending": p, "sent": s}

    def close(self): self.db.close()


class CloudSink(Protocol):
    def send(self, records: list[dict]) -> None:
        """Deliver a batch or raise. Raising means 'not delivered' and the batch stays queued."""


class HttpCloudSink:
    """POSTs a JSON batch to a configured URL. Constructed only when the user enables it in config."""

    def __init__(self, url: str, timeout: float = 5.0, token: Optional[str] = None):
        if urllib.parse.urlparse(url).scheme not in ("http", "https"):
            raise ConfigError("cloud url must start with http:// or https://")
        self.url, self.timeout, self.token = url, timeout, token

    def send(self, records):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(self.url, json.dumps({"records": records}).encode(), headers)
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            if not 200 <= r.status < 300:
                raise OSError(f"cloud endpoint answered HTTP {r.status}")


def make_sink(cfg: dict | None, token: Optional[str] = None) -> Optional[CloudSink]:
    """cfg['cloud'] = {'enabled': false (default), 'url': 'https://...'}. Returns None unless explicitly enabled."""
    c = (cfg or {}).get("cloud") or {}
    if not c.get("enabled", False):
        return None
    if not c.get("url"):
        raise ConfigError("cloud.enabled is true but cloud.url is missing")
    return HttpCloudSink(c["url"], c.get("timeout", 5.0), token)


class Syncer:
    """Pushes queued records to the sink in order, oldest first, in batches. With no sink it does nothing at all."""

    def __init__(self, queue: OutboxQueue, sink: Optional[CloudSink] = None, batch_size: int = 20):
        self.queue, self.sink, self.batch_size = queue, sink, batch_size

    def sync_once(self) -> dict:
        if self.sink is None:
            return {"skipped": "no cloud endpoint configured", "sent": 0, **self.queue.counts()}
        sent = 0
        while True:
            batch = self.queue.pending(self.batch_size)
            if not batch:
                break
            ids = [r["id"] for r in batch]
            try:
                self.sink.send(batch)
            except Exception as e:                 # unreachable / rejected: keep everything queued
                self.queue.mark_failed(ids, f"{type(e).__name__}: {e}")
                return {"error": f"{type(e).__name__}: {e}", "sent": sent, **self.queue.counts()}
            self.queue.mark_sent(ids)
            sent += len(ids)
        return {"sent": sent, **self.queue.counts()}
