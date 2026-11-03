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
    owned_names = {s.name for p in roster.poolers for s in p.players if s.dropped_on is None}
    assert data["deals"] and all(d["player"] not in owned_names for d in data["deals"])
    pts = [d["pts"] for d in data["deals"]]
    assert pts == sorted(pts, reverse=True)


def test_awards_and_text(built):
    _, _, data = built
    assert {a["label"] for a in data["awards"]} == {"Pooler de la soirée", "Meilleur joueur", "Au frette"}
    assert data["headline"]["title"] and data["summary"].startswith("Pool de la LNH")
    assert len(data["summary"].splitlines()) == 11


def test_page_embeds_data_safely(built):
    _, _, data = built
    page = render(data)
    assert "window.DATA = {" in page and page.count("</script>") == 1
    evil = dict(data, headline={"title": "</script><b>x", "text": "y"})
    assert render(evil).count("</script>") == 1
