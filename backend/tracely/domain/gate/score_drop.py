"""Evaluator score drops between two gate runs — pure, no I/O.

A scenario gate that passes can still be worse than the last one: every conversation clears its
bar while the goal-completion judge slides from 0.9 to 0.6. Verdicts can't see that; means can.

Compared PER SCENARIO, then averaged over the scenarios both runs drove. Pooling all scores per
run instead would turn "this PR ran a different subset" into a fake regression (or hide a real
one). Only evaluators whose every value sits in [0, 1] are compared — a latency check scored in
milliseconds has no meaningful absolute "drop" on the same scale as a judge's 0.8.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

# Per scenario id → per score name → raw values (one per graded turn / conversation).
ScoreTable = Mapping[str, Mapping[str, Sequence[float]]]

_EPS = 1e-9


@dataclass(frozen=True)
class ScoreDrop:
    name: str
    baseline: float
    current: float
    scenarios: int

    @property
    def delta(self) -> float:
        return self.current - self.baseline

    def message(self) -> str:
        n = self.scenarios
        return (
            f"{self.name} {self.delta:+.2f} vs last green gate "
            f"({self.baseline:.2f}→{self.current:.2f}, {n} scenario{'s' if n != 1 else ''})"
        )


def _mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)


def score_drops(
    current: ScoreTable,
    baseline: ScoreTable,
    threshold: float,
    exclude: Sequence[str] = (),
) -> list[ScoreDrop]:
    """Evaluators whose mean fell by at least `threshold` (absolute) vs `baseline`, worst first."""
    skip = set(exclude)
    per_name: dict[str, list[tuple[float, float]]] = {}
    unit_scale: dict[str, bool] = {}
    for sid, cur_scores in current.items():
        base_scores = baseline.get(sid)
        if not base_scores:
            continue
        for name, cur_vals in cur_scores.items():
            base_vals = base_scores.get(name)
            if name in skip or not cur_vals or not base_vals:
                continue
            in_unit = all(0.0 <= v <= 1.0 for v in (*cur_vals, *base_vals))
            unit_scale[name] = unit_scale.get(name, True) and in_unit
            per_name.setdefault(name, []).append((_mean(base_vals), _mean(cur_vals)))

    drops = []
    for name, pairs in per_name.items():
        if not unit_scale[name]:
            continue
        base = _mean([b for b, _ in pairs])
        cur = _mean([c for _, c in pairs])
        if base - cur >= threshold - _EPS:
            drops.append(ScoreDrop(name, base, cur, len(pairs)))
    return sorted(drops, key=lambda d: d.delta)
