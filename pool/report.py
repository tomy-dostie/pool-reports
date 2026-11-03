"""Builds the report data (all the numbers and the French text) for one morning."""
import statistics
from bisect import bisect_left, bisect_right
from collections import defaultdict
from dataclasses import replace
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from .engine import find_line, score_day, standings, validate
from .nhl import TEAM_CODES, resolve_ids

TORONTO = ZoneInfo("America/Toronto")
COLORS = ["#FFB84D", "#5EB6FF", "#4FD1A5", "#FF8FC7", "#A99BFF", "#D0D6E4", "#FF8A6B", "#C6E86B", "#5ED6D6", "#FFD0A0"]
DAYS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MONTHS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
MONTHS_SHORT_FR = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def _short(d):
    return f"{d.day} {MONTHS_SHORT_FR[d.month - 1]}"


def now_toronto():
    return datetime.now(TORONTO)


def _plural(n, one, many):
    return one if abs(n) <= 1 else many


def _ga(g, a):
    parts = []
    if g:
        parts.append(f"{g} B")
    if a:
        parts.append(f"{a} A")
    return " · ".join(parts)


def _clock(start_utc):
    t = datetime.fromisoformat(start_utc.replace("Z", "+00:00")).astimezone(TORONTO)
    return f"{t.hour} h" if t.minute == 0 else f"{t.hour} h {t.minute:02d}"


def _names(names, limit=3):
    if len(names) <= limit:
        return ", ".join(names)
    rest = len(names) - limit
    return ", ".join(names[:limit]) + f" et {rest} {_plural(rest, 'autre', 'autres')}"


def collect(client, start, through, game_types=(2,), failures=None):
    """Finished regular-season games and player lines for every date from start to through."""
    lines_by_day, games_by_day = {}, {}
    d = start
    while d <= through:
        games = [g for g in client.score(d) if g.is_final and g.date == d and g.game_type in game_types]
        lines = []
        for g in games:
            try:
                lines += client.boxscore(g)
            except RuntimeError as e:   # NHL server hiccup: carry on, the next run retries (nothing is cached)
                if failures is None:
                    raise
                failures.append(f"{g.away} @ {g.home} ({d}): {e}")
        lines_by_day[d] = lines
        games_by_day[d] = games
        d += timedelta(days=1)
    return lines_by_day, games_by_day


def team_sheet(pooler, roster, lines_by_day, game_days, last_day, directory, today, league=None):
    """Every stint of one pooler with the stats earned while owned: (team, former, moves).

    Uses the same matching (find_line) and dates (counts_on) as the engine, so team + former points
    add up to the pooler's total in the standings. Moves dated after `today` are not shown yet."""
    week_start = last_day - timedelta(days=6)
    rows = []
    for s in pooler.players:
        if s.added_on > today:
            continue
        if s.dropped_on is not None and s.dropped_on > today:
            s = replace(s, dropped_on=None)
        gp = g = a = pts = last7 = 0
        for d in game_days:
            if d > last_day or not s.counts_on(d):
                continue
            l = find_line(s, lines_by_day[d], [])      # unmatched names were already warned about by score_day
            if l is None:
                continue
            p = l.goals * roster.goal_points + l.assists * roster.assist_points
            gp, g, a, pts = gp + 1, g + l.goals, a + l.assists, pts + p
            if d >= week_start:
                last7 += p
        dp = directory.get(s.player_id)
        ppg, pct = (league or {}).get(s.player_id, (None, None))
        rows.append((s, {"player": dp.name if dp else s.name, "team": dp.team if dp else s.team,
                         "pos": "Déf" if s.position == "D" else "Att", "gp": gp, "g": g, "a": a, "pts": pts, "last7": last7,
                         "ppg": ppg, "pct": pct}))

    team = sorted((r for s, r in rows if s.dropped_on is None), key=lambda r: (-r["pts"], -r["gp"], r["player"]))
    former = sorted(({**r, "until": _short(s.dropped_on - timedelta(days=1)), "_d": s.dropped_on}
                     for s, r in rows if s.dropped_on is not None), key=lambda r: (r["_d"], r["player"]), reverse=True)
    for r in former:
        del r["_d"]

    # a move = a drop and an add on the same date (several on one date are paired in roster order)
    moves, adds = [], [(s, r) for s, r in rows if s.added_on > roster.start_date]
    for s, r in rows:
        if s.dropped_on is None:
            continue
        j = next((k for k, (t, _) in enumerate(adds) if t.added_on == s.dropped_on), None)
        new = adds.pop(j)[1] if j is not None else None
        moves.append({"date": s.dropped_on.isoformat(), "dateLabel": _short(s.dropped_on), "out": r["player"], "outPts": r["pts"],
                      "in": new["player"] if new else None, "inPts": new["pts"] if new else None})
    for t, r in adds:
        moves.append({"date": t.added_on.isoformat(), "dateLabel": _short(t.added_on), "out": None, "outPts": None,
                      "in": r["player"], "inPts": r["pts"]})
    moves.sort(key=lambda m: m["date"], reverse=True)
    return team, former, moves


