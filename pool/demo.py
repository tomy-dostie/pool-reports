"""Synthetic NHL data for tests and previews: same interface as NhlClient, no network, clearly fake numbers."""
import random
from datetime import timedelta

from .engine import Line, norm_team
from .nhl import TEAM_CODES, DirPlayer, Game


class SyntheticClient:
    def __init__(self, roster, today, live=False):
        self.today = today
        self.live = live          # today's games: some in progress, some finished, some to come (evening preview)
        self.players = {}
        self.pool_ids = set()
        pid = 9_000_000
        for p in roster.poolers:
            for s in p.players:
                pid += 1
                team = norm_team(s.team) if s.team else "TOR"
                self.players.setdefault(team, []).append(DirPlayer(pid, s.name, s.position or "F", team))
                self.pool_ids.add(pid)
        for team in TEAM_CODES:
            for k in range(1, 4):
                pid += 1
                self.players.setdefault(team, []).append(DirPlayer(pid, f"Libre {team} {k}", "F" if k < 3 else "D", team))

    def roster(self, team):
        return self.players.get(team, [])

    def score(self, d):
        playing = [t for i, t in enumerate(TEAM_CODES) if (d.toordinal() + i) % 2 == 0]
        games = []
        for i in range(0, len(playing) - 1, 2):
            start = f"{d.isoformat()}T23:00:00Z" if i % 3 == 0 else f"{(d + timedelta(days=1)).isoformat()}T0{i % 3}:30:00Z"
            state = "OFF" if d < self.today else "FUT"
            if self.live and d == self.today:
                state = ("OFF", "LIVE", "LIVE", "FUT")[(i // 2) % 4]
            g = Game(int(d.strftime("%Y%m%d")) * 100 + i // 2, d, state, 2, playing[i], playing[i + 1], start)
            if self.live and d == self.today and g.started:      # scoreboard only matters for the live night
                lines = self.boxscore(g)
                g.away_score = sum(l.goals for l in lines if l.team == g.away)
                g.home_score = sum(l.goals for l in lines if l.team == g.home)
                g.period, g.clock = (3, "00:00") if g.is_final else (2, "08:41")
            games.append(g)
        return games

    def boxscore(self, game, cache=True):
        lines = []
        for team in (game.away, game.home):
            for p in self.players.get(team, []):
                rng = random.Random(game.id * 1000 + p.id)
                if rng.random() < 0.08:
                    continue
                star = p.id in self.pool_ids
                g = (1 if rng.random() < (0.22 if star else 0.08) else 0) + (1 if rng.random() < 0.03 else 0)
                a = (1 if rng.random() < (0.32 if star else 0.1) else 0) + (1 if rng.random() < 0.05 else 0)
                lines.append(Line(game.date, p.id, f"{p.name.split(' ')[0][0]}. {p.name.split(' ', 1)[-1]}", team, g, a, p.position))
        return lines
