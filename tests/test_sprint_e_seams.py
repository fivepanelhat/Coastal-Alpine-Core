"""Sprint E seam tests — config overlays, effects, skill graph, code mode."""

from __future__ import annotations

import pytest

from coastal_alpine_core.code_mode import CodeModeRunner
from coastal_alpine_core.config_overlay import ConfigOverlay
from coastal_alpine_core.effects import EffectJournal
from coastal_alpine_core.skill_graph import SkillGraphError, resolve_skill_order


def test_config_overlay_merge_order():
    cfg = ConfigOverlay(defaults={"llm": {"model": "base", "temp": 0.1}, "x": 1})
    cfg.register_profile("edge", {"llm": {"model": "edge-model"}})
    cfg.set_tenant({"x": 2})
    cfg.set_session({"llm": {"temp": 0.5}})
    cfg.use_profile("edge")
    resolved = cfg.resolve()
    assert resolved["llm"]["model"] == "edge-model"
    assert resolved["llm"]["temp"] == 0.5
    assert resolved["x"] == 2


def test_config_rejects_secret_keys():
    cfg = ConfigOverlay()
    with pytest.raises(ValueError):
        cfg.register_profile("bad", {"api_token": "x"})


def test_effect_journal_undo():
    state = {"n": 0}

    def reverse(payload):
        state["n"] -= payload.get("delta", 1)

    journal = EffectJournal()
    journal.register_reverse("bump", reverse)
    state["n"] += 1
    journal.record("bump", payload={"delta": 1}, reverse_payload={"delta": 1})
    assert state["n"] == 1
    rec = journal.undo_last()
    assert rec is not None and rec.undone
    assert state["n"] == 0


def test_skill_graph_order_and_cycle():
    skills = {
        "a": {"depends_on": []},
        "b": {"depends_on": ["a"]},
        "c": {"depends_on": ["b"]},
    }
    assert resolve_skill_order(skills) == ["a", "b", "c"]

    cyclic = {"a": {"depends_on": ["b"]}, "b": {"depends_on": ["a"]}}
    with pytest.raises(SkillGraphError):
        resolve_skill_order(cyclic)


def test_code_mode_tool_call_and_block_import():
    calls = []

    def echo(msg=""):
        calls.append(msg)
        return msg

    runner = CodeModeRunner({"echo": echo})
    ok = runner.run('result = tools.echo(msg="hi")')
    assert ok.success is True
    assert ok.output == "hi"
    assert calls == ["hi"]

    bad = runner.run("import os\nresult = os.getcwd()")
    assert bad.success is False