MIN_GAMES_FOR_RANK = 5


def league_percentiles(lines_by_day, game_days, roster):
    """{player_id: (points_per_game, percentile)} for every NHL skater with enough games.

    Percentile = share of skaters of the same group (forwards or defensemen) with a lower season points per game,
    ties counted half. Season-wide (all teams), not only while owned by a pooler."""
    season = {}
    for d in game_days:
        for l in lines_by_day[d]:
            if l.position == "G":
                continue
            s = season.setdefault(l.player_id, [0, 0, "F"])
            s[0] += 1
            s[1] += l.goals * roster.goal_points + l.assists * roster.assist_points
            s[2] = "D" if l.position == "D" else "F"
    out = {}
    for group in ("F", "D"):
        rows = [(pid, v[1] / v[0]) for pid, v in season.items() if v[2] == group and v[0] >= MIN_GAMES_FOR_RANK]
        values = sorted(x for _, x in rows)
        n = len(values)
        for pid, x in rows:
            lo, hi = bisect_left(values, x), bisect_right(values, x)
            out[pid] = (round(x, 2), max(1, min(99, round(100 * (lo + (hi - lo) / 2) / n))))
    return out


def _rank_and_avg(values):
    """values {id: number} -> {id: {"v", "rank", "avg"}}; ties share a rank."""
    avg = round(sum(values.values()) / len(values), 1) if values else 0
    return {k: {"v": v, "rank": 1 + sum(1 for x in values.values() if x > v), "avg": avg} for k, v in values.items()}


