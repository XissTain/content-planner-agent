"""SQLite checkpoint 与唯一请求约束；同一请求 ID 不允许悄悄换输入。"""
import hashlib
import json
import sqlite3
from pathlib import Path


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def digest(value):
    return hashlib.sha256(dumps(value).encode("utf-8")).hexdigest()[:20]


class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, state TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS plans (id TEXT PRIMARY KEY, request_id TEXT UNIQUE NOT NULL, body TEXT NOT NULL)")
        self.db.commit()

    def close(self):
        self.db.close()

    def load(self, request_id, fingerprint):
        row = self.db.execute("SELECT fingerprint, state FROM runs WHERE id=?", (request_id,)).fetchone()
        if not row:
            return None
        if row[0] != fingerprint:
            raise ValueError("相同 request_id 对应不同输入，请使用新的 request_id。")
        return json.loads(row[1])

    def checkpoint(self, state, fingerprint):
        with self.db:
            self.db.execute(
                "INSERT INTO runs VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET state=excluded.state",
                (state["request"]["request_id"], fingerprint, dumps(state)),
            )

    def plan(self, request_id):
        row = self.db.execute("SELECT body FROM plans WHERE request_id=?", (request_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def save_plan(self, request_id, body):
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO plans VALUES (?, ?, ?)", (body["plan_id"], request_id, dumps(body)))
        return self.plan(request_id)
