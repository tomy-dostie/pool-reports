"""python -m pool build|check  (see README.md)"""
import argparse
import json
import os
import sys
from datetime import date, timedelta

from .engine import load_roster, norm, score_day
from .nhl import NhlClient
from .render import render
from .report import build_report, collect, now_toronto


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pool")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build the web page")
    b.add_argument("--roster", default="roster.json")
    b.add_argument("--out", default="site")
    b.add_argument("--cache", default="cache")
    b.add_argument("--today", help="YYYY-MM-DD (default: today in Toronto)")
    b.add_argument("--demo", action="store_true", help="synthetic data, no network")
    c = sub.add_parser("check", help="compare with PoolExpert numbers")
    c.add_argument("--roster", default="roster.json")
    c.add_argument("--expected", default="expected.json")
    c.add_argument("--cache", default="cache")
    a = ap.parse_args(argv)

    roster = load_roster(a.roster)
    if a.cmd == "build":
        today = date.fromisoformat(a.today) if a.today else now_toronto().date()
        if a.demo:
            from .demo import SyntheticClient
            client = SyntheticClient(roster, today)
        else:
            client = NhlClient(a.cache)
        data = build_report(roster, client, today, demo=a.demo, url=os.environ.get("REPORT_URL", ""))
        os.makedirs(a.out, exist_ok=True)
        open(os.path.join(a.out, "index.html"), "w", encoding="utf-8").write(render(data))
        json.dump(data, open(os.path.join(a.out, "data.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        open(os.path.join(a.out, "summary.txt"), "w", encoding="utf-8").write(data["summary"])
        for w in data["warnings"]:
            print("WARNING:", w)
        print(f"Built {a.out}/index.html (results of {data['meta']['lastDay']}, {len(data['poolers'])} poolers)")
        return 0

    # check
    expected = json.load(open(a.expected, encoding="utf-8"))
    through = date.fromisoformat(expected["through"])
    from .nhl import TEAM_CODES, resolve_ids
    client = NhlClient(a.cache)
    directory = [p for t in TEAM_CODES for p in client.roster(t)]
    problems = resolve_ids(roster, directory)
    for pr in problems:
        print("WARNING:", pr)
    lines_by_day, _ = collect(client, roster.start_date, through)
    ok = diffs = 0
    print(f"Check through {through}  (expected = PoolExpert, ours = NHL data + roster dates)")
    for e in expected["players"]:
        pooler = next(p for p in roster.poolers if p.id == e["pooler"])
        pts = games = 0
        for s in [s for s in pooler.players if norm(s.name) == norm(e["name"])]:
            for d, lines in lines_by_day.items():
                if not s.counts_on(d):
                    continue
                l = next((x for x in lines if x.player_id == s.player_id), None)
                if l:
                    games += 1
                    pts += l.goals * roster.goal_points + l.assists * roster.assist_points
        match = pts == e["points"] and games == e["games"]
        ok, diffs = ok + match, diffs + (not match)
        print(f"{'ok  ' if match else 'DIFF'}  {pooler.name:8} {e['name']:20} pts {e['points']:3} vs {pts:3}   games {e['games']:3} vs {games:3}")
    print(f"\n{ok} match, {diffs} differ.")
    return 0 if diffs == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
