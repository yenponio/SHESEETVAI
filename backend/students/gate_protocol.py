"""Bounded USB framing and a local durable event inbox; no hardware opened on import."""
import sqlite3
from contextlib import closing
from pathlib import Path

EVENTS = {
    "OPENING", "OPEN_ESTIMATED", "AT_A", "BOTH_DETECTED", "AT_B",
    "ENTERED", "WALKED_AWAY", "PASSAGE_UNCERTAIN", "CANCELLED",
    "CLOSING", "CLOSE_PAUSED", "CLOSED_ESTIMATED",
}
OPEN_REJECTIONS = {"ERROR SENSOR_UNKNOWN", "ERROR START_OUTSIDE_AT_A"}


class LineFramer:
    def __init__(self, limit=128):
        self.buffer = bytearray()
        self.limit = limit

    def feed(self, chunk):
        lines = []
        for byte in chunk:
            if byte == 10:
                lines.append(bytes(self.buffer).rstrip(b"\r").decode("ascii"))
                self.buffer.clear()
            else:
                self.buffer.append(byte)
                if len(self.buffer) > self.limit:
                    self.buffer.clear()
                    raise ValueError("Oversized serial line")
        return lines


def parse_event(line, active_attempt=None):
    if line in OPEN_REJECTIONS:
        if not active_attempt:
            raise ValueError("Opening rejection without an active command")
        return int(active_attempt), "OPEN_REJECTED"
    parts = line.split()
    if not parts or parts[0] not in EVENTS:
        return None
    if len(parts) != 2 or not parts[1].isascii() or not parts[1].isdigit():
        raise ValueError("Malformed gate event")
    attempt = int(parts[1])
    if not 1 <= attempt <= 2147483647:
        raise ValueError("Gate event ID out of range")
    return attempt, parts[0]


class EventJournal:
    def __init__(self, path):
        self.path = str(Path(path))
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                bridge TEXT NOT NULL, attempt INTEGER NOT NULL,
                event TEXT NOT NULL, applied INTEGER NOT NULL DEFAULT 0
            )""")

    def append(self, bridge, attempt, event):
        with closing(sqlite3.connect(self.path, timeout=2)) as db, db:
            cursor = db.execute(
                "INSERT INTO events(bridge, attempt, event) VALUES (?, ?, ?)",
                (bridge, attempt, event),
            )
            return cursor.lastrowid

    def pending(self):
        with closing(sqlite3.connect(self.path, timeout=2)) as db, db:
            return db.execute(
                "SELECT seq, bridge, attempt, event FROM events WHERE applied=0 ORDER BY seq LIMIT 100"
            ).fetchall()

    def acknowledge(self, seq):
        with closing(sqlite3.connect(self.path, timeout=2)) as db, db:
            db.execute("UPDATE events SET applied=1 WHERE seq=?", (seq,))
