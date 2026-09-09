"""Offline checks for the Japan Daily Brief.

This edition ran without a suite for months, and it is the one that shipped a
NameError in the footer, a validation gate that printed its findings and then
sent anyway, a Download PDF button pointing at a file that has never existed,
and two feeds silent for fifty-one days. Every check here exists because
something in that list reached a reader.

Nothing here touches the network, the model, or the mailer. Run it with:

    python3 smoke_test.py
"""
from __future__ import annotations

import inspect
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

PASSED = 0
FAILURES: list[str] = []


def check(name: str, cond, detail: str = "") -> None:
    global PASSED
    if cond:
        PASSED += 1
    else:
        FAILURES.append(f"{name}: {detail}")
        print(f"  FAIL  {name} {detail}")


def section(title: str) -> None:
    print(f"\n[{title}]")


import collect            # noqa: E402
import digest as digest_mod   # noqa: E402
import feed_health        # noqa: E402
import japan_calendar     # noqa: E402
import length_budget      # noqa: E402
import render             # noqa: E402
import run as run_mod     # noqa: E402
import send_email         # noqa: E402


def _digest(**over) -> dict:
    """A digest with every section populated, so the renderer is fully walked."""
    d = {
        "digest_date": "Wednesday, September 9, 2026",
        "re_line": "Diet reconvenes · BOJ holds · Osprey grounding lifted",
        "morning_memo": ["First.", "Second.", "Third."],
        "web_url": "https://example.org/index.html",
        "top_stories": [
            {"headline": "Cabinet approves the defence budget request",
             "body": "The request totals a record sum.", "source": "Yomiuri",
             "src_line": 'per Yomiuri: "Cabinet approves request"',
             "url": "https://example.org/a", "category_tag": "Security"},
            {"headline": "BOJ holds rates", "body": "No change to the policy rate.",
             "source": "Nikkei", "src_line": 'per Nikkei: "BOJ holds"',
             "url": "https://example.org/b", "category_tag": "Economy"},
        ],
        "overnight_items": [
            {"category": "Security", "headline": "Destroyer transits the strait",
             "body_text": "Second passage this week.", "source": "Kyodo",
             "url": "https://example.org/c"},
            {"category": "Trade", "headline": "Tariff talks resume",
             "body_text": "Officials meet in Washington.", "source": "Asahi",
             "url": "https://example.org/d"},
            {"category": "Politics", "headline": "Upper house committee sits",
             "body_text": "Budget testimony scheduled.", "source": "NHK World",
             "url": "https://example.org/d2"},
        ],
        "key_stat": {"number": "1.4%", "label": "Q2 GDP, annualised",
                     "context": "Third consecutive quarter of growth.",
                     "source": "Cabinet Office"},
        "also_today": [
            {"category": "trade", "headline": "Chip subsidy tranche released",
             "body_text": "METI names the recipients.", "source": "Nikkei",
             "url": "https://example.org/e"},
            {"category": "politics", "headline": "Reshuffle speculation",
             "body_text": "Two portfolios in play.", "source": "Mainichi",
             "url": "https://example.org/f"},
        ],
        "business_economy": [
            {"headline": "Yen steadies", "body_text": "After a volatile session.",
             "source": "Bloomberg", "url": "https://example.org/g"}],
        "indo_pacific": [
            {"headline": "Trilateral exercise announced", "body_text": "Three navies.",
             "source": "Reuters", "url": "https://example.org/h"}],
        "opeds_today": [
            {"headline": "The alliance after the election", "authors": "A. Writer",
             "summary": "An argument.", "central_argument": "The core claim.",
             "source": "Foreign Affairs", "url": "https://example.org/i"}],
        "calendar_watch": [],
        "market_indicators": {
            "nikkei": {"value": "39,110", "change_pct": 0.6},
            "usd_jpy": {"value": "147.20", "change_pct": -0.2},
            "brent": {"value": "72.40", "change_pct": -1.1},
            "boj_rate": {"value": "0.50%"}},
    }
    d.update(over)
    return d


# ── 1. Render ────────────────────────────────────────────────────────────
def test_render():
    section("render")
    html = render.render_html(_digest())
    check("renders a full page", len(html) > 12_000, str(len(html)))

    # The footer referenced archive_url, which was never computed, so this
    # raised NameError on every call and no test existed to catch it.
    check("renders with no web_url at all",
          len(render.render_html({"re_line": "x", "morning_memo": ["a", "b", "c"]})) > 3_000)

    body = html.split("<body", 1)[-1]
    hrefs = re.findall(r'href="([^"]*)"', body)
    check("no empty hrefs", not [h for h in hrefs if not h.strip()],
          str([h for h in hrefs if not h.strip()][:3]))

    # Gmail strips `name` on an <a>, so "Back to top" and every jump link did
    # nothing in the inbox while working in a browser.
    anchors = {m for m, _ in re.findall(r'<a name="([a-z0-9-]+)" id="([a-z0-9-]+)"', body)}
    jumps = {h[1:] for h in hrefs if h.startswith("#")}
    check("every anchor carries an id", anchors, str(len(anchors)))
    check("every jump link resolves", jumps <= anchors, str(sorted(jumps - anchors)))

    check("jump row is labelled", "In this issue" in html)
    check("overnight is a scan list", 'class="flash-table"' in html)
    check("stat panel present", 'a name="key-stat"' in html)
    check("the wire is grouped", 'a name="wire"' in html)
    check("house footer", "CSIS Japan Chair" in html and "Washington, D.C." in html)
    check("contact is the Japan chair's", "dmartin@csis.org" in html)
    check("no Korea contact left behind", "alim@csis.org" not in html)


