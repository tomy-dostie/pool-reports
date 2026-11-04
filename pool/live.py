"""Evening "En direct": points scored tonight in games that have started, on top of the morning standings.

Provisional by design: the official numbers are the next morning's report. Uses the same scoring (score_day) as
the standings, so a finished night here gives exactly what the morning report will add.
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone

from .engine import norm_team, score_day
from .report import TORONTO, _clock, _ga, MONTHS_FR

# A game night runs past midnight: until 6 h, "tonight" is still the previous date.
NIGHT_ENDS_HOUR = 6


def live_day(now):
    """The NHL date of the current game night (Toronto time)."""
    return (now.astimezone(TORONTO) - timedelta(hours=NIGHT_ENDS_HOUR)).date()


def tonight_games(client, day, game_types=(2,)):
    return [g for g in client.score(day) if g.date == day and g.game_type in game_types]


def signature(games):
    """Changes when a game starts, ends, changes period or someone scores (a point always comes with a goal)."""
    key = [(g.id, g.state, g.away_score, g.home_score, g.period, g.intermission) for g in games if g.started]
    return hashlib.sha256(json.dumps(sorted(key)).encode()).hexdigest()[:16] if key else None


def _status(g):
    if g.is_final:
        return "Final" + (" (prol.)" if g.period_type == "OT" else " (t.b.)" if g.period_type == "SO" else "")
    if g.started:
        if g.intermission:
            return f"Entracte {g.period}" if g.period <= 3 else "Entracte"
        per = {1: "1re", 2: "2e", 3: "3e"}.get(g.period, "Prol." if g.period_type == "OT" else "T.b." if g.period_type == "SO" else f"{g.period}e")
        return f"{per} · {g.clock}" if g.clock else per
    return _clock(g.start_utc) if g.start_utc else "À venir"


def build_live(roster, client, day, poolers, directory, now=None):
    """Live payload for the page, or None when no game of the night has started yet.

    poolers = the morning report's pooler entries (rank, total, color...) to build the provisional standings;
    directory = {player_id: DirPlayer} from the NHL rosters (full names, current teams)."""
    games = tonight_games(client, day)
    started = [g for g in games if g.started]
    if not started:
        return None
    lines, failed = [], 0
    for g in started:
        try:
            lines += client.boxscore(g, cache=False)
        except RuntimeError:          # NHL hiccup: that game's points show up on the next run
            failed += 1
    res = score_day(roster, day, lines)
    in_play = {t for g in started if not g.is_final for t in (g.away, g.home)}
    to_come = {t for g in games if not g.started for t in (g.away, g.home)}
    played = {t for g in started for t in (g.away, g.home)}

    by_id = {p.id: p for p in roster.poolers}
    rows = []
    for p in poolers:
        pts, scorers = res.get(p["id"], (0, []))
        # current NHL team of each active player (NHL rosters first, roster.json as fallback)
        teams = [directory[s.player_id].team if s.player_id in directory else norm_team(s.team)
                 for s in by_id[p["id"]].players if s.counts_on(day)]
        rows.append({
            "id": p["id"], "name": p["name"], "color": p["color"], "morningRank": p["rank"], "morning": p["total"],
            "tonight": pts, "total": p["total"] + pts,
            "playing": sum(1 for t in teams if t in in_play),
            "toCome": sum(1 for t in teams if t in to_come),
            "done": sum(1 for t in teams if t in played and t not in in_play),
            "scorers": [{"player": directory[pid].name if pid in directory else nm, "line": _ga(gl, a), "pts": sp, "team": tm}
                        for nm, tm, gl, a, sp, pid in scorers],
        })
    for r in rows:
        r["rank"] = 1 + sum(1 for x in rows if x["total"] > r["total"])
        r["move"] = r["morningRank"] - r["rank"]
    rows.sort(key=lambda r: (r["rank"], -r["tonight"], r["name"]))

    now = now or datetime.now(timezone.utc)
    t = now.astimezone(TORONTO)
    order = {"LIVE": 0, "CRIT": 0, "FUT": 2, "PRE": 2, "OFF": 1, "FINAL": 1}
    return {
        "day": day.isoformat(), "dayLabel": f"{day.day} {MONTHS_FR[day.month - 1]}",
        "updated": f"{t.hour} h {t.minute:02d}", "updatedAt": now.astimezone(timezone.utc).isoformat(timespec="seconds"),
        # a missed box score makes the signature differ from the scoreboard's, so the next run rebuilds
        "sig": signature(games) + ("-incomplet" if failed else ""), "failed": failed,
        "inProgress": sum(1 for g in started if not g.is_final), "finals": sum(1 for g in started if g.is_final),
        "upcoming": sum(1 for g in games if not g.started), "allDone": all(g.is_final for g in games),
        "games": [{"away": g.away, "home": g.home, "as": g.away_score, "hs": g.home_score, "status": _status(g),
                   "live": g.started and not g.is_final, "final": g.is_final}
                  for g in sorted(games, key=lambda g: (order.get(g.state, 3), g.start_utc, g.home))],
        "poolers": rows,
    }
