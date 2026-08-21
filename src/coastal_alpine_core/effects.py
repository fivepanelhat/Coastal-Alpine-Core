"""
Reversible effects journal (Sprint E).

Tools/skills may declare a reverse operation. The journal records applied
effects so callers can undo in LIFO order under HITL policy.

CAT constraints:
- No secrets in effect payloads.
- Journal is local in-memory (optional JSONL append for audit).
- Undo is best-effort; failures are recorded, not swallowed silently.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger("coastal_alpine_core.effects")

ReverseFn = Callable[[dict[str, Any]], None]


@dataclass
class EffectRecord:
    effect_id: str
    action: str
    payload: dict[str, Any] = field(default_factory=dict)
    reverse_action: str | None = None
    reverse_payload: dict[str, Any] = field(default_factory=dict)
    reversible: bool = False
    applied_at: float = field(default_factory=time.time)
    undone: bool = False
    undo_error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class EffectJournal:
    """Stack of applied effects with optional reverse handlers."""

    def __init__(self, audit_path: str | Path | None = None):
        self._stack: list[EffectRecord] = []
        self._handlers: dict[str, ReverseFn] = {}
        self.audit_path = Path(audit_path) if audit_path else None

    def register_reverse(self, action: str, fn: ReverseFn) -> None:
        if not action:
            raise ValueError("action must be non-empty")
        self._handlers[action] = fn

    def record(
        self,
        action: str,
        *,
        payload: dict[str, Any] | None = None,
        reverse_action: str | None = None,
        reverse_payload: dict[str, Any] | None = None,
        reversible: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EffectRecord:
        rev = reverse_action or action
        is_rev = reversible if reversible is not None else (rev in self._handlers)
        rec = EffectRecord(
            effect_id=str(uuid.uuid4()),
            action=action,
            payload=dict(payload or {}),
            reverse_action=rev if is_rev else None,
            reverse_payload=dict(reverse_payload or payload or {}),
            reversible=is_rev,
            metadata=dict(metadata or {}),
        )
        self._stack.append(rec)
        self._audit(rec, event="applied")
        return rec

    def undo_last(self) -> Optional[EffectRecord]:
        for rec in reversed(self._stack):
            if rec.undone:
                continue
            if not rec.reversible or not rec.reverse_action:
                rec.undone = True
                rec.undo_error = "not_reversible"
                self._audit(rec, event="undo_skipped")
                return rec
            handler = self._handlers.get(rec.reverse_action)
            if handler is None:
                rec.undone = True
                rec.undo_error = f"no_handler:{rec.reverse_action}"
                self._audit(rec, event="undo_failed")
                return rec
            try:
                handler(rec.reverse_payload)
                rec.undone = True
                self._audit(rec, event="undone")
            except Exception as exc:
                rec.undo_error = str(exc)[:200]
                self._audit(rec, event="undo_failed")
                logger.warning("Undo failed for %s: %s", rec.effect_id, exc)
            return rec
        return None

    def undo_all(self) -> list[EffectRecord]:
        done: list[EffectRecord] = []
        while True:
            rec = self.undo_last()
            if rec is None:
                break
            done.append(rec)
        return done

    def pending(self) -> list[EffectRecord]:
        return [r for r in self._stack if not r.undone]

    def history(self) -> list[EffectRecord]:
        return list(self._stack)

    def clear(self) -> None:
        self._stack.clear()

    def _audit(self, rec: EffectRecord, *, event: str) -> None:
        if not self.audit_path:
            return
        try:
            self.audit_path.parent.mkdir(parents=True, exist_ok=True)
            line = json.dumps({"event": event, **asdict(rec)}, default=str)
            with self.audit_path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError as exc:
            logger.debug("Effect audit write failed: %s", exc)