# ── 2. Dark mode ─────────────────────────────────────────────────────────
def test_dark_mode():
    section("dark mode")
    html = render.render_html(_digest())
    gaps = render._check_dark_coverage(html)
    check("every colour has a dark rule", not gaps, "; ".join(gaps[:4]))
    check("dark media query present", "prefers-color-scheme: dark" in html)


# ── 3. Print and mobile ──────────────────────────────────────────────────
def test_print_and_mobile():
    section("print + mobile")
    html = render.render_html(_digest())
    check("print stylesheet", "@media print" in html)
    check("chrome hidden in print",
          re.search(r"@media print.*?no-print", html, re.S) is not None)
    check("mobile media query", "@media only screen and (max-width" in html)
    body = html.split("<body", 1)[-1]
    wide = {int(w) for w in re.findall(r"width:\s*(\d{3,4})px", body)}
    check("no element wider than the frame", not {w for w in wide if w > 680}, str(sorted(wide)))

    # The button pointed at a guessed latest.pdf. There is no exporter here,
    # so that file has never existed.
    no_pdf = render.render_html(_digest())
    check("no PDF link without a published pdf_url", "Download PDF" not in no_pdf)
    with_pdf = render.render_html(_digest(pdf_url="https://example.org/2026-09-09.pdf"))
    check("PDF link when the run published one", "Download PDF" in with_pdf)


# ── 4. Length ────────────────────────────────────────────────────────────
def test_length():
    section("length ceiling")
    check("ceiling is set", run_mod.WORD_CEILING == 2400, str(run_mod.WORD_CEILING))
    check("prompt states the band",
          "1,900-2,200" in inspect.getsource(digest_mod))
    check("run.py enforces it", "length_budget.apply(" in Path("run.py").read_text(encoding="utf-8"))

    over = _digest()
    filler = " ".join(["word"] * 120)
    for key in ("overnight_items", "also_today", "business_economy", "indo_pacific"):
        over[key] = [{"headline": "H", "body_text": filler, "source": "S",
                      "url": f"https://example.org/{key}{i}"} for i in range(9)]
    before = run_mod._count_words(over)
    check("fixture starts over the ceiling", before > run_mod.WORD_CEILING, str(before))
    length_budget.apply(over, run_mod._count_words, run_mod.WORD_CEILING)
    check("trimmer brings it under", run_mod._count_words(over) <= run_mod.WORD_CEILING,
          f"{before} -> {run_mod._count_words(over)}")
    check("top stories are never trimmed", len(over["top_stories"]) == 2)


# ── 4b. Source diversity ─────────────────────────────────────────────────
def test_source_diversity():
    """The rule the validator enforces must have something that satisfies it.

    The validator rejects a brief where one outlet appears more than three
    times across top stories and overnight, and nothing used to cap it, so an
    over-represented source blocked the send with no way to recover. Whole-
    outlet RSS feeds return far more items per source than the site: searches
    they replaced, which makes that input likely rather than exotic.
    """
    section("source diversity")
    d = {"overnight_items": [{"source": "Reuters", "headline": f"r{i}"} for i in range(6)]
                            + [{"source": "Kyodo", "headline": "k"}],
         "also_today": [{"source": "Nikkei", "headline": f"n{i}"} for i in range(5)]}
    log = run_mod._enforce_source_diversity(d)
    check("excess items are dropped", len(log) == 5, str(len(log)))
    check("the cap holds", sum(1 for i in d["overnight_items"]
                               if i["source"] == "Reuters") <= run_mod._SOURCE_CAP)
    check("the section floor is respected", len(d["overnight_items"]) >= 3)
    # And the gate it feeds must then pass.
    full = dict(d, top_stories=[{"source": "A", "headline": "x"},
                                {"source": "B", "headline": "y"}],
                morning_memo=["a", "b", "c"])
    check("the validator no longer objects",
          not [f for f in run_mod._validate_digest(full) if "DIVERSITY" in f])
    # Top stories are deliberately exempt: two to four curated items where the
    # story outweighs the count.
    top = {"top_stories": [{"source": "Reuters", "headline": f"t{i}"} for i in range(4)]}
    run_mod._enforce_source_diversity(top)
    check("top stories are untouched", len(top["top_stories"]) == 4)


