from datetime import date
from pool.engine import *
from pool.engine import norm_team

D = lambda n: date(2026, 10, n)
def L(d, pid, name, team, g, a): return Line(d, pid, name, team, g, a)

def roster():
    return Roster([
        Pooler("alex", "Alex", [Stint("Nathan MacKinnon", "COL", 1, D(7)), Stint("Cale Makar", "COL", 2, D(7))]),
        Pooler("dan", "Dan", [Stint("Brock Boeser", "VAN", 3, D(7), D(20)), Stint("Connor Bedard", "CHI", 4, D(20))]),
    ])

def test_scoring_goals_and_assists():
    r = roster()
    res = score_day(r, D(8), [L(D(8), 1, "Nathan MacKinnon", "COL", 1, 3), L(D(8), 2, "Cale Makar", "COL", 0, 2)])
    assert res["alex"][0] == 6
    assert res["alex"][1][0][0] == "Nathan MacKinnon"

def test_unowned_players_ignored():
    res = score_day(roster(), D(8), [L(D(8), 99, "Someone Else", "TOR", 3, 3)])
    assert res["alex"][0] == 0 and res["dan"][0] == 0

def test_waiver_dropped_player_keeps_old_points_and_stops_counting():
    r = roster()
    days = {D(19): score_day(r, D(19), [L(D(19), 3, "Brock Boeser", "VAN", 1, 1)]),
            D(20): score_day(r, D(20), [L(D(20), 3, "Brock Boeser", "VAN", 2, 0), L(D(20), 4, "Connor Bedard", "CHI", 1, 1)])}
    assert days[D(19)]["dan"][0] == 2          # Boeser counts the day before the move
    assert days[D(20)]["dan"][0] == 2          # only Bedard counts on the move date
    s = standings(r, days, D(20))
    dan = [x for x in s if x[1] == "dan"][0]
    assert dan[3] == 4                          # 2 kept from Boeser + 2 from Bedard, nothing from Boeser's 2 goals on D20

def test_new_player_starts_at_zero():
    r = roster()
    res = score_day(r, D(19), [L(D(19), 4, "Connor Bedard", "CHI", 5, 5)])
    assert res["dan"][0] == 0                   # Bedard's points before he was added do not count

def test_name_fallback_and_accents():
    r = Roster([Pooler("a", "A", [Stint("Alex Pietrangelo", "", None, D(7))])])
    res = score_day(r, D(8), [L(D(8), 5, "Alex Pietrangelo", "VGK", 0, 1)])
    assert res["a"][0] == 1
    r2 = Roster([Pooler("a", "A", [Stint("Jonathan Marchessault", "", None, D(7))])])
    assert score_day(r2, D(8), [L(D(8), 6, "Jonathan Marchessault", "NSH", 1, 0)])["a"][0] == 1
    assert norm("Tomáš Hertl") == norm("Tomas Hertl")
    assert norm("J.T. Miller") == "jtmiller"

def test_ambiguous_name_warns_and_is_skipped():
    r = Roster([Pooler("a", "A", [Stint("Sebastian Aho", "", None, D(7))])])
    w = []
    res = score_day(r, D(8), [L(D(8), 7, "Sebastian Aho", "CAR", 1, 0), L(D(8), 8, "Sebastian Aho", "NYI", 0, 1)], w)
    assert res["a"][0] == 0 and any("Ambiguous" in x for x in w)

def test_ambiguous_name_resolved_by_team():
    r = Roster([Pooler("a", "A", [Stint("Sebastian Aho", "CAR", None, D(7))])])
    res = score_day(r, D(8), [L(D(8), 7, "Sebastian Aho", "CAR", 1, 0), L(D(8), 8, "Sebastian Aho", "NYI", 0, 1)])
    assert res["a"][0] == 1

