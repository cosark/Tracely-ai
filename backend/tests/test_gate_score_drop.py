"""Score drops between scenario gates: a run that passes can still be worse than the last one.

Pure-function cases for `domain.gate.score_drop`, plus the service path through
`GateService.grade_scenarios` on the same in-memory harness as `test_scenario_hardening`.
"""

from __future__ import annotations

from tracely.config import settings
from tracely.domain.gate.score_drop import score_drops
from tracely.infrastructure.db import models

from tests.test_scenario_hardening import PROJECT, _Reader, _svc, db  # noqa: F401  (fixture)


def test_drop_past_threshold_is_reported():
    (d,) = score_drops({"s1": {"goal": [0.5]}}, {"s1": {"goal": [0.9]}}, 0.1)
    assert d.name == "goal" and round(d.delta, 2) == -0.4 and d.scenarios == 1
    assert "goal -0.40 vs last green gate (0.90→0.50, 1 scenario)" == d.message()


def test_small_drop_and_improvement_are_not():
    assert score_drops({"s1": {"g": [0.85]}}, {"s1": {"g": [0.9]}}, 0.1) == []
    assert score_drops({"s1": {"g": [1.0]}}, {"s1": {"g": [0.2]}}, 0.1) == []


def test_only_shared_scenarios_are_compared():
    # s2 only ran this time with a low score: a different subset is not a regression.
    cur = {"s1": {"g": [0.9]}, "s2": {"g": [0.1]}}
    assert score_drops(cur, {"s1": {"g": [0.9]}}, 0.1) == []


def test_non_unit_scale_and_excluded_names_are_skipped():
    cur = {"s1": {"latency": [900.0], "adv": [0.0]}}
    base = {"s1": {"latency": [100.0], "adv": [1.0]}}
    assert score_drops(cur, base, 0.1, exclude=["adv"]) == []


def _gate(db, gid, status, trace_ids, created):  # noqa: F811
    db.add(models.GateRun(
        id=gid, project_id=PROJECT, agent_id="a1", env="ci", status=status,
        passed=0, failed=0, skipped=0, total=1, created_at=created,
    ))
    db.add(models.GateCase(
        id=f"gc-{gid}", gate_run_id=gid, scenario_id="sc1", candidate_trace_id=f"c-{gid}",
        verdict="PASS" if status == "PASS" else "PENDING", detail={"trace_ids": trace_ids},
    ))
    db.commit()


def _run(db, monkeypatch, max_score_drop):  # noqa: F811
    from datetime import datetime, timedelta, timezone

    monkeypatch.setattr(settings, "gate_scenario_span_grace_s", 0)
    db.add(models.Scenario(id="sc1", project_id=PROJECT, agent_id="a1", title="s", kind="SCRIPTED", turns=[]))
    now = datetime.now(timezone.utc)
    _gate(db, "old", "PASS", ["t-old"], now - timedelta(days=1))
    _gate(db, "new", "RUNNING", ["t-new"], now)
    reader = _Reader(scores={
        "t-old": [{"name": "goal", "verdict": "PASS", "value": 0.9}],
        "t-new": [{"name": "goal", "verdict": "PASS", "value": 0.6}],
    })
    return _svc(db, reader=reader).grade_scenarios("new", max_score_drop=max_score_drop)


def test_passing_gate_with_a_score_drop_warns(db, monkeypatch):  # noqa: F811
    gate = _run(db, monkeypatch, None)
    assert gate.status == "PASS"
    assert any(w.startswith("score drop: goal -0.30") for w in gate.warnings)


def test_max_score_drop_makes_it_block(db, monkeypatch):  # noqa: F811
    gate = _run(db, monkeypatch, 0.2)
    assert gate.status == "FAIL"


def test_drop_below_max_score_drop_still_passes(db, monkeypatch):  # noqa: F811
    gate = _run(db, monkeypatch, 0.5)
    assert gate.status == "PASS" and gate.warnings
