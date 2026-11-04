"""Parsers and the engine against real NHL responses saved in tests/fixtures (captured 2026-10-28)."""
import json
import os
from datetime import date

from pool.engine import Pooler, Roster, Stint, norm, score_day
from pool.nhl import DirPlayer, parse_boxscore, parse_roster, parse_score, resolve_ids

FX = os.path.join(os.path.dirname(__file__), "fixtures")
D = date(2026, 10, 27)


def load(name):
    return json.load(open(os.path.join(FX, name), encoding="utf-8"))


def test_score_lists_finished_regular_season_games():
    games = parse_score(load("score-2026-10-27.json"))
    assert len(games) == 11
    assert all(g.is_final and g.date == D and g.game_type == 2 for g in games)
    first = next(g for g in games if g.id == 2026020188)
    assert (first.away, first.home) == ("CBJ", "PHI")
    assert first.away_score == 4 and first.period == 4 and first.period_type == "OT" and first.started


def test_unfinished_games_are_never_cached(tmp_path):
    from pool.nhl import Game, NhlClient
    calls = []
    client = NhlClient(str(tmp_path))
    client._fetch = lambda path: calls.append(path) or load("boxscore-2026020188.json")
    live = Game(1, D, "LIVE", 2, "CBJ", "PHI", "")
    final = Game(2, D, "OFF", 2, "CBJ", "PHI", "")
    client.boxscore(live); client.boxscore(live)
    client.boxscore(final, cache=False)
    assert len(calls) == 3 and not list(tmp_path.iterdir())          # nothing written while live / live run
    client.boxscore(final); client.boxscore(final)
    assert len(calls) == 4 and (tmp_path / "boxscore-2.json").exists()   # morning run: cached once


def test_boxscore_gives_goals_assists_ids_positions():
    lines = parse_boxscore(load("boxscore-2026020188.json"), D)
    assert len(lines) == 40
    by = {l.player_id: l for l in lines}
    k = by[8482660]
    assert (k.name, k.team, k.goals, k.assists, k.position) == ("K. Johnson", "CBJ", 2, 1, "F")
    w = by[8478460]
    assert (w.goals, w.assists, w.position) == (0, 2, "D")
    assert (by[8481533].team, by[8481533].goals, by[8481533].assists) == ("PHI", 1, 1)
    assert sum(l.position == "G" for l in lines) == 4


def test_roster_gives_full_names_and_ids():
    roster = parse_roster(load("roster-COL.json"), "COL")
    assert len(roster) == 22
    by = {p.id: p for p in roster}
    assert (by[8477492].name, by[8477492].position) == ("Nathan MacKinnon", "F")
    assert by[8480069].position == "D"
    assert next(p for p in roster if norm(p.name) == "martinnecas").id == 8480039


def test_resolve_ids_uses_names_team_and_position():
    directory = [DirPlayer(1, "Elias Pettersson", "F", "VAN"), DirPlayer(2, "Elias Pettersson", "D", "VAN"),
                 DirPlayer(3, "Sebastian Aho", "F", "CAR"), DirPlayer(4, "Sebastian Aho", "D", "NYI"),
                 DirPlayer(5, "Brayden Point", "F", "TBL"), DirPlayer(6, "Tim Stützle", "F", "OTT")]
    d0 = date(2026, 9, 29)
    r = Roster([Pooler("a", "A", [Stint("Elias Pettersson", "VAN", None, d0, None, "F"), Stint("Sebastian Aho", "CAR", None, d0, None, "F"),
                                  Stint("Brayden Point", "TB", None, d0, None, "F"), Stint("Tim Stutzle", "OTT", None, d0, None, "F"),
                                  Stint("Nobody Here", "TOR", None, d0, None, "F")])])
    problems = resolve_ids(r, directory)
    ids = [s.player_id for s in r.poolers[0].players]
    assert ids == [1, 3, 5, 6, None]
    assert len(problems) == 1 and "Nobody Here" in problems[0]


def test_real_game_scores_through_the_engine_by_id():
    d0 = date(2026, 9, 29)
    r = Roster([Pooler("vinny", "Vinny", [Stint("Kent Johnson", "CBJ", 8482660, d0)]),
                Pooler("jeff", "Jeff", [Stint("Adam Fantilli", "CBJ", 8484166, d0), Stint("Matthew Knies", "CBJ", 8482720, d0)]),
                Pooler("gab", "Gab", [Stint("Trevor Zegras", "PHI", 8481533, d0)])])
    res = score_day(r, D, parse_boxscore(load("boxscore-2026020188.json"), D))
    assert res["vinny"][0] == 3 and res["jeff"][0] == 3 and res["gab"][0] == 2


def test_resolve_ids_handles_nicknames_and_reports_failures():
    directory = [DirPlayer(10, "Mitchell Marner", "F", "VGK"), DirPlayer(11, "Zachary Werenski", "D", "CBJ"),
                 DirPlayer(12, "Matthew Boldy", "F", "MIN"), DirPlayer(13, "Alexander Ovechkin", "F", "WSH")]
    d0 = date(2026, 9, 29)
    r = Roster([Pooler("a", "A", [Stint("Mitch Marner", "VGK", None, d0, None, "F"), Stint("Zach Werenski", "CBJ", None, d0, None, "D"),
                                  Stint("Matt Boldy", "MIN", None, d0, None, "F"), Stint("Alex Ovechkin", "WSH", None, d0, None, "F"),
                                  Stint("Totally Unknown", "TOR", None, d0, None, "F")])])
    notes = []
    problems = resolve_ids(r, directory, notes)
    assert [s.player_id for s in r.poolers[0].players] == [10, 11, 12, 13, None]
    assert len(notes) == 4 and len(problems) == 1


def test_unresolved_player_still_scores_from_abbreviated_box_name():
    d0 = date(2026, 9, 29)
    r = Roster([Pooler("v", "V", [Stint("Kent Johnson", "CBJ", None, d0, None, "F")])])
    res = score_day(r, D, parse_boxscore(load("boxscore-2026020188.json"), D))
    assert res["v"][0] == 3