def build_report(roster, client, today, game_types=(2,), demo=False, url=""):
    warnings = list(validate(roster))
    directory = {}
    for team in TEAM_CODES:
        for p in client.roster(team):
            directory[p.id] = p
    failures = []
    notes = []
    unresolved = resolve_ids(roster, list(directory.values()), notes)
    warnings += unresolved + [f"NOTE: {n}" for n in notes]
    full_name = lambda pid, fallback: directory[pid].name if pid in directory else fallback

    through = today - timedelta(days=1)
    lines_by_day, games_by_day = collect(client, roster.start_date, through, game_types, failures)
    game_days = sorted(d for d, l in lines_by_day.items() if l)
    last_day = game_days[-1] if game_days else through
    warnings += [f"GAME NOT LOADED: {f}" for f in failures]
    results = {d: score_day(roster, d, lines, warnings) for d, lines in lines_by_day.items()}

    rows = standings(roster, results, last_day)
    leader_total = rows[0][3]
    by_id_row = {r[1]: r for r in rows}

    # season progress: median games played per team, used for the full-season projection
    gp = defaultdict(int)
    for games in games_by_day.values():
        for g in games:
            gp[g.away] += 1
            gp[g.home] += 1
    gp_median = statistics.median(gp.values()) if gp else 0

    # running totals for the trend lines (last 8 game days)
    cum = {p.id: {} for p in roster.poolers}
    running = {p.id: 0 for p in roster.poolers}
    for d in game_days:
        for pid, (pts, _) in results[d].items():
            running[pid] += pts
            cum[pid][d] = running[pid]
    spark_days = [d for d in game_days if d <= last_day][-8:]

    # tonight's games
    schedule = {}
    for g in client.score(today):
        if g.date == today and not g.is_final and g.game_type in game_types:
            schedule[g.home] = (g.away, True, g.start_utc)
            schedule[g.away] = (g.home, False, g.start_utc)

    league = league_percentiles(lines_by_day, game_days, roster)
    trend_days = [d for d in game_days if d <= last_day]
    last_week = [d for d in trend_days if d > last_day - timedelta(days=7)]

    poolers = []
    for i, p in enumerate(roster.poolers):
        rank, _, name, total, yday, move = by_id_row[p.id]
        scorers = [{"player": full_name(pid, nm), "line": _ga(g, a), "pts": pts}
                   for nm, tm, g, a, pts, pid in (results[last_day][p.id][1] if last_day in results else [])]
        tonight = []
        for s in p.players:
            if not s.counts_on(today) or s.player_id is None:
                continue
            dp = directory.get(s.player_id)
            team = dp.team if dp else s.team
            if team in schedule:
                opp, home, start = schedule[team]
                tonight.append({"player": s.name, "game": f"{team} c. {opp}" if home else f"{team} à {opp}",
                                "time": _clock(start), "_sort": start})
        tonight.sort(key=lambda x: (x["_sort"], x["player"]))
        for t in tonight:
            del t["_sort"]
        sheet, former, moves = team_sheet(p, roster, lines_by_day, game_days, last_day, directory, today, league)
        if sum(r["pts"] for r in sheet + former) != total:
            warnings.append(f"{p.name}: team sheet adds up to {sum(r['pts'] for r in sheet + former)} pts, standings say {total} (check roster dates)")
        poolers.append({
            "id": p.id, "name": p.name, "initials": p.name[:2].upper(), "color": COLORS[i % len(COLORS)],
            "rank": rank, "move": move, "total": total, "yday": yday, "gap": leader_total - total,
            "proj": round(total * roster.season_games / gp_median) if gp_median else total,
            "spark": [cum[p.id].get(d, 0) for d in spark_days],
            "scorers": scorers, "tonight": tonight, "team": sheet, "former": former, "moves": moves,
            "trend": [cum[p.id].get(d, 0) for d in trend_days], "last7": sum(results[d][p.id][0] for d in last_week),
        })
    poolers.sort(key=lambda x: (x["rank"], x["name"]))
    # tiles for each pooler: value, rank among the poolers and pool average
    kpis = {k: _rank_and_avg({p["id"]: p[k] for p in poolers}) for k in ("total", "yday", "last7", "proj")}
    for p in poolers:
        p["kpi"] = {k: kpis[k][p["id"]] for k in kpis}

    # per-player history for streaks and slumps
    history = defaultdict(list)          # id -> [(date, points, goals, assists, name, team, position)]
    for d in game_days:
        for l in lines_by_day[d]:
            history[l.player_id].append((d, l.goals * roster.goal_points + l.assists * roster.assist_points, l.goals, l.assists, l.name, l.team, l.position))

    owned = {s.player_id for p in roster.poolers for s in p.players if s.counts_on(today) and s.player_id is not None}
    week = set(game_days[-7:])
    deals = []
    for pid, hist in history.items():
        if pid in owned or hist[-1][6] == "G":
            continue
        recent = [h for h in hist if h[0] in week]
        pts = sum(h[1] for h in recent)
        if pts == 0:
            continue
        streak = 0
        for h in reversed(hist):
            if h[1] > 0:
                streak += 1
            else:
                break
        g, a = sum(h[2] for h in recent), sum(h[3] for h in recent)
        team = hist[-1][5]
        meta = f"{team} · série de {streak} matchs" if streak >= 3 else f"{team} · {_ga(g, a)}"
        deals.append({"player": full_name(pid, hist[-1][4]), "meta": meta, "pts": pts, "hot": streak >= 3, "pct": league.get(pid, (None, None))[1], "_s": (-pts, -streak, hist[-1][4])})
    deals.sort(key=lambda x: x["_s"])
    deals = deals[:5]
    for dl in deals:
        del dl["_s"]

    cold = []
    for p in roster.poolers:
        for s in p.players:
            if not s.counts_on(today) or s.player_id not in history:
                continue
            last5 = history[s.player_id][-5:]
            if len(last5) >= 4 and sum(h[1] for h in last5) == 0 and (last_day - last5[-1][0]).days <= 7:
                cold.append({"player": s.name, "owner": p.name, "line": f"0 pt en {len(last5)} matchs", "_n": len(last5)})
    cold.sort(key=lambda x: (-x["_n"], x["player"]))
    cold = cold[:3]
    for c in cold:
        del c["_n"]

    # headline, tiles, awards, chatter
    pool_points = sum(p["yday"] for p in poolers)
    n_games = len(games_by_day.get(last_day, []))
    leaders = [p for p in poolers if p["rank"] == 1]
    movers = [p for p in poolers if p["move"] > 0]
    top_mover = max(movers, key=lambda p: (p["move"], p["yday"])) if movers else None
    if not game_days:
        headline = {"title": "La saison démarre bientôt", "text": "Aucun match joué pour l’instant."}
    elif len(leaders) > 1:
        headline = {"title": "Égalité au sommet", "text": f"{_names([p['name'] for p in leaders])} sont à égalité avec {leaders[0]['total']} points."}
    else:
        lead = leaders[0]
        took = lead["move"] > 0
        second = poolers[1]
        best = lead["scorers"][0] if lead["scorers"] else None
        text = (f"{best['player']} a ajouté {best['pts']} {_plural(best['pts'], 'point', 'points')} hier soir. " if best else "")
        text += f"{lead['name']} compte {lead['total']} points, {lead['total'] - second['total']} de plus que {second['name']}."
        headline = {"title": f"{lead['name']} prend le sommet" if took else f"{lead['name']} garde le sommet", "text": text}
    tiles = [
        {"value": str(pool_points), "label": "points dans le pool"},
        {"value": str(n_games), "label": _plural(n_games, "match joué", "matchs joués")},
        {"value": f"+{top_mover['move']}" if top_mover else "0", "label": f"{_plural(top_mover['move'], 'rang', 'rangs')} pour {top_mover['name']}" if top_mover else "changement au classement"},
    ]

    awards = []
    if pool_points:
        best_pts = max(p["yday"] for p in poolers)
        awards.append({"label": "Pooler de la soirée", "winner": _names([p["name"] for p in poolers if p["yday"] == best_pts], 2), "detail": f"+{best_pts} pts"})
        owned_scorers = [(sc["pts"], sc["player"], p["name"]) for p in poolers for sc in p["scorers"]]
        if owned_scorers:
            owned_scorers.sort(key=lambda x: (-x[0], x[1]))
            pts, player, owner = owned_scorers[0]
            awards.append({"label": "Meilleur joueur", "winner": player.split(" ")[-1], "detail": f"{pts} pts pour {owner}"})
        low = min(p["yday"] for p in poolers)
        awards.append({"label": "Au frette", "winner": _names([p["name"] for p in poolers if p["yday"] == low], 2), "detail": "0 pt" if low == 0 else f"{low} pts"})

    day_totals = {p.id: [results[d][p.id][0] for d in game_days] for p in roster.poolers}
    last3 = {p["id"]: sum(day_totals[p["id"]][-3:]) for p in poolers}
    chatter = []
    if len(game_days) >= 3 and len(poolers) > 2:
        hot = max(poolers, key=lambda p: (last3[p["id"]], -p["rank"]))
        cold_p = min(poolers, key=lambda p: (last3[p["id"]], -p["rank"]))
        if last3[hot["id"]] > last3[cold_p["id"]]:
            chatter.append({"tag": "En feu", "good": True, "name": hot["name"], "color": hot["color"],
                            "text": f"{hot['name']} a ramassé {last3[hot['id']]} points en 3 soirs, le meilleur rendement du pool."})
            chatter.append({"tag": "Au frette", "good": False, "name": cold_p["name"], "color": cold_p["color"],
                            "text": f"{cold_p['name']} n’a que {last3[cold_p['id']]} points en 3 soirs, le pire du pool. Une transaction s’impose."})
    close = [p for p in poolers[1:3] if 0 < p["gap"] <= 6]
    if close and len(leaders) == 1:
        c = close[0]
        chatter.append({"tag": "Dans le rétroviseur", "good": True, "name": c["name"], "color": c["color"], "text": f"{c['name']} n’est qu’à {c['gap']} {_plural(c['gap'], 'point', 'points')} du sommet. Rien n’est joué."})
    if top_mover and top_mover["move"] >= 2:
        chatter.append({"tag": "Remontée", "good": True, "name": top_mover["name"], "color": top_mover["color"], "text": f"{top_mover['name']} gagne {top_mover['move']} rangs en une soirée."})
    chatter = chatter[:4]

    since = (today - timedelta(days=7)).isoformat()
    recent_moves = [{"id": p["id"], "name": p["name"], "color": p["color"], "date": m["date"]}
                    for p in poolers for m in p["moves"] if m["date"] >= since]
    recent_moves.sort(key=lambda m: (m["date"], m["name"]), reverse=True)

    t = now_toronto()
    summary =[f"Pool de la LNH : rapport du {today.day} {MONTHS_FR[today.month - 1]}"]
    for p in poolers:
        mv = f" ({'+' if p['move'] > 0 else ''}{p['move']})" if p["move"] else ""
        summary.append(f"{p['rank']}. {p['name']} : {p['total']} pts (+{p['yday']}){mv}")
    if url:
        summary.append(url)

    return {
        "meta": {
            "demo": demo, "dayNumber": today.day, "month": MONTHS_FR[today.month - 1],
            "weekday": DAYS_FR[today.weekday()], "lastDay": last_day.isoformat(),
            "lastDayLabel": f"{last_day.day} {MONTHS_FR[last_day.month - 1]}", "seasonGames": roster.season_games,
            "updated": f"{t.day} {MONTHS_FR[t.month - 1]} à {t.hour} h {t.minute:02d}", "gamesTonight": len(schedule) // 2,
            "missingGames": len(failures),
            "unresolved": [u.split("'")[1] for u in unresolved if "'" in u],
        },
        "headline": headline, "tiles": tiles, "poolers": poolers, "deals": deals, "cold": cold,
        "awards": awards, "chatter": chatter, "recentMoves": recent_moves, "trendDays": [_short(d) for d in trend_days], "summary":"\n".join(summary), "warnings": sorted(set(warnings)),
    }
