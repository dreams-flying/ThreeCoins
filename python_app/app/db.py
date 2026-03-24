from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "readings.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS readings (
                id TEXT PRIMARY KEY,
                timestamp INTEGER NOT NULL,
                question TEXT,
                payload TEXT NOT NULL
            )
            """
        )


def save_reading(raw: dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO readings (id, timestamp, question, payload) VALUES (?, ?, ?, ?)",
            (raw["id"], raw["timestamp"], raw.get("question", ""), json.dumps(raw, ensure_ascii=False)),
        )


def get_reading(reading_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT payload FROM readings WHERE id = ?", (reading_id,)).fetchone()
    if not row:
        return None
    return json.loads(row["payload"])


def get_history(limit: int = 200) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT payload FROM readings ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [json.loads(r["payload"]) for r in rows]


def delete_reading(reading_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM readings WHERE id = ?", (reading_id,))


def clear_history() -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM readings")
