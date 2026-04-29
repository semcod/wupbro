"""In-memory + JSONL persistence for WUP events.

The storage layer is intentionally simple: events are kept in memory
(deque, capped) AND appended to a JSONL file for persistence between
restarts. Suitable for a single-node dashboard.
"""

from __future__ import annotations

import json
import threading
from collections import deque
from pathlib import Path
from typing import Deque, Iterable, List, Optional

from .models import Event


class EventStore:
    """Thread-safe ring buffer + JSONL persistence."""

    def __init__(self, jsonl_path: Optional[Path] = None, capacity: int = 1000):
        self.capacity = capacity
        self.events: Deque[Event] = deque(maxlen=capacity)
        self.jsonl_path = jsonl_path
        self._lock = threading.Lock()
        self._seq = 0  # monotonic insertion counter (tiebreaker for sort)
        self._seq_by_id: dict = {}
        if self.jsonl_path:
            self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
            self._load_existing()

    def _load_existing(self) -> None:
        if not self.jsonl_path or not self.jsonl_path.exists():
            return
        try:
            with self.jsonl_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        self.events.append(Event.model_validate_json(line))
                    except Exception:
                        continue
        except OSError:
            pass

    def add(self, event: Event) -> None:
        with self._lock:
            self._seq += 1
            self._seq_by_id[id(event)] = self._seq
            self.events.append(event)
            if self.jsonl_path:
                try:
                    with self.jsonl_path.open("a", encoding="utf-8") as fh:
                        fh.write(event.model_dump_json() + "\n")
                except OSError:
                    pass

    def list(
        self,
        type_filter: Optional[str] = None,
        service_filter: Optional[str] = None,
        limit: int = 100,
    ) -> List[Event]:
        with self._lock:
            items: List[Event] = list(self.events)
            seq_map = dict(self._seq_by_id)
        if type_filter:
            items = [e for e in items if e.type == type_filter]
        if service_filter:
            items = [e for e in items if e.service == service_filter]
        # newest first: primary key timestamp, tiebreaker insertion sequence
        items.sort(key=lambda e: (e.timestamp, seq_map.get(id(e), 0)), reverse=True)
        return items[:limit]

    def clear(self) -> None:
        with self._lock:
            self.events.clear()
            self._seq_by_id.clear()
            self._seq = 0
            if self.jsonl_path and self.jsonl_path.exists():
                try:
                    self.jsonl_path.unlink()
                except OSError:
                    pass

    def stats(self) -> dict:
        with self._lock:
            counts: dict = {}
            for e in self.events:
                counts[e.type] = counts.get(e.type, 0) + 1
            return {"total": len(self.events), "by_type": counts}


# Module-level default store (used by routers); tests can replace via dependency override.
_default_store: Optional[EventStore] = None


def get_default_store() -> EventStore:
    global _default_store
    if _default_store is None:
        _default_store = EventStore(jsonl_path=Path(".wupbro/events.jsonl"))
    return _default_store


def set_default_store(store: EventStore) -> None:
    global _default_store
    _default_store = store
