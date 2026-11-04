"""Whole pipeline on synthetic data (no network): numbers must be consistent with the engine."""
import json
import os
import re
from datetime import date

import pytest

from pool.demo import SyntheticClient
from pool.engine import load_roster, score_day, standings
from pool.render import render
from pool.report import build_report, collect

ROOT = os.path.join(os.path.dirname(__file__), "..")
TODAY = date(2026, 10, 28)


@pytest.fixture(scope="module")
def built():
    roster = load_roster(os.path.join(ROOT, "roster.json"))
    client = SyntheticClient(roster, TODAY)
    return roster, client, build_report(roster, client, TODAY, demo=True)


def test_roster_file_is_sound():
    r = load_roster(os.path.join(ROOT, "roster.json"))
    assert len(r.poolers) == 10 and r.season_games == 84
    for p in r.poolers:
        active = [s for s in p.players if s.dropped_on is None]
        assert len(active) == 16
        assert sum(s.position == "D" for s in active) == 4


def test_pipeline_resolves_everyone_and_has_no_warnings(built):
    roster, _, data = built
    assert data["warnings"] == []
    assert all(s.player_id is not None for p in roster.poolers for s in p.players)


def test_standings_match_the_engine(built):
    roster, client, data = built
    lines_by_day, _ = collect(client, roster.start_date, TODAY.replace(day=27))
    results = {d: score_day(roster, d, l) for d, l in lines_by_day.items()}
    last = date.fromisoformat(data["meta"]["lastDay"])
    expected = {r[1]: r for r in standings(roster, results, last)}
    for p in data["poolers"]:
        e = expected[p["id"]]
        assert (p["rank"], p["total"], p["yday"], p["move"]) == (e[0], e[3], e[4], e[5])
        assert p["gap"] == max(x["total"] for x in data["poolers"]) - p["total"]
    ranks = [p["rank"] for p in data["poolers"]]
    assert ranks == sorted(ranks) and ranks[0] == 1


def test_trend_lines_end_at_the_total(built):
    _, _, data = built
    for p in data["poolers"]:
        assert p["spark"][-1] == p["total"]
        assert p["spark"] == sorted(p["spark"])          # running totals never go down


def test_tonight_only_lists_active_players_whose_team_plays(built):
    roster, client, data = built
    playing = {t for g in client.score(TODAY) for t in (g.away, g.home)}
    for p in data["poolers"]:
        for t in p["tonight"]:
            assert t["game"].split(" ")[0] in playing and re.match(r"^\d+ h( \d\d)?$", t["time"])


def test_free_agents_exclude_owned_players(built):
    roster, _, data = built
    # owned on the report date (a player added later, e.g. Jamie Benn on Oct 31, is still a free agent on Oct 28)
    owned_names = {s.name for p in roster.poolers for s in p.players if s.counts_on(TODAY)}
    assert data["deals"] and all(d["player"] not in owned_names for d in data["deals"])
    pts = [d["pts"] for d in data["deals"]]
    assert pts == sorted(pts, reverse=True)


def test_awards_and_text(built):
    _, _, data = built
    assert {a["label"] for a in data["awards"]} == {"Pooler de la soirée", "Meilleur joueur", "Au frette"}
    assert data["headline"]["title"] and data["summary"].startswith("Pool de la LNH")
    assert len(data["summary"].splitlines()) == 11


def test_team_sheet_adds_up_to_the_total(built):
    roster, _, data = built
    for p in data["poolers"]:
        assert p["team"] and {"team", "former", "moves"} <= set(p)
        assert sum(r["pts"] for r in p["team"] + p["former"]) == p["total"]
        for r in p["team"] + p["former"]:
            assert r["pts"] == r["g"] + r["a"] and r["gp"] >= 0 and 0 <= r["last7"] <= r["pts"]
        pts = [r["pts"] for r in p["team"]]
        assert pts == sorted(pts, reverse=True)
        assert len(p["team"]) == 16          # every active player is listed, even with 0 pts


