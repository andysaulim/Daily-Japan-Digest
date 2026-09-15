"""Check which candidate RSS feeds actually deliver, before trusting one.

Almost every source in this brief is a Google News search rather than the
outlet's own RSS, which makes one service a single point of failure — and on
14 September it failed exactly that way: Tier 2 (29 of 30 on Google News) and
Tier 3 (18 of 18) both returned zero while Tier 1, which has real publisher
feeds behind half its sources, came back fine. The whole Expert Analysis and
Events section vanished.

Moving a source to its native feed is the fix, but a guessed feed URL is how
Korea Herald went silent for weeks: it 404s, nothing notices, and the source
quietly stops contributing. This script is the check. It fetches each
candidate, reports how many entries came back and how recent they are, so a
URL is adopted because it was measured rather than because it looked right.

    python3 probe_feeds.py                 # probe the built-in candidate list
    python3 probe_feeds.py URL [URL ...]   # probe specific URLs

Needs real network access. It will report nothing useful from a sandbox whose
proxy denies the publisher hosts.
"""
from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

import feedparser
import requests

TIMEOUT = 12
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JapanDailyBrief/1.0)"}

# Candidates worth testing, grouped by the tier they would serve. Nothing here
# is adopted until it has been probed — that is the entire point of the file.
CANDIDATES: dict[str, list[tuple[str, str]]] = {
    "tier2 — think tanks": [
        ("Brookings",         "https://www.brookings.edu/feed/"),
        ("Foreign Policy",    "https://foreignpolicy.com/feed/"),
        ("Atlantic Council",  "https://www.atlanticcouncil.org/feed/"),
        ("War on the Rocks",  "https://warontherocks.com/feed/"),
        ("Stimson",           "https://www.stimson.org/feed/"),
        ("Hudson",            "https://www.hudson.org/rss.xml"),
        ("CFR",               "https://www.cfr.org/rss.xml"),
        ("CSIS analysis",     "https://www.csis.org/analysis/feed"),
        ("CSIS rss",          "https://www.csis.org/rss.xml"),
        ("Carnegie",          "https://carnegieendowment.org/rss.xml"),
        ("Lowy Interpreter",  "https://www.lowyinstitute.org/the-interpreter/rss.xml"),
        ("Foreign Affairs",   "https://www.foreignaffairs.com/rss.xml"),
        ("Pacific Forum",     "https://pacforum.org/feed"),
        ("NBR",               "https://www.nbr.org/feed/"),
    ],
    "events": [
        ("CSIS events",       "https://www.csis.org/events/feed"),
        ("CSIS events rss",   "https://www.csis.org/events/rss.xml"),
        ("Brookings events",  "https://www.brookings.edu/events/feed/"),
        ("Hudson events",     "https://www.hudson.org/events/rss.xml"),
    ],
    # Tier 3 journals sit on Cambridge Core, Oxford Academic and Taylor &
    # Francis, whose feed URLs carry per-journal numeric ids. Those ids are not
    # guessable and are deliberately absent: add them here once looked up on
    # the publisher's own site, then probe.
    "tier3 — journals": [],
}


def probe(name: str, url: str) -> str:
    try:
        resp = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
    except Exception as exc:
        return f"  ✖  {name:20} {type(exc).__name__}: {str(exc)[:60]}"
    if resp.status_code != 200:
        return f"  ✖  {name:20} HTTP {resp.status_code}"
    entries = feedparser.parse(resp.content).entries
    if not entries:
        # A 200 with no items is what Google News returns when it throttles,
        # and what a moved feed path often returns too. It is a failure.
        return f"  ✖  {name:20} HTTP 200 but zero entries"
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    fresh = 0
    for e in entries:
        parsed = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
        if parsed and datetime(*parsed[:6], tzinfo=timezone.utc) >= cutoff:
            fresh += 1
    return f"  ✔  {name:20} {len(entries):3} entries, {fresh} in the last 7 days"


def main(argv: list[str]) -> int:
    if argv:
        groups = {"given on the command line": [(u, u) for u in argv]}
    else:
        groups = {k: v for k, v in CANDIDATES.items() if v}

    for group, feeds in groups.items():
        print(f"\n{group}")
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(probe, n, u): n for n, u in feeds}
            for f in sorted(as_completed(futures), key=lambda _: 0):
                print(f.result())
    print("\nAdopt only the ✔ lines, via _direct(name, url, gnews_query) so the "
          "search stays as fallback.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