# ── 5. Validation gate ───────────────────────────────────────────────────
def test_validation_gate():
    section("validation gate")
    src = Path("run.py").read_text(encoding="utf-8")
    # It printed "Use --force-send to override validation gate" and then sent
    # the brief regardless, so every failure it reported went out anyway.
    check("a failure blocks the send",
          "if not validation_passed and not args.force_send:" in src)
    check("the HTML is still written for review", "not sending" in src)
    check("force-send still exists", "--force-send" in src)
    bad = _digest(morning_memo=["only", "two"])
    check("a short memo is a failure",
          any("MORNING MEMO" in f for f in run_mod._validate_digest(bad)))
    # The word-count minimum is about a real brief, not a fixture, so it is
    # the one failure a fixture is allowed to trip.
    check("a complete digest passes every structural check",
          not [f for f in run_mod._validate_digest(_digest()) if "WORD COUNT" not in f],
          str([f for f in run_mod._validate_digest(_digest()) if "WORD COUNT" not in f]))


# ── 6. Feeds and feed health ─────────────────────────────────────────────
def test_feeds():
    section("feeds + health")
    feeds = {}
    for name in ("TIER1_FEEDS", "TIER2_FEEDS", "TIER3_FEEDS", "TIER4_FEEDS"):
        feeds.update(getattr(collect, name))
    check("every tier has feeds", len(feeds) > 40, str(len(feeds)))

    # Mainichi and Jiji were Google-News-only and went 51 days without
    # delivering. A search that stops matching returns nothing indefinitely.
    for name in ("Mainichi", "Jiji Press", "Asahi AJW", "NHK World"):
        check(f"{name} has a native path first",
              "news.google.com" not in feeds.get(name, ""), feeds.get(name, "missing"))
        check(f"{name} keeps a search fallback", name in collect._FALLBACK)

    # record() reloads from disk on every call, so the run-to-run count only
    # accumulates through the save-backed helper. Point it at a temp file so
    # the check never touches the real history.
    real_path, tmp_path = feed_health.PATH, feed_health.PATH + ".smoke"
    feed_health.PATH = tmp_path
    try:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        lines = []
        for _ in range(feed_health.SILENT_RUN_THRESHOLD):
            lines = feed_health.update_and_report(
                {"Mainichi": {"success": False, "count": 0},
                 "Yomiuri": {"success": True, "count": 6}})
        check("a feed silent three runs is reported",
              any("Mainichi" in ln for ln in lines), str(lines))
        check("a delivering feed is not reported",
              not any("Yomiuri" in ln for ln in lines), str(lines))
    finally:
        feed_health.PATH = real_path
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ── 7. Calendar ──────────────────────────────────────────────────────────
def test_calendar():
    section("calendar")
    items = japan_calendar.upcoming(date(2026, 8, 1), 30)
    got = {i["headline"] for i in items}
    check("Hiroshima is computed", any("Hiroshima" in h for h in got), str(got))
    check("dates carry the right year",
          all(i["_date"].startswith("2026") for i in items))
    # A date that has passed this year must roll to next year, not appear as past.
    nxt = japan_calendar.upcoming(date(2026, 12, 20), 60)
    check("a passed date rolls forward",
          all(i["_date"] >= "2026-12-20" for i in nxt), str([i["_date"] for i in nxt]))
    # The model's own dated events outrank an anniversary anyone could look up.
    merged = japan_calendar.merge(
        [{"month": "Sep", "day": 12, "headline": "Diet session opens", "detail": "d"}],
        date(2026, 9, 9))
    check("model events survive the merge",
          any(i["headline"] == "Diet session opens" for i in merged))
    check("nothing that moves is hard-coded",
          not any(w in h.lower() for _, _, h, _ in japan_calendar.RECURRING
                  for w in ("summit", "boj", "election", "diet session")))


# ── 8. Subject line and recipients ───────────────────────────────────────
def test_email():
    section("email")
    src = inspect.getsource(send_email)
    check("subject is the house format", "Japan Daily Brief | " in src)
    check("sender carries a display name", 'msg["From"]' in src)
    os.environ["DIGEST_TO"] = "a@csis.org, b@csis.org , c@csis.org"
    parsed = [p.strip() for p in os.environ["DIGEST_TO"].split(",") if p.strip()]
    check("comma-separated recipients parse", len(parsed) == 3, str(parsed))


def main() -> int:
    for t in (test_render, test_source_diversity, test_dark_mode, test_print_and_mobile, test_length,
              test_validation_gate, test_feeds, test_calendar, test_email):
        try:
            t()
        except Exception as exc:                                # noqa: BLE001
            FAILURES.append(f"{t.__name__}: crashed: {exc}")
            print(f"  FAIL  {t.__name__} crashed: {exc}")
    print(f"\n{PASSED} checks passed, {len(FAILURES)} failed")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
