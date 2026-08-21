"""
SessionEvent store — append-only, tenant-aware event stream for Weaver / Aether.

CAT Sprint A Phase 1. Complements DataFlywheel Trajectory (outcome-level) with
finer-grained, resumeable SessionEvents for HITL evidence and Trajectory views.
Local-first JSONL; no network; no secrets in payloads.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

logger = logging.getLogger("CoastalAlpineCore.SessionEvents")

# v1 vocabulary — keep stable; extend only by addition
EVENT_TYPES = frozenset(
    {
        "session_start",
        "prompt_received",
        "security_check",
        "agent_step",
        "tool_call",
        "tool_result",
        "skill_load",
        "skill_applied",
        "llm_call",
        "approval_required",
        "approval_granted",
        "approval_denied",
        "blocked",
        "escalation",
        "session_end",
        "error",
    }
)


@dataclass
class SessionEvent:
    """Immutable-style event record. Callers should not mutate after append."""

    event_id: str
    session_id: str
    tenant_id: str | None
    timestamp: str
    event_type: str
    actor: str
    payload: dict[str, Any]
    parent_event_id: str | None = None
    prev_event_id: str | None = None
    outcome: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionEvent":
        valid = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in valid})


def new_event_id() -> str:
    return str(uuid.uuid4())


def utc_now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def make_event(
    *,
    session_id: str,
    event_type: str,
    actor: str,
    payload: dict[str, Any] | None = None,
    tenant_id: str | None = None,
    parent_event_id: str | None = None,
    prev_event_id: str | None = None,
    outcome: str | None = None,
    metadata: dict[str, Any] | None = None,
    event_id: str | None = None,
    timestamp: str | None = None,
) -> SessionEvent:
    if event_type not in EVENT_TYPES:
        logger.warning(
            "Unknown event_type %r — recording anyway for forward compatibility",
            event_type,
        )
    return SessionEvent(
        event_id=event_id or new_event_id(),
        session_id=session_id,
        tenant_id=tenant_id,
        timestamp=timestamp or utc_now_iso(),
        event_type=event_type,
        actor=actor,
        payload=payload or {},
        parent_event_id=parent_event_id,
        prev_event_id=prev_event_id,
        outcome=outcome,
        metadata=metadata or {},
    )


class SessionEventStore:
    """
    Append-only JSONL store for SessionEvents.

    Edge-safe: SD-card rotation defaults match DataFlywheel.
    Tenant filter is advisory at read time; writers must set tenant_id.
    """

    DEFAULT_MAX_BYTES = 5 * 1024 * 1024
    DEFAULT_KEEP_LINES = 4000

    def __init__(
        self,
        storage_path: str | Path = "session_events.jsonl",
        max_bytes: int | None = None,
        keep_lines: int | None = None,
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_bytes = max_bytes if max_bytes is not None else self.DEFAULT_MAX_BYTES
        self.keep_lines = (
            keep_lines if keep_lines is not None else self.DEFAULT_KEEP_LINES
        )
        self._last_event_id_by_session: dict[str, str] = {}

    def append(self, event: SessionEvent) -> SessionEvent:
        # Chain prev_event_id if caller left it empty and we have a last for this session
        if event.prev_event_id is None and event.session_id in self._last_event_id_by_session:
            event = SessionEvent(
                **{
                    **event.to_dict(),
                    "prev_event_id": self._last_event_id_by_session[event.session_id],
                }
            )
        line = json.dumps(event.to_dict(), default=str) + "\n"
        with self.storage_path.open("a", encoding="utf-8") as f:
            f.write(line)
        self._last_event_id_by_session[event.session_id] = event.event_id
        logger.debug(
            "SessionEvent %s type=%s session=%s",
            event.event_id,
            event.event_type,
            event.session_id,
        )
        self.rotate_if_needed()
        return event

    def emit(self, **kwargs: Any) -> SessionEvent:
        """Convenience: make_event + append."""
        return self.append(make_event(**kwargs))

    def rotate_if_needed(self) -> bool:
        try:
            if not self.storage_path.is_file():
                return False
            if self.storage_path.stat().st_size <= self.max_bytes:
                return False
            lines = self.storage_path.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
            if len(lines) > self.keep_lines:
                kept = lines[-self.keep_lines :]
                self.storage_path.write_text(
                    "\n".join(kept) + "\n", encoding="utf-8"
                )
            else:
                data = self.storage_path.read_bytes()
                self.storage_path.write_bytes(data[-(self.max_bytes // 2) :])
            logger.warning("SessionEventStore rotated at %s", self.storage_path)
            return True
        except OSError as e:
            logger.error("SessionEventStore rotation failed: %s", e)
            return False

    def _iter_events(self) -> Iterable[SessionEvent]:
        if not self.storage_path.exists():
            return
        with self.storage_path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield SessionEvent.from_dict(json.loads(line))
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(
                        "SessionEventStore: skipping corrupt line %s: %s", line_no, e
                    )

    def list_session(
        self,
        session_id: str,
        tenant_id: str | None = None,
        event_types: frozenset[str] | None = None,
        limit: int | None = None,
    ) -> list[SessionEvent]:
        events: list[SessionEvent] = []
        for ev in self._iter_events():
            if ev.session_id != session_id:
                continue
            if tenant_id is not None and ev.tenant_id != tenant_id:
                continue
            if event_types is not None and ev.event_type not in event_types:
                continue
            events.append(ev)
        if limit is not None and limit > 0:
            return events[-limit:]
        return events

    def get(self, event_id: str) -> SessionEvent | None:
        for ev in self._iter_events():
            if ev.event_id == event_id:
                return ev
        return None

    def resume_from(
        self,
        session_id: str,
        after_event_id: str,
        tenant_id: str | None = None,
    ) -> list[SessionEvent]:
        """Return events in session strictly after after_event_id (Trajectory-style resume)."""
        found = False
        out: list[SessionEvent] = []
        for ev in self.list_session(session_id, tenant_id=tenant_id):
            if not found:
                if ev.event_id == after_event_id:
                    found = True
                continue
            out.append(ev)
        return out

    def recent(
        self, limit: int = 100, tenant_id: str | None = None
    ) -> list[SessionEvent]:
        if limit <= 0:
            return []
        events = list(self._iter_events())
        if tenant_id is not None:
            events = [e for e in events if e.tenant_id == tenant_id]
        return events[-limit:]
