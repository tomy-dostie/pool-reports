"""NHL web API client (unofficial, api-web.nhle.com). Parsers are pure and tested on real responses."""
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date

from .engine import Line, norm, norm_team

BASE = "https://api-web.nhle.com/"
TEAM_CODES = ["ANA", "BOS", "BUF", "CGY", "CAR", "CHI", "COL", "CBJ", "DAL", "DET", "EDM", "FLA", "LAK", "MIN", "MTL", "NSH",
              "NJD", "NYI", "NYR", "OTT", "PHI", "PIT", "SEA", "SJS", "STL", "TBL", "TOR", "UTA", "VAN", "VGK", "WSH", "WPG"]


@dataclass
class Game:
    id: int
    date: date
    state: str
    game_type: int          # 1 preseason, 2 regular season, 3 playoffs
    away: str
    home: str
    start_utc: str

    @property
    def is_final(self):
        return self.state in ("OFF", "FINAL")


@dataclass
class DirPlayer:
    id: int
    name: str
    position: str           # F, D or G
    team: str


def parse_score(js):
    return [Game(g["id"], date.fromisoformat(g["gameDate"]), g.get("gameState", ""), g.get("gameType", 2),
                 g["awayTeam"]["abbrev"], g["homeTeam"]["abbrev"], g.get("startTimeUTC", ""))
            for g in js.get("games", [])]


def parse_boxscore(js, d):
    """One Line per skater/goalie who dressed. Names are abbreviated ('K. Johnson'): match by player id."""
    out = []
    stats = js.get("playerByGameStats")
    if not stats:
        return out
    for side in ("awayTeam", "homeTeam"):
        team = js[side]["abbrev"]
        for group, pos in (("forwards", "F"), ("defense", "D"), ("goalies", "G")):
            for p in stats.get(side, {}).get(group, []):
                out.append(Line(d, p["playerId"], p["name"]["default"], team, p.get("goals", 0), p.get("assists", 0), pos))
    return out


def parse_roster(js, team):
    out = []
    for group, pos in (("forwards", "F"), ("defensemen", "D"), ("goalies", "G")):
        for p in js.get(group, []):
            out.append(DirPlayer(p["id"], f'{p["firstName"]["default"]} {p["lastName"]["default"]}'.strip(), pos, team))
    return out


class NhlClient:
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        self._rosters = {}

    def _fetch(self, path):
        last = None
        for attempt in range(6):
            try:
                req = urllib.request.Request(BASE + path, headers={"User-Agent": "pool-reports/1.0"})
                with urllib.request.urlopen(req, timeout=45) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except (OSError, ValueError) as e:   # timeouts, resets, HTTP errors, truncated JSON
                last = e
                time.sleep(min(30, 3 * 2 ** attempt))
        raise RuntimeError(f"NHL API request failed: {path}: {last}")

    def _cached(self, path, name):
        p = os.path.join(self.cache_dir, name)
        if os.path.exists(p):
            return json.load(open(p, encoding="utf-8"))
        js = self._fetch(path)
        os.makedirs(self.cache_dir, exist_ok=True)
        json.dump(js, open(p, "w", encoding="utf-8"))
        return js

    def score(self, d):
        """Games of one NHL day. A day is cached only once every game on it is final (off days are re-checked)."""
        name = f"score-{d.isoformat()}.json"
        p = os.path.join(self.cache_dir, name)
        if os.path.exists(p):
            return parse_score(json.load(open(p, encoding="utf-8")))
        js = self._fetch(f"v1/score/{d.isoformat()}")
        games = parse_score(js)
        if games and all(g.is_final for g in games):
            os.makedirs(self.cache_dir, exist_ok=True)
            json.dump(js, open(p, "w", encoding="utf-8"))
        return games

    def boxscore(self, game):
        return parse_boxscore(self._cached(f"v1/gamecenter/{game.id}/boxscore", f"boxscore-{game.id}.json"), game.date)

    def roster(self, team):
        if team not in self._rosters:
            self._rosters[team] = parse_roster(self._fetch(f"v1/roster/{team}/current"), team)
        return self._rosters[team]


def resolve_ids(roster, directory, notes=None):
    """Fill in player_id on every stint that lacks one, from the NHL rosters.

    Tries the full name, then first initial + last name (Mitch / Mitchell, Zach / Zachary), then last name
    alone on the same team. Returns the players it could NOT resolve; `notes` receives what it matched loosely.
    """
    notes = notes if notes is not None else []
    by_name, by_initial, by_last = {}, {}, {}
    for p in directory:
        first, _, last = p.name.partition(" ")
        by_name.setdefault(norm(p.name), []).append(p)
        if last:
            by_initial.setdefault(norm(first[0] + last), []).append(p)
            by_last.setdefault(norm(last), []).append(p)

    def narrow(c, s):
        if len(c) > 1 and s.team:
            c = [p for p in c if p.team == norm_team(s.team)] or c
        if len(c) > 1 and s.position:
            c = [p for p in c if p.position == s.position] or c
        return c

    problems = []
    for pooler in roster.poolers:
        for s in pooler.players:
            if s.player_id is not None:
                continue
            first, _, last = s.name.partition(" ")
            c = narrow(by_name.get(norm(s.name), []), s)
            loose = False
            if not c and last:
                c, loose = narrow(by_initial.get(norm(first[0] + last), []), s), True
            if not c and last and s.team:
                c, loose = [p for p in narrow(by_last.get(norm(last), []), s) if p.team == norm_team(s.team)], True
            if len(c) == 1:
                s.player_id = c[0].id
                if loose:
                    notes.append(f"{pooler.name}: '{s.name}' matched loosely to '{c[0].name}' ({c[0].team})")
            elif not c:
                problems.append(f"{pooler.name}: '{s.name}' not found on any current NHL roster (spelling? injured?)")
            else:
                problems.append(f"{pooler.name}: '{s.name}' matches {len(c)} players; set playerId by hand")
    return problems
