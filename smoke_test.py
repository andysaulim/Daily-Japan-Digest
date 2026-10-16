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
import time as _time      # noqa: E402
import digest as digest_mod   # noqa: E402
import feed_health        # noqa: E402
import japan_calendar     # noqa: E402
import length_budget      # noqa: E402
import render             # noqa: E402
import run as run_mod     # noqa: E402
import send_email         # noqa: E402


def _today_et() -> str:
    """Today in ET, formatted the way the pipeline writes digest_date."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo("America/New_York")).strftime("%A, %B %-d, %Y")


def _digest(**over) -> dict:
    """A digest with every section populated, so the renderer is fully walked."""
    d = {
        # Computed, never hardcoded: run.py's validator compares this against
        # today in ET, so a literal date passes on the day it is written and
        # fails every day after. This gate has no continue-on-error and sits
        # ahead of the pipeline, so a stale fixture date would have blocked
        # every send from 10 September onward.
        "digest_date": _today_et(),
        "re_line": "Diet reconvenes · BOJ holds · Osprey grounding lifted",
        "web_url": "https://example.org/index.html",
        "top_stories": [
            {"headline": "Cabinet approves the defence budget request",
             "body": "The request totals a record sum.", "source": "Yomiuri",
             "src_line": 'per Yomiuri: "Cabinet approves request"',
             "url": "https://example.org/a", "category_tag": "Security"},
            {"headline": "BOJ holds rates", "body": "No change to the policy rate.",
             "source": "Nikkei", "src_line": 'per Nikkei: "BOJ holds"',
             "url": "https://example.org/b", "category_tag": "Economy"},
            {"headline": "Destroyer transits the strait",
             "body": "Second passage this week.", "source": "Kyodo",
             "src_line": 'per Kyodo: "Destroyer transits"',
             "url": "https://example.org/c", "category_tag": "Defense"},
            {"headline": "Tariff talks resume",
             "body": "Officials meet in Washington.", "source": "Asahi",
             "src_line": 'per Asahi: "Tariff talks resume"',
             "url": "https://example.org/d", "category_tag": "Alliance"},
            {"headline": "Upper house committee sits",
             "body": "Budget testimony scheduled.", "source": "NHK World",
             "src_line": 'per NHK World: "Committee sits"',
             "url": "https://example.org/d2", "category_tag": "Politics-Diet"},
        ],
        "key_stat": {"number": "1.4%", "label": "Q2 GDP, annualised",
                     "context": "Third consecutive quarter of growth.",
                     "source": "Cabinet Office"},
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
        # The docstring above claimed every section was populated and this
        # fixture carried nine keys, so the blocking gate never walked the
        # government cards, the PM Watch line, the pressure panel, the poll
        # table, quoted statements or either new section. It does now.
        "us_japan_relations": [
            {"headline": "Host-nation support talks open", "body_text": "First round.",
             "track": "Alliance", "source": "Kyodo", "url": "https://example.org/j"}],
        "events_today": [
            {"title": "The next host-nation support agreement", "host": "CSIS",
             "event_date": "Sep 18, 2026", "format": "Hybrid",
             "summary": "A panel.", "url": "https://example.org/k"}],
        "academic_today": [
            {"title": "Basing access and credibility", "journal_tier": "A+",
             "authors": "Nakamura", "summary": "A study.",
             "source": "International Security", "url": "https://example.org/l"}],
        "prc_government": [
            {"ministry": "Ministry of Foreign Affairs", "ministry_jp": "外務省",
             "official": "Kihara Seiji, Foreign Minister",
             "action": "MOFA lodges a protest", "detail": "Over a survey vessel.",
             "source_label": "Kyodo", "url": "https://example.org/m"}],
        "npc_politburo": [
            {"body": "Budget Committee", "action": "Sets the supplementary timetable",
             "detail": "A floor vote follows.", "url": "https://example.org/n"}],
        "personnel_changes": [
            {"position": "Ambassador to Australia", "name": "Hayashi Motoko",
             "action": "appointed", "detail": "The post was vacant since July.",
             "predecessor": "Suzuki Takeshi"}],
        "social_statements": [
            {"avatar_initials": "KS", "who": "Kimura Shunsuke",
             "handle_context": "Chief Cabinet Secretary",
             "platform_date": "Kyodo · Sep 9",
             "quote_text": "We have conveyed our position through diplomatic channels.",
             "analyst_note": "The figure is new.", "badge_class": "sb-p",
             "url": "https://example.org/o"}],
        "public_sentiment": {
            "approval_polls": [{"pollster": "NHK", "cabinet_approval": "48%",
                                "cabinet_disapproval": "34%", "poll_date": "Sep 5-7",
                                "days_old": 4}],
            "party_support": [{"party": "LDP", "support_pct": "34%"}],
            "discourse_flag": "Coalition strain over the supplementary budget."},
        "xinhua_delta": {
            "pm_appearance_today": True,
            "pm_days_since_last_appearance": 0,
            "pm_activity": "Chaired the disaster-response meeting.",
            "china_signal": "A visa-fee increase was confirmed.",
            "dprk_signal": None, "russia_signal": None,
            "senkaku_status": "Two vessels remain in the contiguous zone.",
            "key_quotes": [], "output_volume": "Normal — 14 items",
            "silence_today": False, "watch_flag": False,
            "bottom_line": "Economic-pressure measures are accumulating."},
        "on_this_day": [
            {"date": "September 8, 1951", "event": "The peace treaty was signed.",
             "relevance": "The security treaty followed the same day."}],
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
          len(render.render_html({"re_line": "x", "top_stories": [
              {"headline": "H", "body": "B", "source": "S",
               "url": "https://example.org/x"}]})) > 3_000)

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
    check("stat panel present", 'a name="key-stat"' in html)
    check("house footer", "CSIS Japan Chair" in html and "Washington, D.C." in html)
    check("contact is the Japan chair's", "dmartin@csis.org" in html)
    check("no Korea contact left behind", "alim@csis.org" not in html)


# ── 1b. Headlines come from the source ───────────────────────────────────
def test_source_headlines():
    """The 25 September inversion, pinned.

    The brief ran "Trump hails China as WWII ally, calls for Taiwan
    independence opposition at summit close". Xi called for that. The Japan
    Times headline it was built from said so, and the brief printed it in grey
    italics directly underneath — the model had reordered the clauses and
    dropped Xi as the subject of the second. Top Stories now shows the feed's
    title, so this shape cannot recur.
    """
    section("source headlines")

    _real = {"top_stories": [{
        "headline": "Trump hails China as WWII ally, calls for Taiwan "
                    "independence opposition at summit close",
        "orig_title": "Xi calls for U.S. to \u2018oppose\u2019 Taiwan independence "
                      "as Trump hails China as WWII ally",
        "body": "Trump concluded his Washington summit with Xi Jinping.",
        "source": "The Japan Times", "link_source": "The Japan Times",
        "url": "https://example.org/jt-1", "category_tag": "China-Japan"}]}
    html = render.render_html(dict(_real, re_line="x"))
    check("the headline is the source's wording",
          "Xi calls for U.S. to" in html)
    check("the model's inverted wording is nowhere in the brief",
          "Trump hails China as WWII ally, calls for" not in html)

    # Fallback: an item that never matched a collected article still renders.
    _nomatch = {"re_line": "x", "top_stories": [{
        "headline": "Cabinet approves the budget request",
        "body": "A record sum.", "source": "Yomiuri",
        "url": "https://example.org/y-1", "category_tag": "Politics"}]}
    _fb = render.render_html(_nomatch)
    check("no orig_title falls back to the model's headline",
          "Cabinet approves the budget request" in _fb)
    check("the fallback leaves no empty headline", "<h3" in _fb)

    # Publisher suffix: strip only on a match, never on a real dash clause.
    _strip = render._strip_publisher_suffix
    check("a matching publisher suffix is stripped",
          _strip("North Korea fires ballistic missile into waters outside "
                 "Japan EEZ - The Japan Times", "Japan Times")
          == "North Korea fires ballistic missile into waters outside Japan EEZ")
    check("the leading article does not defeat the match",
          _strip("Russia lodges protest with Japan - The Washington Post",
                 "Washington Post") == "Russia lodges protest with Japan")
    check("a dot-com suffix still matches",
          _strip("Japan 10-Year Yield Climbs - Bloomberg.com", "Bloomberg")
          == "Japan 10-Year Yield Climbs")
    check("a real dash clause survives",
          _strip("Takaichi wins - and now must govern", "Reuters")
          == "Takaichi wins - and now must govern")
    check("a suffix that is not the publisher survives",
          _strip("Some story - Kyodo News", "The Japan Times")
          == "Some story - Kyodo News")


# ── 1c. Forthcoming events are not reported as done ───────────────────────
def test_tense_risk():
    """The 22 September failure: a noon meeting written up at 7 AM as held.

    The cause was missing information — the prompt carried the date and never
    the clock — so the fix is in digest.py. This checks the prompt now says so,
    and that the run-log backstop catches the real shape.
    """
    section("forthcoming vs completed")
    dsrc = inspect.getsource(digest_mod)
    check("the prompt states the current time", "Current time:" in dsrc)
    check("the prompt carries the forthcoming rule", "TIME OF DAY" in dsrc)
    check("the generation clock is computed",
          'strftime("%-I:%M %p ET")' in dsrc)

    _flag = run_mod._flag_tense_risk
    _real = {"top_stories": [{
        "orig_title": "Japan Meets With Trump, Hoping to Get His Help on China",
        "body": "Takaichi held talks with Trump in New York on Tuesday."}]}
    check("the real 22 September shape is flagged", bool(_flag(_real)))
    # Intent in a gerund, with no scheduling word anywhere — the form that
    # slipped past the first version of this check.
    check("intent language counts, not just scheduling language",
          bool(_flag({"top_stories": [{
              "orig_title": "Japan seeking US assurances ahead of summit",
              "body": "Tokyo announced it had reached a deal on Friday."}]})))
    check("a genuinely completed story is not flagged",
          not _flag({"top_stories": [{
              "orig_title": "Xi calls for U.S. to oppose Taiwan independence",
              "body": "Trump concluded his summit with Xi on Friday."}]}))
    check("a forthcoming story written as forthcoming is not flagged",
          not _flag({"top_stories": [{
              "orig_title": "Takaichi is set to meet Trump on Tuesday",
              "body": "The two are due to meet later today."}]}))
    check("the check is a warning, not a gate",
          not [f for f in run_mod._validate_digest(_digest())
               if "TENSE" in f])


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
    check("ceiling is set", run_mod.WORD_CEILING == 1900, str(run_mod.WORD_CEILING))
    check("prompt states the band",
          "1,400-1,700" in inspect.getsource(digest_mod))
    check("run.py enforces it", "length_budget.apply(" in Path("run.py").read_text(encoding="utf-8"))

    over = _digest()
    filler = " ".join(["word"] * 120)
    # Overnight and The Wire were the two biggest pools this used to inflate.
    # What remains has to carry the whole overshoot on its own.
    for key in ("business_economy", "indo_pacific", "opeds_today",
                "us_japan_relations"):
        over[key] = [{"headline": "H", "body_text": filler, "source": "S",
                      "url": f"https://example.org/{key}{i}"} for i in range(9)]
    before = run_mod._count_words(over)
    check("fixture starts over the ceiling", before > run_mod.WORD_CEILING, str(before))
    length_budget.apply(over, run_mod._count_words, run_mod.WORD_CEILING)
    check("trimmer brings it under", run_mod._count_words(over) <= run_mod.WORD_CEILING,
          f"{before} -> {run_mod._count_words(over)}")
    check("top stories are never trimmed", len(over["top_stories"]) == 5)


# ── 4b. Source diversity ─────────────────────────────────────────────────
def test_source_diversity():
    """The rule the validator enforces must have something that satisfies it.

    The validator rejects a brief where one outlet appears more than three
    times in Top Stories, and nothing used to cap it, so an over-represented
    source blocked the send with no way to recover. Whole-outlet RSS feeds
    return far more items per source than the site: searches they replaced,
    which makes that input likely rather than exotic.

    Top Stories is the whole scope now. It used to be exempt, with Overnight
    giving up the excess instead; removing Overnight and The Wire took that
    release valve away, so this section has to give items up itself.
    """
    section("source diversity")
    d = {"top_stories": [{"source": "Reuters", "headline": f"r{i}",
                          "url": f"https://example.org/r{i}"} for i in range(6)]
                        + [{"source": "Kyodo", "headline": "k",
                            "url": "https://example.org/k"}]}
    log = run_mod._enforce_source_diversity(d)
    check("excess items are dropped", len(log) == 3, str(len(log)))
    check("the cap holds", sum(1 for i in d["top_stories"]
                               if i["source"] == "Reuters") <= run_mod._SOURCE_CAP)
    check("the section floor is respected",
          len(d["top_stories"]) >= run_mod._TOP_STORIES_FLOOR,
          str(len(d["top_stories"])))
    # And the gate it feeds must then pass.
    check("the validator no longer objects",
          not [f for f in run_mod._validate_digest(d) if "DIVERSITY" in f])

    # The floor outranks the cap. Trimming must never hand the gate a count
    # failure in place of a breadth one, so the floor is the same number as
    # the validator's minimum and the dropped item comes back.
    floored = {"top_stories": [{"source": "Reuters", "headline": f"t{i}",
                                "url": f"https://example.org/t{i}"} for i in range(4)]}
    run_mod._enforce_source_diversity(floored)
    check("the floor is never breached to satisfy the cap",
          len(floored["top_stories"]) == run_mod._TOP_STORIES_FLOOR,
          str(len(floored["top_stories"])))
    check("the floor matches the validator's minimum, so trimming never "
          "swaps one failure for another",
          not [f for f in run_mod._validate_digest(floored)
               if f.startswith("TOP STORIES")])
    # And what survives is a real editorial problem, reported rather than hidden.
    check("a brief entirely from one outlet still blocks",
          [f for f in run_mod._validate_digest(floored)
           if f.startswith("SOURCE DIVERSITY")])


def test_cross_day():
    """Repeats from a recent edition must not starve Top Stories.

    On 4 October the model wrote six Top Stories, the cross-day ledger then
    removed three as already published, and the gate held the brief through
    four runs. Two changes: repeats are withheld from the model's input, and
    the post-hoc sweep never takes Top Stories below the validator's floor.
    """
    section("cross-day repeats")
    stories = [{"source": f"S{i}", "headline": f"story {i}",
                "url": f"https://example.org/s{i}"} for i in range(6)]
    prev_urls = {f"https://example.org/s{i}" for i in (0, 2, 3, 5)}
    d = run_mod._dedupe_cross_day({"top_stories": [dict(x) for x in stories]},
                                  prev_urls, set())
    kept = [x["url"] for x in d["top_stories"]]
    check("repeats never take Top Stories below the floor",
          len(kept) == run_mod._TOP_STORIES_FLOOR, str(kept))
    check("the earliest repeats come back, in the model's order",
          kept == [f"https://example.org/s{i}" for i in (0, 1, 2, 4)], str(kept))
    check("the gate then passes on count",
          not [f for f in run_mod._validate_digest(d) if f.startswith("TOP STORIES")])
    d = run_mod._dedupe_cross_day(
        {"top_stories": [dict(x) for x in stories],
         "business_economy": [{"headline": "b", "url": "https://example.org/s0"}]},
        {"https://example.org/s0"}, set())
    check("above the floor a repeat is still removed",
          len(d["top_stories"]) == 5, str(len(d["top_stories"])))
    check("the floor applies to Top Stories only", d["business_economy"] == [])

    payload = {"tier1": [{"title": "Fresh story", "url": "https://example.org/new"},
                         {"title": "Old story", "url": "https://example.org/old"},
                         {"title": "Ran Yesterday - Kyodo",
                          "url": "https://news.google.com/rss/articles/x"}],
               "tier4": [{"title": "Old story", "url": "https://example.org/old"}]}
    entries = [{"date": "2026-10-03", "url": "https://example.org/old", "title": "x"},
               {"date": "2026-10-03", "url": "https://kyodo.example/y",
                "title": "model headline", "orig": "ran yesterday kyodo"}]
    urls, titles = run_mod._ledger_recent_keys(entries, date(2026, 10, 4))
    n = run_mod._filter_published_inputs(payload, urls, titles)
    check("already-published articles are withheld from the model",
          [a["title"] for a in payload["tier1"]] == ["Fresh story"],
          str(payload["tier1"]))
    check("a decoded Google News repeat is caught by its feed title", n == 2, str(n))
    check("Tier 4 signal baseline is left whole", len(payload["tier4"]) == 1)


# ── 5. Validation gate ───────────────────────────────────────────────────
def test_validation_gate():
    section("validation gate")
    src = Path("run.py").read_text(encoding="utf-8")
    # It printed "Use --force-send to override validation gate" and then sent
    # the brief regardless, so every failure it reported went out anyway.
    check("a failure blocks the send",
          "if not validation_passed and not args.force_send:" in src)
    check("the HTML is still written for review", "not sending" in src)

    # 15 September: 'The Japan Times' appeared 4 times across top + overnight,
    # the gate blocked the send, and nothing could clear it — the enforcer
    # counted per section and skipped top_stories, while the validator counted
    # the two together. Overnight is gone; the same shape now lands entirely
    # in Top Stories, and the enforcer has to clear it there.
    import run as _run

    def _src_failures(d):
        return [f for f in _run._validate_digest(d) if f.startswith("SOURCE DIVERSITY")]

    def _item(source, n):
        return {"source": source, "headline": f"{source} story {n}",
                "url": f"https://example.org/{source.replace(' ', '')}-{n}"}

    _over = {"top_stories": [_item("The Japan Times", 1), _item("The Japan Times", 2),
                             _item("The Japan Times", 3), _item("The Japan Times", 4),
                             _item("Nikkei", 5)]}
    _run._enforce_source_diversity(_over)
    _remaining = sum(1 for i in _over["top_stories"]
                     if i.get("source") == "The Japan Times")
    check("an over-represented outlet is capped to 3", _remaining <= 3,
          f"{_remaining} remain")
    check("and the gate then passes on it", not _src_failures(_over),
          "; ".join(_src_failures(_over)))
    check("the brief keeps enough stories to send",
          len(_over["top_stories"]) >= _run._TOP_STORIES_FLOOR,
          str(len(_over["top_stories"])))

    # The gate is the guarantee, the enforcer only the mechanism. A digest
    # that reaches validation without having been through the enforcer is
    # still checked rather than trusted.
    _unenforced = {"top_stories": [_item("The Japan Times", i) for i in range(1, 5)]}
    check("the gate still catches an unenforced digest",
          bool(_src_failures(_unenforced)), "; ".join(_src_failures(_unenforced)))

    # The sections themselves are gone; nothing should re-introduce them.
    _removed = ("morning_memo", "overnight_items", "also_today")
    _gates = _run._validate_digest(_digest())
    check("no gate demands a removed section",
          not [f for f in _gates
               if any(k.split("_")[0].upper() in f for k in _removed)],
          "; ".join(_gates))
    check("digest.py has no minimum for a removed section",
          not [k for k in _removed
               if k in inspect.getsource(digest_mod._check_content_minimums)])

    # 14 September: the brief shipped a Japan Times news commentary under
    # "Op-Eds & Think Tank Commentary" on a run whose collector reported
    # "Tier 2: 0 articles from 0 sources". The prompt forbids it and the
    # prompt was not enough, so the boundary is checked after the fact now.
    _tiered = _run._enforce_source_tiers(
        {"opeds_today": [{"title": "From the news pool",
                          "url": "https://example.org/tier1-only"},
                         {"title": "Genuinely Tier 2",
                          "url": "https://example.org/in-tier2"}],
         "academic_today": [{"title": "Not in tier 3",
                             "url": "https://example.org/nope"}]},
        {"tier2": [{"url": "https://example.org/in-tier2"}],
         "tier3": [],
         "events": []})
    _kept = [i["url"] for i in _tiered["opeds_today"]]
    check("an op-ed absent from tier 2 is dropped",
          "https://example.org/tier1-only" not in _kept, str(_kept))
    check("an op-ed present in tier 2 survives",
          "https://example.org/in-tier2" in _kept, str(_kept))
    check("an empty tier empties its section",
          _tiered["academic_today"] == [], str(_tiered["academic_today"]))

    # A tier missing from the payload is unknown, not empty: an older cached
    # collected.json predates the events key, and must not blank the section.
    _unknown = _run._enforce_source_tiers(
        {"events_today": [{"title": "Kept", "url": "https://example.org/e"}]}, {})
    check("a tier absent from the payload is left alone",
          len(_unknown["events_today"]) == 1, str(_unknown["events_today"]))
    check("force-send still exists", "--force-send" in src)
    bad = _digest(top_stories=[{"headline": "only one", "body": "b",
                                "source": "S", "url": "https://example.org/z"}])
    check("too few top stories is a failure",
          any("TOP STORIES" in f for f in run_mod._validate_digest(bad)))
    # 4 October: the gate demanded four stories, a quiet day produced three,
    # and the brief was held through four runs and went out seven hours late.
    # The 4-6 band is the editorial target; the gate is the floor below which
    # a brief is not worth sending, and they are not the same number.
    _three = _digest(top_stories=[
        {"headline": f"story {i}", "body": "b", "source": f"S{i}",
         "url": f"https://example.org/t{i}"} for i in range(3)])
    check("three top stories still send",
          not [f for f in run_mod._validate_digest(_three)
               if f.startswith("TOP STORIES")],
          "; ".join(f for f in run_mod._validate_digest(_three)
                    if f.startswith("TOP STORIES")))
    check("the pipeline still protects four when it has them",
          run_mod._TOP_STORIES_FLOOR >= 4, str(run_mod._TOP_STORIES_FLOOR))
    check("the floor never drops below what the gate demands",
          run_mod._TOP_STORIES_FLOOR >= 2)
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

    # Every collector consumes _fetch_feeds_parallel's {source: (entries, extra)}
    # shape, and the one that forgot to unpack the tuple walked the entries LIST
    # as though it were a single entry. Collection died on the first .get and
    # the brief could not send. The offline suite never calls the collectors —
    # they need network — so nothing here could see it; substituting the fetcher
    # tests the contract without one. Guard every collector, not just the one
    # that broke.
    _fake_entry = {
        "title": "Japan and the alliance: a panel discussion",
        "summary": "A panel on Japan policy. Register to attend. Tokyo, Diet, MOFA.",
        "link": "https://example.org/event",
        "published_parsed": _time.gmtime(),
    }
    _real_fetch = collect._fetch_feeds_parallel
    for _name, _fn, _tiered in (
            ("events", collect._collect_events, None),
            ("tier1", collect._collect_tier1, None),
            ("tier2", collect._collect_tier2, "A"),
            ("tier3", collect._collect_tier3, "A+"),
            ("tier4", collect._collect_tier4, None),
    ):
        collect._fetch_feeds_parallel = (
            lambda d, is_tiered=False, _t=_tiered: {"Fake Feed": ([_fake_entry], _t)})
        try:
            _fn()
            _ok, _why = True, ""
        except Exception as _e:
            _ok, _why = False, f"{type(_e).__name__}: {_e}"
        finally:
            collect._fetch_feeds_parallel = _real_fetch
        check(f"_collect_{_name} unpacks the fetcher's (entries, extra) shape", _ok, _why)

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
    # Reply-To is decoupled from the sending account, so moving the sending
    # Gmail does not silently move reader mail away from the footer contact.
    check("reply-to is its own variable", "DIGEST_REPLY_TO" in src)
    check("unset reply-to falls back to the sender",
          "reply_to or gmail_user" in src)

    # A send that was attempted and failed must fail the RUN. It used to print
    # a warning and exit 0, so a wrong App Password produced a green workflow
    # that emailed nobody — found while moving the brief to the Japan Chair
    # account, when a green test run could not be distinguished from a
    # delivered one.
    _saved = {k: os.environ.get(k) for k in ("GMAIL_USER", "GMAIL_APP_PASS")}
    try:
        os.environ["GMAIL_USER"] = ""
        os.environ["GMAIL_APP_PASS"] = ""
        # Behavioural: missing credentials are reported as a failed send, not
        # swallowed. This is the signal the exit code now depends on.
        check("missing credentials report a failed send",
              send_email.send_digest("<p>x</p>", recipients=["a@csis.org"]) is False)
    finally:
        for k, v in _saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    rsrc = Path("run.py").read_text(encoding="utf-8")
    check("a failed send sets the flag", "send_failed = True" in rsrc)
    check("and the flag fails the run",
          "if send_blocked or send_failed:" in rsrc)
    check("the exit message says which happened",
          'else "the email could not be sent"' in rsrc)
    # --no-send declines to send by request; it must stay green.
    check("--no-send does not mark a failure",
          "--no-send: skipping email send" in rsrc
          and rsrc.index("--no-send: skipping email send")
              < rsrc.index("send_failed = True"))



# ── Subject line ─────────────────────────────────────────────────────────────
# One shape across all four editions: "<Edition> Daily Brief | <Weekday>,
# <Month> <D>, <Year>". Korea used to carry a DIGEST_SUBJECT_STYLE variable that
# appended the lead story, so its subject differed from its siblings depending
# on a repo setting nobody would think to check.
import inspect as _insp, re as _re
from datetime import datetime as _dt
from zoneinfo import ZoneInfo as _ZI
import send_email as _se
_src = _insp.getsource(_se)
_m = _re.search(r'subject = f"([^"]+)"', _src)
check("send_email builds a default subject", _m is not None)
if _m:
    _tmpl = _m.group(1)
    _ds = _dt.now(_ZI("America/New_York")).strftime("%A, %B %-d, %Y")
    _subj = _tmpl.replace("{date_str}", _ds)
    if "{BRIEF_NAME}" in _subj:
        _subj = _subj.replace("{BRIEF_NAME}", _se.BRIEF_NAME)
    check("house subject format: <Edition> Daily Brief | <Weekday>, <Month> <D>, <Year>",
          _re.fullmatch(r"Japan Daily Brief \| \w+, \w+ \d{1,2}, \d{4}", _subj) is not None,
          _subj)
    check("the separator is a pipe, not a dash", "|" in _tmpl and "—" not in _tmpl, _tmpl)

# ── BOJ Policy Board roster ──────────────────────────────────────────────────
# A story reached the brief reading "BOJ board member Masu" six times, with no
# given name, because the source headline named no one and the NAMES rule
# rightly forbids filling that in from memory. The roster is verified data from
# boj.or.jp, so completing a surname from it is not inventing — the rule now
# says so, narrowly.
_BOJ_BOARD = ["Kazuo Ueda", "Shinichi Uchida", "Ryozo Himino", "Hajime Takata",
              "Naoki Tamura", "Junko Koeda", "Kazuyuki Masu", "Toichiro Asada",
              "Ayano Sato"]
# The roster rides in the user payload's leaders reference; the NAMES rule
# that governs its use is in the system prompt. Check each where it lives.
_roster = digest_mod._POLITICAL_LEADERS
_prompt = digest_mod.SYSTEM_PROMPT
check("the Policy Board roster is in the leaders reference", "BANK OF JAPAN POLICY BOARD" in _roster)
for _n in _BOJ_BOARD:
    check(f"roster names {_n}", _n in _roster)
check("all nine members are listed", sum(_roster.count(n) >= 1 for n in _BOJ_BOARD) == 9)
check("the roster cites its source", "boj.or.jp" in _roster)
check("the roster is dated, so staleness is visible", "as of Sep 10 2026" in _roster)
check("the NAMES rule allows completion from a reference block",
      "you may complete it ONLY from a REFERENCE BASELINE block" in _prompt)
check("completion still requires an unambiguous match",
      "matches more than one person" in _prompt)
check("supplying a name from memory is still forbidden",
      "never supply a given name from your own knowledge" in _prompt)



import render as _rmod

# ── Raw markdown must never reach a reader ───────────────────────────────────
# The prompt asks for a name in **double asterisks** and a figure in *single*
# ones, and the renderer converts them. A field that skips the conversion ships
# the asterisks instead: the 10 September China brief carried eighteen, among
# them **Ford** and a half-open **Cynthia "Xanthi". Walking every prose field
# means a newly added one cannot leak quietly.
import copy as _copy
import preview as _preview
_PROSE = ("body","body_text","summary","detail","context","text","note",
          "analyst_note","so_what","headline","central_argument")
_d = _copy.deepcopy(_preview.DIGEST)
_marks = {}
def _mark(o):
    if isinstance(o, dict):
        for k, v in list(o.items()):
            if k in _PROSE and isinstance(v, str) and v.strip():
                t = "MARK%d" % len(_marks); _marks[t] = k; o[k] = "**%s** tail." % t
            else: _mark(v)
    elif isinstance(o, list):
        for x in o: _mark(x)
_mark(_d)
_html = _rmod.render_html(_d)
_leaks = sorted({f for t, f in _marks.items() if "**%s**" % t in _html})
check("no prose field ships literal ** to the reader", not _leaks, ", ".join(_leaks))
_d2 = _copy.deepcopy(_preview.DIGEST)
_d2["top_stories"][0]["body"] = "**<script>alert(1)</script>** and **A Name**"
_h2 = _rmod.render_html(_d2)
check("emphasis cannot smuggle markup past the escaper", "<script>" not in _h2)
check("a genuine name still bolds", 'font-weight:700;">A Name</strong>' in _h2)

# The fixture does not populate every section — Australia's omits canberra
# politics, business, op-eds and academic — so a walk of the fixture alone can
# pass while those sections still leak. Two backstops: the walk must actually
# have marked a meaningful number of fields, and the renderer's source must
# contain no unwrapped prose site at all.
check("the markdown walk actually covered fields, not zero",
      len(_marks) >= 8, f"{len(_marks)} fields marked")
import re as _re2, pathlib as _pl2
_rsrc = _pl2.Path("render.py").read_text(encoding="utf-8")
_unwrapped = _re2.findall(
    r'(?<!_emphasis\()\b_esc\(\w+\.get\("(detail|context|headline|note|body_text|body|summary)", ""\)\)',
    _rsrc)
check("no prose field is rendered without the emphasis conversion",
      not _unwrapped, ", ".join(sorted(set(_unwrapped))))


_COST_DIGEST_MOD = digest_mod
_COST_RUN_FILE = "run.py"
_COST_WF_FILE = ".github/workflows/daily-digest.yml"
# ── API cost must be recorded ────────────────────────────────────────────────
# Recording spend has three parts and any one can go missing without a symptom:
# a per-call ledger, a write of that ledger into metrics.jsonl, and a workflow
# step that commits the file. The Japan edition had none of the three and
# nobody noticed for months; the Korea edition had the first two and its file
# lived only in an Actions cache that GitHub evicts after seven days. Neither
# showed up as a failure, because a missing cost record looks exactly like a
# cheap week. This asserts all three.
import inspect as _ci, pathlib as _cp, re as _cr

_cost_src = _ci.getsource(_COST_DIGEST_MOD)
check("digest keeps a per-call token ledger",
      "TOKEN_LEDGER" in _cost_src or "_RUN_USAGE" in _cost_src)
check("the ledger carries model, tokens and cache counts",
      all(k in _cost_src for k in ('"model"', '"input"', '"output"')) or
      all(k in _cost_src for k in ("input_tokens", "output_tokens")))
check("a price table exists and names the models in use",
      "MODEL_PRICING" in _cost_src or "_PRICING" in _cost_src or "PRICE" in _cost_src.upper())

_run_src = _cp.Path(_COST_RUN_FILE).read_text(encoding="utf-8")
check("run.py writes a metrics line per run",
      "metrics.jsonl" in _run_src or "METRICS_JSONL" in _run_src)
check("the metrics write cannot break a send",
      _cr.search(r"try:[^#]{0,400}metrics", _run_src, _cr.S) is not None or
      "non-fatal" in _run_src.lower())

_wf_src = _cp.Path(_COST_WF_FILE).read_text(encoding="utf-8")
check("the workflow commits metrics.jsonl, so it outlives any cache",
      "metrics.jsonl" in _wf_src)
_gi = _cp.Path(".gitignore")
check("metrics.jsonl is not gitignored (a committed file that git skips is a silent loss)",
      not (_gi.exists() and any(l.strip() == "metrics.jsonl" for l in _gi.read_text().splitlines())))

def main() -> int:
    for t in (test_render, test_source_headlines, test_tense_risk,
              test_source_diversity, test_cross_day, test_dark_mode, test_print_and_mobile, test_length,
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

