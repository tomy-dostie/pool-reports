"""Pool scoring engine: 1 point per goal and per assist, only active players score.

A stint is one period of active ownership. A waiver move closes one stint (dropped_on) and opens
another (added_on) on the same date. A stint counts games with added_on <= date < dropped_on,
so a dropped player's last day does NOT count (confirmed against PoolExpert).
"""
import json
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Line:
    date: date
    player_id: int
    name: str
    team: str
    goals: int
    assists: int
    position: str = ""


@dataclass
class Stint:
    name: str
    team: str = ""
    player_id: Optional[int] = None
    added_on: date = date.min
    dropped_on: Optional[date] = None
    position: str = ""

    def counts_on(self, d):
        return d >= self.added_on and (self.dropped_on is None or d < self.dropped_on)


@dataclass
class Pooler:
    id: str
    name: str
    players: list = field(default_factory=list)


@dataclass
class Roster:
    poolers: list
    goal_points: int = 1
    assist_points: int = 1
    start_date: date = date.min
    season_games: int = 84


def norm(s):
    """Strip accents, spaces and punctuation: 'Tomas Hertl' == 'Tomás Hertl', 'J.T. Miller' == 'jtmiller'."""
    d = unicodedata.normalize("NFD", s)
    return "".join(c.lower() for c in d if c.isalnum() and unicodedata.category(c) != "Mn")


# PoolExpert team code -> NHL team code
TEAM_ALIASES = {"TB": "TBL", "NJ": "NJD", "SJ": "SJS", "LA": "LAK", "WIN": "WPG"}


def norm_team(t):
    t = t.strip().upper()
    return TEAM_ALIASES.get(t, t)


def load_roster(path):
    raw = json.load(open(path, encoding="utf-8"))
    iso = lambda s: date.fromisoformat(s) if s else None
    poolers = [Pooler(p["id"], p["name"], [
        Stint(s["name"], s.get("team", ""), s.get("playerId"), iso(s["addedOn"]), iso(s.get("droppedOn")), s.get("position", ""))
        for s in p["players"]]) for p in raw["poolers"]]
    return Roster(poolers, raw.get("goalPoints", 1), raw.get("assistPoints", 1),
                  iso(raw.get("startDate")) or date.min, raw.get("seasonGames", 84))


def validate(r):
    """Roster mistakes worth fixing: bad dates, the same player owned twice at the same time."""
    w = []
    items = [(p.id, s) for p in r.poolers for s in p.players]
    for pid, s in items:
        if s.dropped_on is not None and s.dropped_on <= s.added_on:
            w.append(f"{s.name}: droppedOn must be after addedOn")
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            (pa, a), (pb, b) = items[i], items[j]
            same = (a.player_id is not None and a.player_id == b.player_id) or \
                   (a.player_id is None and b.player_id is None and norm(a.name) == norm(b.name))
            if not same:
                continue
            a_end = a.dropped_on or date.max
            b_end = b.dropped_on or date.max
            if a.added_on < b_end and b.added_on < a_end:
                w.append(f"{a.name} is owned twice at the same time ({pa}, {pb})")
    return w


def _narrow(items, pred):
    kept = [x for x in items if pred(x)]
    return kept if kept else items


def find_line(s, lines, warnings):
    if s.player_id is not None:
        return next((l for l in lines if l.player_id == s.player_id), None)
    c = [l for l in lines if norm(l.name) == norm(s.name)]
    if not c:   # box scores abbreviate names ("K. Johnson"): try first initial + last name
        first, _, last = s.name.partition(" ")
        if last:
            c = [l for l in lines if norm(l.name) == norm(first[0] + last)]
    if len(c) > 1 and s.team:
        c = _narrow(c, lambda l: norm_team(l.team) == norm_team(s.team))
    if len(c) > 1 and s.position:
        c = _narrow(c, lambda l: l.position == s.position)
    if len(c) > 1:
        warnings.append(f"Ambiguous name '{s.name}': add a playerId")
        return None
    return c[0] if c else None


def score_day(r, d, lines, warnings=None):
    """{pooler_id: (points, [(name, team, goals, assists, points, player_id), ...])} for one game date."""
    warnings = warnings if warnings is not None else []
    out = {}
    for p in r.poolers:
        total, scorers = 0, []
        for s in p.players:
            if not s.counts_on(d):
                continue
            l = find_line(s, lines, warnings)
            if l is None:
                continue
            pts = l.goals * r.goal_points + l.assists * r.assist_points
            total += pts
            if pts > 0:
                scorers.append((l.name, l.team, l.goals, l.assists, pts, l.player_id))
        scorers.sort(key=lambda x: (-x[4], x[0]))
        out[p.id] = (total, scorers)
    return out


def _ranks(r, totals):
    return {p.id: 1 + sum(1 for q in r.poolers if totals[q.id] > totals[p.id]) for p in r.poolers}


def standings(r, days, as_of):
    """Rows (rank, id, name, total, last_day_points, rank_change). Ties share a rank. Positive change = moved up."""
    tot = {p.id: 0 for p in r.poolers}
    prev = dict(tot)
    yday = dict(tot)
    for d, res in days.items():
        if d > as_of:
            continue
        for pid, (pts, _) in res.items():
            tot[pid] += pts
            if d < as_of:
                prev[pid] += pts
            else:
                yday[pid] += pts
    rk, pr = _ranks(r, tot), _ranks(r, prev)
    rows = [(rk[p.id], p.id, p.name, tot[p.id], yday[p.id], pr[p.id] - rk[p.id]) for p in r.poolers]
    return sorted(rows, key=lambda x: (x[0], x[2]))
