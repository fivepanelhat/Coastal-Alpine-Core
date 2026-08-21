"""Unit tests for SessionEvent / SessionEventStore (Sprint A Phase 1)."""

from __future__ import annotations

from pathlib import Path

from coastal_alpine_core.session_events import (
    EVENT_TYPES,
    SessionEventStore,
    make_event,
)


def test_make_and_append_list_resume(tmp_path: Path) -> None:
    store = SessionEventStore(storage_path=tmp_path / "events.jsonl")
    sid = "sess-1"
    e1 = store.emit(
        session_id=sid,
        event_type="session_start",
        actor="orchestrator",
        tenant_id="tenant-a",
        payload={"goal": "demo"},
    )
    e2 = store.emit(
        session_id=sid,
        event_type="prompt_received",
        actor="orchestrator",
        tenant_id="tenant-a",
        payload={"chars": 12},
    )
    e3 = store.emit(
        session_id=sid,
        event_type="agent_step",
        actor="intake",
        tenant_id="tenant-a",
        payload={"step": 1},
    )

    assert e1.event_id
    assert e2.prev_event_id == e1.event_id
    assert e3.prev_event_id == e2.event_id

    listed = store.list_session(sid, tenant_id="tenant-a")
    assert len(listed) == 3
    assert listed[0].event_type == "session_start"

    resumed = store.resume_from(sid, e1.event_id, tenant_id="tenant-a")
    assert len(resumed) == 2
    assert resumed[0].event_id == e2.event_id

    got = store.get(e2.event_id)
    assert got is not None
    assert got.event_type == "prompt_received"


def test_tenant_filter(tmp_path: Path) -> None:
    store = SessionEventStore(storage_path=tmp_path / "events.jsonl")
    store.emit(
        session_id="s",
        event_type="agent_step",
        actor="x",
        tenant_id="t1",
    )
    store.emit(
        session_id="s",
        event_type="agent_step",
        actor="x",
        tenant_id="t2",
    )
    assert len(store.list_session("s", tenant_id="t1")) == 1
    assert len(store.list_session("s")) == 2


def test_event_types_vocabulary() -> None:
    assert "session_start" in EVENT_TYPES
    assert "approval_granted" in EVENT_TYPES
    assert "blocked" in EVENT_TYPES


def test_make_event_unknown_type_still_builds() -> None:
    ev = make_event(
        session_id="s",
        event_type="custom_future_type",
        actor="test",
    )
    assert ev.event_type == "custom_future_type"


def test_rotate_missing_file_safe(tmp_path: Path) -> None:
    store = SessionEventStore(storage_path=tmp_path / "missing.jsonl")
    assert store.rotate_if_needed() is False