def test_ranks_ties_and_movement():
    r = Roster([Pooler(i, i.title(), [Stint(f"P{i}", "", n, D(7))]) for n, i in enumerate(["a", "b", "c"], 1)])
    days = {D(8): score_day(r, D(8), [L(D(8), 1, "Pa", "X", 0, 3), L(D(8), 2, "Pb", "X", 0, 2), L(D(8), 3, "Pc", "X", 0, 1)]),
            D(9): score_day(r, D(9), [L(D(9), 3, "Pc", "X", 0, 1), L(D(9), 2, "Pb", "X", 0, 1)])}
    s = standings(r, days, D(9))
    by = {x[1]: x for x in s}
    assert by["a"][0] == 1 and by["a"][3] == 3
    assert by["a"][0] == by["b"][0] == 1 and by["c"][0] == 3
    assert by["c"][5] == 0                         # c was 3rd before, still 3rd
    assert by["b"][4] == 1 and by["c"][4] == 1 and by["c"][3] == 2   # yesterday's points, c has 2 total

def test_validate_overlapping_ownership():
    r = Roster([Pooler("a", "A", [Stint("X", "", 1, D(7))]), Pooler("b", "B", [Stint("X", "", 1, D(10))])])
    assert validate(r)
    r2 = Roster([Pooler("a", "A", [Stint("X", "", 1, D(7), D(10))]), Pooler("b", "B", [Stint("X", "", 1, D(10))])])
    assert validate(r2) == []                      # clean hand-off on the same date
    r3 = Roster([Pooler("a", "A", [Stint("X", "", 1, D(7), D(7))])])
    assert validate(r3)

def test_same_player_readded_later_counts_both_stints():
    r = Roster([Pooler("a", "A", [Stint("X", "", 1, D(7), D(10)), Stint("X", "", 1, D(15))])])
    for d, expected in [(D(8), 1), (D(12), 0), (D(16), 1)]:
        assert score_day(r, d, [L(d, 1, "X", "T", 1, 0)])["a"][0] == expected


def test_team_codes_from_poolexpert_match_nhl_codes():
    r = Roster([Pooler("a", "A", [Stint("Sebastian Aho", "CAR", None, D(7)), Stint("Brayden Point", "TB", None, D(7))])])
    lines = [L(D(8), 7, "Sebastian Aho", "CAR", 1, 0), L(D(8), 8, "Sebastian Aho", "NYI", 0, 1)]
    assert score_day(r, D(8), lines)["a"][0] == 1
    r2 = Roster([Pooler("a", "A", [Stint("Sebastian Aho", "NYI", None, D(7))])])
    assert score_day(r2, D(8), lines)["a"][0] == 1
    r3 = Roster([Pooler("a", "A", [Stint("Same Name", "TB", None, D(7))])])
    two = [L(D(8), 1, "Same Name", "TBL", 2, 0), L(D(8), 2, "Same Name", "WPG", 0, 5)]
    assert score_day(r3, D(8), two)["a"][0] == 2
    assert norm_team("WIN") == "WPG" and norm_team("tb") == "TBL" and norm_team("UTA") == "UTA"

def test_same_name_same_team_resolved_by_position():
    # two Elias Petterssons in Vancouver: a forward and a defenseman
    lines = [Line(D(8), 10, "Elias Pettersson", "VAN", 1, 1, "F"), Line(D(8), 11, "Elias Pettersson", "VAN", 0, 1, "D")]
    fwd = Roster([Pooler("a", "A", [Stint("Elias Pettersson", "VAN", None, D(7), position="F")])])
    dfn = Roster([Pooler("a", "A", [Stint("Elias Pettersson", "VAN", None, D(7), position="D")])])
    none = Roster([Pooler("a", "A", [Stint("Elias Pettersson", "VAN", None, D(7))])])
    assert score_day(fwd, D(8), lines)["a"][0] == 2
    assert score_day(dfn, D(8), lines)["a"][0] == 1
    w = []
    assert score_day(none, D(8), lines, w)["a"][0] == 0 and w