def test_moves_pair_drop_and_add_and_hide_future_ones(built):
    _, _, data = built
    rej = next(p for p in data["poolers"] if p["id"] == "rej")
    # TODAY is Oct 28: the Oct 23 move is shown, the Oct 31 one (Frondell -> Cirelli) is not yet
    assert [(m["date"], m["out"], m["in"]) for m in rej["moves"]] == [("2026-10-23", "K'Andre Miller", "Morgan Rielly")]
    assert [r["player"] for r in rej["former"]] == ["K'Andre Miller"] and rej["former"][0]["until"] == "22 oct."
    names = [r["player"] for r in rej["team"]]
    assert "Anton Frondell" in names and "Anthony Cirelli" not in names
    assert any(m["id"] == "rej" and m["date"] == "2026-10-23" for m in data["recentMoves"])


def test_drop_day_points_go_to_nobody_on_the_team_sheet():
    from pool.report import team_sheet
    from pool.engine import Line, Pooler, Roster, Stint
    d1, d2 = date(2026, 10, 1), date(2026, 10, 2)
    old, new = Stint("Old Guy", "TOR", 1, date(2026, 9, 29), d2), Stint("New Guy", "MTL", 2, d2, None)
    roster = Roster([Pooler("x", "X", [old, new])], start_date=date(2026, 9, 29))
    lines = {d1: [Line(d1, 1, "O. Guy", "TOR", 1, 0)], d2: [Line(d2, 1, "O. Guy", "TOR", 2, 0), Line(d2, 2, "N. Guy", "MTL", 0, 1)]}
    team, former, moves = team_sheet(roster.poolers[0], roster, lines, [d1, d2], d2, {}, date(2026, 10, 3))
    assert [(r["player"], r["pts"]) for r in team] == [("New Guy", 1)]
    assert [(r["player"], r["pts"], r["until"], r["after"]) for r in former] == [("Old Guy", 1, "1 oct.", 2)]
    assert moves == [{"date": "2026-10-02", "dateLabel": "2 oct.", "out": "Old Guy", "outPts": 1, "outAfter": 2, "in": "New Guy", "inPts": 1}]


def test_trades_judge_each_move_by_what_came_after(built):
    _, _, data = built
    by_id = {p["id"]: p for p in data["poolers"]}
    assert data["trades"]
    for t in data["trades"]:
        m = next(m for m in by_id[t["id"]]["moves"] if m["out"] == t["out"] and m["in"] == t["in"])
        assert t["diff"] == m["inPts"] - m["outAfter"] and m["outAfter"] >= 0
        assert t["tag"] == ("Bon coup" if t["diff"] > 0 else "Regret" if t["diff"] < 0 else "Égalité")
    diffs = [t["diff"] for t in data["trades"]]
    assert diffs == sorted(diffs, reverse=True)
    for p in data["poolers"]:
        assert all(r["after"] is not None and r["after"] >= 0 for r in p["former"])
        assert all("after" not in r for r in p["team"])


def test_nights_won_are_symmetric_and_ranks_end_at_today(built):
    roster, _, data = built
    by_id = {p["id"]: p for p in data["poolers"]}
    n_days = len(data["trendDays"])
    for p in data["poolers"]:
        assert len(p["ranks"]) == n_days and p["ranks"][-1] == p["rank"]
        assert all(1 <= r <= len(by_id) for r in p["ranks"])
        assert set(p["h2h"]) == set(by_id) - {p["id"]}
        for q, (w, l, t) in p["h2h"].items():
            assert w + l + t == n_days
            assert by_id[q]["h2h"][p["id"]] == [l, w, t]                  # my wins are their losses
            assert by_id[q]["h2hStreak"][p["id"]] == -p["h2hStreak"][q]


