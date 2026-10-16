"""Short persistent local memory (SQLite) of recent events."""
from __future__ import annotations

import json
import sqlite3
import time


class Memory:
    def __init__(self, path: str = "ecaps_memory.sqlite"):
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, ts REAL, kind TEXT, data TEXT)")
        self.db.commit()

    def add(self, kind: str, data: dict):
        self.db.execute("INSERT INTO events(ts,kind,data) VALUES(?,?,?)", (time.time(), kind, json.dumps(data)))
        self.db.commit()

    def recent(self, n: int = 5) -> list[dict]:
        rows = self.db.execute("SELECT kind,data FROM events ORDER BY id DESC LIMIT ?", (n,)).fetchall()
        return [{"kind": k, **json.loads(d)} for k, d in reversed(rows)]

    def close(self): self.db.close()
