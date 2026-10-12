"""Which agent version introduced a failure mode — pure, no I/O.

Input is, per agent version, how many production runs it served and how many of those landed in
the cluster. A version is blamed only when the versions BEFORE it served real traffic and never
failed this way: "0 of 340 runs on v2, 41 of 280 on v3" says v3 introduced it. A failure that is
present from the first version we ever saw — or whose earlier versions barely ran — has no
attributable version, and saying one would send someone bisecting the wrong change.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

# Clean runs on earlier versions needed before the first failing version gets the blame.
MIN_CLEAN_RUNS = 20


@dataclass(frozen=True)
class VersionRow:
    version_id: str  # "" = runs that carried no `tracely.agent.version`
    runs: int
    members: int
    first_seen: datetime


def introduced_in(rows: Sequence[VersionRow], min_clean_runs: int = MIN_CLEAN_RUNS) -> str | None:
    """The version id that introduced this failure, or None when it can't be attributed."""
    clean = 0
    for r in sorted((r for r in rows if r.version_id), key=lambda r: r.first_seen):
        if r.members:
            return r.version_id if clean >= min_clean_runs else None
        clean += r.runs
    return None