def test_nights_won_brute_force():
    from pool.report import nightly
    from pool.engine import Pooler, Roster
    d = [date(2026, 10, k) for k in (1, 2, 3, 4)]
    roster = Roster([Pooler("a", "A"), Pooler("b", "B")])
    pts = {"a": [3, 1, 2, 4], "b": [1, 1, 3, 0]}
    results = {x: {i: (pts[i][k], []) for i in pts} for k, x in enumerate(d)}
    ranks, h2h, streaks = nightly(roster, results, d, {x: [] for x in d})
    assert h2h["a"]["b"] == [2, 1, 1] and h2h["b"]["a"] == [1, 2, 1]
    assert streaks["a"]["b"] == 1 and streaks["b"]["a"] == -1
    assert ranks["a"] == [1, 1, 1, 1] and ranks["b"] == [2, 2, 2, 2]    # a: 3,4,6,10  b: 1,2,5,5


def test_season_records(built):
    roster, _, data = built
    by_id = {p["id"]: p for p in data["poolers"]}
    recs = {r["key"]: r for r in data["records"]}
    assert {"night", "player", "first"} <= set(recs)
    best_night = max(max(b - a for a, b in zip([0] + p["trend"], p["trend"])) for p in data["poolers"])
    assert recs["night"]["value"] == best_night
    longest = max(max((sum(1 for _ in g) for k, g in __import__("itertools").groupby(p["ranks"]) if k == 1), default=0) for p in data["poolers"])
    assert recs["first"]["value"] == longest
    assert all(r["who"] in by_id and isinstance(r["new"], bool) and r["text"] for r in data["records"])


def test_tonight_clash_is_the_busiest_game(built):
    _, _, data = built
    per_game = {}
    for p in data["poolers"]:
        for t in p["tonight"]:
            a, sep, b = t["game"].partition(" c. ") if " c. " in t["game"] else t["game"].partition(" à ")
            home = a if sep == " c. " else b
            per_game.setdefault(home, []).append(p["id"])
    c = data["tonightClash"]
    assert c and c["players"] == max(len(v) for v in per_game.values())
    home = c["game"].split(" à ")[1]
    assert c["players"] == len(per_game[home]) == sum(x["n"] for x in c["poolers"])


def test_pace_catch_threat_and_no_far_dates():
    from pool.report import pace
    days = [date(2026, 10, 20) + __import__("datetime").timedelta(days=k) for k in range(14)]
    nightly_pts = {"a": 2, "b": 3, "c": 0}                   # per day over the last 14 days
    results = {d: {i: (v, []) for i, v in nightly_pts.items()} for d in days}
    poolers = [{"id": "a", "name": "A", "total": 100}, {"id": "b", "name": "B", "total": 90}, {"id": "c", "name": "C", "total": 10}]
    out = pace(poolers, results, days, days[-1], date(2026, 9, 29))
    # b gains 1 pt/day on a, 10 behind -> passes a in 11 days (needs to be strictly ahead)
    assert out["b"]["chase"] == {"kind": "catch", "id": "a", "name": "A", "gain": 1.0, "date": "13 nov."}
    assert out["a"]["chase"]["kind"] == "threat" and out["a"]["chase"]["id"] == "b"
    assert out["c"]["chase"] is None                         # slower than b: never catches up
    assert out["a"]["milestone"]["value"] == 150
    assert out["c"]["milestone"] is None or out["c"]["milestone"]["value"] == 50


def test_page_has_the_team_card(built):
    _, _, data = built
    page = render(data)
    assert "L’alignement" in page and "openTeam" in page and "#equipe" in page


def test_page_loads_nothing_from_other_sites(built, tmp_path):
    from pool.render import copy_static
    _, _, data = built
    page = render(data)
    assert "googleapis" not in page and "gstatic" not in page and "Content-Security-Policy" in page
    assert not re.search(r"""(src|href)=["']?https?://""", page)
    copy_static(str(tmp_path))
    for name in re.findall(r"url\(fonts/([\w-]+\.woff2)\)", page):
        assert (tmp_path / "fonts" / name).stat().st_size > 1000
    assert (tmp_path / "fonts" / "OFL.txt").exists()


