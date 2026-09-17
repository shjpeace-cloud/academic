"""
Visit statistics for the site, from GoatCounter (shjpeace.goatcounter.com).

    python .claude/tools/site_stats.py              last 30 days
    python .claude/tools/site_stats.py --days 7
    python .claude/tools/site_stats.py --start 2026-09-17 --end 2026-10-17

Prints total visits, a daily series, top pages and top referrers.

The API token is read-only ("Read statistics") and lives in the Windows user
environment variable GOATCOUNTER_TOKEN, never in this repo. A session started
before the variable was set does not have it in its environment, so it is also
read from the registry.
"""

import argparse
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request

SITE = "https://shjpeace.goatcounter.com/api/v0"


def token() -> str:
    t = os.environ.get("GOATCOUNTER_TOKEN")
    if not t and sys.platform == "win32":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                t = winreg.QueryValueEx(k, "GOATCOUNTER_TOKEN")[0]
        except OSError:
            pass
    if not t:
        raise SystemExit("GOATCOUNTER_TOKEN is not set")
    return t


def get(path: str, **params) -> dict:
    url = f"{SITE}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token()}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--start", help="YYYY-MM-DD")
    ap.add_argument("--end", help="YYYY-MM-DD (inclusive)")
    ap.add_argument("--limit", type=int, default=15)
    a = ap.parse_args()

    today = dt.date.today()
    end = dt.date.fromisoformat(a.end) if a.end else today
    start = dt.date.fromisoformat(a.start) if a.start else end - dt.timedelta(days=a.days - 1)
    # The API's end date is exclusive.
    span = dict(start=start.isoformat(), end=(end + dt.timedelta(days=1)).isoformat())

    total = get("stats/total", **span)
    print(f"GoatCounter  {start} – {end}")
    print(f"  visits: {total['total']}")
    days = [d for d in total.get("stats", []) if d["daily"]]
    if days:
        print("  by day:")
        for d in days:
            print(f"    {d['day']}  {d['daily']:>5}")

    hits = get("stats/hits", limit=a.limit, **span)
    print("  top pages:")
    for h in hits.get("hits", []) or []:
        print(f"    {h['count']:>5}  {h['path']}")
    if not hits.get("hits"):
        print("    (none)")

    refs = get("stats/toprefs", limit=a.limit, **span)
    print("  top referrers:")
    for r in refs.get("stats", []) or []:
        print(f"    {r['count']:>5}  {r.get('name') or '(direct)'}")
    if not refs.get("stats"):
        print("    (none)")


if __name__ == "__main__":
    main()
