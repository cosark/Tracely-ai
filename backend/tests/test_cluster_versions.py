"""Version attribution for a failure cluster (`domain.failure.versions.introduced_in`)."""

from __future__ import annotations

from datetime import datetime, timedelta

from tracely.api.routers.clusters import _versions
from tracely.domain.failure.versions import VersionRow, introduced_in

T0 = datetime(2026, 9, 1)


def _row(v: str, runs: int, members: int, day: int) -> VersionRow:
    return VersionRow(v, runs, members, T0 + timedelta(days=day))


def test_first_failing_version_after_clean_traffic_is_blamed():
    rows = [_row("v3", 280, 41, 10), _row("v2", 340, 0, 0)]  # input order must not matter
    assert introduced_in(rows) == "v3"


def test_present_since_the_first_version_is_not_attributed():
    assert introduced_in([_row("v1", 300, 5, 0), _row("v2", 300, 9, 5)]) is None


def test_too_little_clean_traffic_is_not_attributed():
    assert introduced_in([_row("v1", 3, 0, 0), _row("v2", 300, 9, 5)]) is None


def test_unversioned_runs_are_ignored():
    assert introduced_in([_row("", 500, 0, 0), _row("v1", 10, 2, 1)]) is None


def test_router_block_uses_labels_and_orders_oldest_first():
    out = _versions(
        [
            {"version_id": "id3", "runs": 280, "members": 41, "first_seen": T0 + timedelta(days=9)},
            {"version_id": "id2", "runs": 340, "members": 0, "first_seen": T0},
            {"version_id": "", "runs": 4, "members": 0, "first_seen": T0},
        ],
        {"id2": "v2", "id3": "v3"},
    )
    assert out["introduced_in"] == "v3"
    assert [r["version"] for r in out["rows"]] == ["v2", None, "v3"]