def test_league_percentiles_rank_within_position():
    from pool.report import league_percentiles
    from pool.engine import Line, Roster
    days = [date(2026, 10, d) for d in range(1, 6)]
    lines = {d: [Line(d, 1, "A", "TOR", 1, 1, "F"), Line(d, 2, "B", "TOR", 1, 0, "F"), Line(d, 3, "C", "TOR", 0, 0, "F"),
                 Line(d, 4, "D", "TOR", 0, 1, "D"), Line(d, 5, "G", "TOR", 0, 1, "G")] for d in days}
    lines[days[0]].append(Line(days[0], 6, "Rookie", "MTL", 3, 0, "F"))      # 1 game: not ranked
    out = league_percentiles(lines, days, Roster([]))
    assert set(out) == {1, 2, 3, 4}                                          # no goalie, no 1-game player
    assert out[1] == (2.0, 83) and out[2] == (1.0, 50) and out[3] == (0.0, 17)
    assert out[4] == (1.0, 50)                                               # alone among defensemen


def test_tiles_trend_and_preview_page(built):
    from pool.render_edge import render_edge
    _, _, data = built
    n = len(data["poolers"])
    for p in data["poolers"]:
        assert p["trend"][-1] == p["total"] and len(p["trend"]) == len(data["trendDays"])
        assert set(p["kpi"]) == {"total", "yday", "last7", "proj"} and p["kpi"]["total"]["rank"] == p["rank"]
        assert all(1 <= k["rank"] <= n for k in p["kpi"].values()) and 0 <= p["last7"] <= p["total"]
        assert all(r["pct"] is None or 1 <= r["pct"] <= 99 for r in p["team"])
    assert any(r["pct"] is not None for p in data["poolers"] for r in p["team"])
    page = render_edge(data)
    assert page.count("</script>") == 1 and "url(fonts/barlow-400.woff2)" in page and "googleapis" not in page
    assert "T’es qui ?" in page and "Depuis ta dernière visite" in page and "Bons coups et regrets" in page
    assert ".innerHTML" not in page


def test_build_writes_new_main_page_classic_fallback_and_redirect(tmp_path):
    from pool.__main__ import main
    out = tmp_path / "site"
    assert main(["build", "--demo", "--today", "2026-10-28", "--roster", os.path.join(ROOT, "roster.json"),
                 "--out", str(out), "--classic", str(out / "classique")]) == 0
    assert "Pool <b>LNH</b> · Analyse" in (out / "index.html").read_text(encoding="utf-8")
    assert "Ma soirée" in (out / "classique" / "index.html").read_text(encoding="utf-8")
    assert 'url=../' in (out / "apercu" / "index.html").read_text(encoding="utf-8")
    for d in (out, out / "classique"):
        assert (d / "fonts" / "barlow-400.woff2").exists()
    manifest = json.loads((out / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["display"] == "standalone" and manifest["start_url"] == "./"
    for icon in {i["src"] for i in manifest["icons"]} | {"apple-touch-icon.png"}:
        assert (out / icon).read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    page = (out / "index.html").read_text(encoding="utf-8")
    assert 'rel="manifest" href="manifest.webmanifest"' in page and "manifest-src 'self'" in page
    assert json.loads((out / "data.json").read_text(encoding="utf-8"))["meta"]["demo"] is True


def test_page_embeds_data_safely(built):
    _, _, data = built
    page = render(data)
    assert "window.DATA = {" in page and page.count("</script>") == 1
    evil = dict(data, headline={"title": "</script><b>x", "text": "y"})
    assert render(evil).count("</script>") == 1


def test_failed_boxscore_does_not_crash_the_build():
    import os
    from pool.engine import load_roster
    from pool.report import collect
    from pool.demo import SyntheticClient
    from datetime import date
    class Flaky(SyntheticClient):
        def boxscore(self, game):
            raise RuntimeError("timeout")
    fails = []
    lines, games = collect(Flaky(load_roster(os.path.join(os.path.dirname(__file__), '..', 'roster.json')), date(2026, 10, 28)), date(2026, 10, 20), date(2026, 10, 21), failures=fails)
    assert fails and all(not v for v in lines.values())
