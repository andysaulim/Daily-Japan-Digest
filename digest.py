"""
Japan Daily Brief — Digest Generator
Sends collected articles to Claude and returns a structured digest JSON.
"""
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import anthropic


# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are the senior intelligence analyst producing the Japan Daily Brief for the CSIS Japan Chair — a daily Presidential Daily Brief-style product read by top government officials, leading Japan scholars, senior policymakers, and elite journalists.

Your readers include: CSIS Japan and Korea Chairs, senior NSC staff, State Department Japan desk officers, Pentagon Asia policy officials, leading academics (Stanford, Harvard, Georgetown, MIT Japan programs), top correspondents (NYT, WSJ, FT, Bloomberg, Reuters Tokyo bureaus), allied government analysts, and Treasury / Commerce / USTR practitioners working on the US-Japan alliance and trade.

YOUR AUDIENCE IS EXPERT. They do not need your opinion — they need facts, data, and connective context to form their own. Your job is to save them time, surface what they might miss, and connect data points across sources. Do NOT editorialize. Do NOT tell the reader what to think. Do NOT use phrases like "this is significant", "notably", "importantly", or "this matters because." Present the facts and let the expert draw conclusions.

YOUR JOB: Process all incoming Japan-related content and produce a single structured JSON briefing package. Write like an intelligence analyst producing raw intelligence summaries — precise, factual, sourced. Add value through: (1) connecting data points across sources the reader hasn't seen together, (2) providing specific historical precedents with dates, (3) flagging what changed vs. yesterday's baseline.

GROUNDING — ZERO HALLUCINATION RULE (CRITICAL):

You are writing an intelligence product. Getting a name, title, date, or fact wrong destroys credibility. One wrong name and the reader stops trusting every fact in the digest.

SOURCE-OR-SKIP PRINCIPLE: For EVERY factual claim you write, you must be able to point to either (a) a source article in this batch, or (b) a reference baseline provided in this prompt. If a fact comes from neither, DO NOT INCLUDE IT. An omission is always better than an invention.

- ONLY use names, titles, figures, and claims that appear explicitly in the source articles provided. If an article says "the foreign minister" without naming them, use "the foreign minister" — do NOT fill in a name from your training data.

- NEVER substitute a name from your memory when the source text is ambiguous. Your training data may be outdated — Japan's leaders change, ministers rotate, the Prime Minister may have changed since your training cutoff. The source article is ground truth. This applies ESPECIALLY to the sitting Prime Minister.

- If two sources conflict on a fact, note both. If a source is vague, stay vague. Precision means knowing what you DON'T know.

- Cross-check: before writing any person's name + title, verify that BOTH the name AND the title appear together in at least one source article in this batch. If not, do not assert the pairing.

- HISTORICAL CLAIMS: Do NOT cite specific historical dates or precedents from memory. pattern_note and analyst_note fields should ONLY reference precedents that are mentioned in today's source articles or the reference baselines provided in this prompt. If no relevant precedent appears in the provided data, set the field to null rather than inventing one. A wrong date is worse than no date.

- OMISSIONS & STREAKS: Do NOT claim "X absent for N days" or "no mention of Y for N days" unless the tracker data provided in this prompt supports the specific count. If no tracker history is available, do not fabricate streak counts.

- ARITHMETIC & TOTALS: When this prompt provides a PRE-CALCULATED total, percentage, or sum, use it EXACTLY as given. Do NOT recalculate — LLMs make arithmetic errors. Only adjust a pre-calculated value if today's articles introduce a NEW data point not already in the baseline.

- DATES: For calendar_watch and on_this_day, only use dates that appear in (a) today's source articles, (b) the VERIFIED JAPAN DATES list, or (c) the baseline references in this prompt. Do NOT generate dates from memory.

- POLLING — SAME-POLL-DATE RULE: For the public_sentiment block, NEVER mix pollsters or survey dates in one figure set. Cabinet approval, disapproval, and party support shares must all come from the SAME survey by the SAME pollster (NHK, Jiji, Yomiuri, Asahi, or Kyodo) for the SAME date range. Always cite the pollster and the date range. If today's articles do not contain a fresh poll, carry forward the most recent cited poll and label it with its original date — do NOT blend numbers from different polls.

- EVERY ARTICLE MUST EXIST IN THE INPUT: Every item in top_stories, overnight_items, also_today, opeds_today, business_economy, indo_pacific, and social_statements MUST correspond to an actual article from the input data above — with a real URL from that input. Do NOT generate articles from your training data. Do NOT present old events as today's news. Do NOT fabricate generic think tank analyses when no such article exists in today's feed. If a section has fewer qualifying articles than its target count, return fewer items or an empty array. An empty section is ALWAYS better than a fabricated entry.

- THINK TANK FABRICATION — HARD BLOCK: You have a strong tendency to fabricate generic-sounding think tank articles from CSIS, CFR, Brookings, Carnegie, RAND, etc. when the feed is thin. These fabrications follow a telltale pattern: vague titles ("examines evolving security environment", "analyzes the alliance"), no specific data points, and no real URL. STOP. If a think tank article does not appear in the input data with a real URL, it does not exist. Do NOT create it.

- ACADEMIC FABRICATION — HARD BLOCK: Same rule applies to academic_today. Do NOT include any journal article that does not appear in the Tier 3 input with a real URL. The authors field must come from the article metadata — do NOT populate it from training data or invent it. If the authors field is missing from the source, set it to null. A news outlet name appearing as "author" means the source is a news article, not a journal paper — exclude it entirely from academic_today.

- URL INTEGRITY — ZERO TOLERANCE: Every url field must be copied CHARACTER-FOR-CHARACTER from the input article's url field. Do NOT reconstruct, guess, shorten, or invent URLs. Do NOT write a URL based on knowing the publication's domain — only use the exact URL from the input. If an article in the input has no URL or an empty URL, set the url field to "" in your output. A missing URL is always better than a fabricated one.

QUALITY STANDARD — THE EXPERT TEST: Every entry must pass these tests:

1. FACTUAL — Does this state what happened with specifics (who, what, when, numbers)?
2. CONNECTIVE — Does this link to a pattern, precedent, or upcoming event with a specific date?
3. PRECISE — Are claims sourced, numbers specific, and attributions clear?
4. NON-OBVIOUS — Would the reader get this from the headline alone? If yes, rewrite.

Do not add commentary that an expert would find patronizing. An empty section is better than filler.

CSIS JAPAN COVERAGE — INSTITUTIONAL CONTEXT:

The CSIS Japan Chair covers the US-Japan alliance, Japanese domestic politics (LDP/coalition dynamics, Diet, elections, cabinet approval), Japan's defense buildup (counterstrike, 2%-of-GDP plan, Nansei island defenses), economic security and semiconductors (Rapidus, TSMC/JASM Kumamoto, export controls), and Japan's posture toward China, the Korean Peninsula, and Russia. Allied trilateral coordination (US-Japan-ROK, Quad, G7) is a recurring axis.

ALLIANCE AS SPINE: The US-Japan alliance is the central axis of Japan policy analysis. Tariffs, host-nation support, USFJ posture, defense industrial cooperation, and regional deterrence all route back to it. When a story has alliance implications, surface them.

PRESTIGE OUTLET RULE — MANDATORY INCLUSION: If ANY Japan-related article appears from WSJ, Washington Post, NYT, Bloomberg, Financial Times, The Economist, CNN, Reuters, CNBC, NHK, Kyodo, Japan Times, or Nikkei Asia, it MUST be included in the digest — in top_stories if it is a major story, otherwise in overnight_items or also_today. When these outlets publish on Japan it is inherently noteworthy. Never drop such a story.

CSIS PRODUCTS — MANDATORY INCLUSION: If ANY same-day article appears from the CSIS Japan Chair, it MUST appear in opeds_today or also_today. These are the in-house products of the institution publishing this digest; they must surface.

JOURNALIST FLAGGING: The following reporters have special Japan expertise. When their bylines appear, treat the story as higher priority and note the journalist in your analysis:

- River Akira Davis, Hisako Ueno, Kiuko Notoya (NYT Tokyo)
- Michelle Ye Hee Lee (WaPo Tokyo bureau chief), Julia Mio Inuma (WaPo Tokyo)
- Peter Landers, Megumi Fujikawa, Miho Inada, Chieko Tsuneoka (WSJ Tokyo)
- Leo Lewis, Kana Inagaki, Harry Dempsey, Eri Sugiura (FT Tokyo)
- Tim Kelly, Sakura Murakami, Kiyoshi Takenaka, Kantaro Komiya, John Geddie (Reuters Tokyo)
- Isabel Reynolds, Yuki Hagiwara, Erica Yokoyama (Bloomberg Tokyo)
- Mari Yamaguchi (AP Tokyo)

VOICE — ECONOMIST-STYLE, FACTS FIRST:

Write like a senior Economist correspondent: crisp, declarative, no throat-clearing. Every sentence earns its place. Lead with the verb. Never start with "In a move that..." or "According to..." — state what happened.

- Summaries: state the facts — who did what, when, with what numbers. Then add ONE beat of context the reader can't see from the headline (a connection, a precedent, a date)
- Do NOT interpret for the reader. Do NOT say "this suggests X" or "this could mean Y." State the facts and the precedent; the expert reader draws the inference
- Do NOT use hedging phrases: "notably", "importantly", "significantly", "it is worth noting", "interestingly"
- Do NOT start sentences with "This comes as...", "The move comes amid...", "This is significant because..."
- Prefer active voice
- "So what" blocks: name the specific decision, meeting, or timeline this affects. One sentence, no editorializing
- Pattern blocks: cite specific historical precedents with exact dates. No interpretation

BREVITY: Body text: 2-3 sentences max — lead with the specific, add one beat of context. "So what": 1 sentence. Pattern notes: 1 sentence with dates. Academic summaries: 3 sentences. Cut all filler.

JAPANESE GOVERNMENT MONITORING: Track activity from these institutions and report any meetings, statements, press briefings, policy announcements, or personnel changes:

- Prime Minister's Office (Kantei) — PM statements, press conferences, diplomacy
- Chief Cabinet Secretary — twice-daily press conferences, government position
- Ministry of Foreign Affairs (Gaimusho / MOFA) — diplomatic posture, presser, protests
- Ministry of Defense (MOD) / Joint Staff — scrambles, China/Russia incursions, exercises
- METI (Ministry of Economy, Trade and Industry) — trade, energy, semiconductors, export controls
- Ministry of Finance (MOF) — budget, FX intervention, currency policy
- Bank of Japan (BOJ) — monetary policy, rate decisions, YCC/policy normalization
- National Security Secretariat (NSS) / National Security Council
- Cabinet personnel and SDF/ambassador appointments

Include only substantive actions (not routine admin). Each entry: ministry, action (1-line headline), detail (1-2 sentences), source URL.

FORMATTING: Do NOT use emojis anywhere in the output. Plain text only.

DEDUPLICATION — CRITICAL (ZERO TOLERANCE):

- ONE TOPIC = ONE ENTRY across the ENTIRE digest. Before placing ANY item, ask: "Is this the same underlying event, decision, or announcement as something already placed?" If yes, DO NOT include it — regardless of source, angle, or section.

- Common duplicates to watch for:
  * "BOJ holds rates" / "Bank of Japan keeps policy rate steady" — ONE entry
  * "PM meets foreign leader" / "Tokyo summit" / "PM-X bilateral" — ONE entry
  * "Japan scrambles jets" / "JASDF intercepts Chinese aircraft" — ONE entry
  * Any wire story (Reuters/AP/AFP/Kyodo) picked up by other outlets — same story, ONE entry

- Pick the BEST source for each topic and place it in the HIGHEST appropriate section.

- LIFESTYLE / ENTERTAINMENT — HARD BLOCK: NEVER include J-pop, idol/celebrity, anime-only, fashion, or cultural-only content in any section. This newsletter covers geopolitics, trade policy, technology, security, and foreign affairs ONLY. Cultural content qualifies ONLY if it has a clear policy or security implication.

- CATEGORIES: Valid categories for top_stories are: Alliance, China-Japan, Korea-Japan, DPRK, Economy/BOJ, Politics/Diet, Defense, Technology, Indo-Pacific, Energy.

Return ONLY valid JSON. No markdown, no preamble, no commentary outside the JSON structure."""


# ─────────────────────────────────────────────────────────────────────────────
# REFERENCE BASELINES
# ─────────────────────────────────────────────────────────────────────────────

_POLITICAL_LEADERS = """\
CURRENT POLITICAL LEADERS — REFERENCE (VERIFY from today's articles; leadership may have changed):

JAPAN GOVERNMENT (Takaichi Cabinet, inaugurated Oct 21 2025, reshuffled Feb 18 2026 — VERIFY from today's articles; ALWAYS use the name from today's articles if it differs):
- Prime Minister: Sanae Takaichi (LDP) — Japan's first female prime minister; succeeded Shigeru Ishiba (since Oct 21 2025). If an article names a different PM, USE THAT NAME.
- Chief Cabinet Secretary: Minoru Kihara
- Foreign Minister (Gaimusho / MOFA): Toshimitsu Motegi
- Defense Minister (MOD): Shinjiro Koizumi
- Finance Minister (MOF): Satsuki Katayama — Japan's first female finance minister
- METI Minister: Ryosei Akazawa — also led US tariff negotiations
- Internal Affairs & Communications Minister: Yoshimasa Hayashi
- Bank of Japan Governor: Kazuo Ueda — since April 2023 (verify)
- LDP leadership (President = PM by convention; Secretary-General, Policy Research Council chair): VERIFY
- Komeito (LDP's coalition partner): leader VERIFY from articles
- Main opposition: Constitutional Democratic Party (CDP) — leader Yoshihiko Noda (verify); other parties: DPP (Democratic Party for the People), Ishin (Japan Innovation Party), JCP (Japanese Communist Party), Reiwa Shinsengumi, Sanseito

US LEADERSHIP (Trump 2nd term, inaugurated Jan 2025):
- President: Donald Trump
- Vice President: JD Vance
- SecState: Marco Rubio
- SecDef: Pete Hegseth
- Treasury Sec: Scott Bessent
- Commerce Sec: Howard Lutnick
- USTR: Jamieson Greer
- INDOPACOM Commander: verify current — was Adm. Samuel Paparo
- US Ambassador to Japan: VERIFY from today's articles

If today's articles name a different officeholder for any position, USE THE NAME FROM THE ARTICLE. This is especially important for the Prime Minister and cabinet ministers."""


_TRADE_BASELINES = """\
US-JAPAN ALLIANCE & TRADE BASELINES (as of early 2026 — carry forward unless today's articles report a change):

TARIFFS APPLIED TO JAPAN (Section 232 / 122 — national-security and emergency authorities apply to allies too):
- Section 232 Automobiles: 25% on autos and auto parts — a central Japanese concern given the auto sector's weight in Japan-US trade. VERIFY current rate and any Japan-specific carve-out from today's articles.
- Section 232 Steel & Aluminum: 50% (country exemptions eliminated). Applies to Japan unless a deal carve-out is reported.
- Section 122 surcharge: temporary global surcharge (10%) with a 150-day statutory limit — applies to Japan the same as other countries. VERIFY status.
- 2024-2025 US-Japan trade/tariff deal: a negotiated framework on tariffs and investment was reported; STATUS = VERIFY from today's articles (terms, investment pledges, and whether auto relief was granted).

ALLIANCE & DEFENSE BASELINES:
- Host-Nation Support ("Sympathy Budget" / omoiyari yosan): Japan funds a large share of USFJ stationing costs under multi-year Special Measures Agreements. VERIFY current cycle.
- Defense spending: Japan's Dec 2022 National Security Strategy commits to raising defense spending toward 2% of GDP by FY2027, plus a counterstrike (long-range strike) capability. Carry forward unless updated.
- US-Japan Security Treaty Article 5: the US treaty commitment to defend territories under Japanese administration — successive US administrations have affirmed it covers the Senkaku Islands.
- USFJ realignment: MCAS Futenma relocation to Henoko (Camp Schwab) remains contested in Okinawa; carry forward.
- Semiconductor / economic security cooperation: Rapidus (2nm foundry, Hokkaido), TSMC Kumamoto (JASM) fabs, and Japan's alignment with US export controls on advanced chips to China. Carry forward unless updated.

USE THESE BASELINES EXACTLY unless today's articles report a NEW policy action or status change. Do NOT invent trade or alliance policy items from memory. Mark anything uncertain "verify"."""


_KEY_DATES = """\
VERIFIED JAPAN DATES (use ONLY these for on_this_day unless today's articles contain a sourced historical reference):

Jan 19 1960: Revised US-Japan Treaty of Mutual Cooperation and Security signed in Washington.
Feb 7: Northern Territories Day (Japan's annual observance pressing Russia over the four disputed islands).
Mar 11 2011: Great East Japan (Tohoku) earthquake and tsunami; Fukushima Daiichi nuclear disaster.
Apr 28 1952: San Francisco Peace Treaty enters into force, ending the Allied Occupation.
May 3 1947: Constitution of Japan takes effect (Constitution Day).
Jul 8 2022: Former PM Shinzo Abe assassinated in Nara during a campaign speech.
Aug 6 1945: Atomic bombing of Hiroshima.
Aug 9 1945: Atomic bombing of Nagasaki.
Aug 15 1945: Emperor Hirohito's radio announcement of surrender (end of WWII in Japan).
Sep 2 1945: Japan signs the formal instrument of surrender aboard USS Missouri.
Sep 8 1951: San Francisco Peace Treaty signed.
Dec 8 1941 (Dec 7 US time): Attack on Pearl Harbor."""


_VERIFIED_UPCOMING = """\
VERIFIED UPCOMING DATES (use these + any dated events from today's articles; mark estimates):

Feb 7: Northern Territories Day — annual rally pressing Russia (recurring).
May 3: Constitution Day — focal point for constitutional-revision debate (recurring).
Recurring: Diet ordinary session typically convenes in January and runs ~150 days; extraordinary sessions convened as needed. VERIFY current session dates from articles.
Recurring: Bank of Japan Monetary Policy Meetings — roughly 8 per year; each can move the policy rate. VERIFY next meeting date from articles (estimate).
Recurring: G7 and Quad summits and ministerials — dates vary by host; VERIFY from articles.
Recurring: Japan's annual defense budget cycle — MOD budget request (late summer), Cabinet draft budget (December), Diet passage (March). VERIFY year-specific dates.
Anniversaries from VERIFIED JAPAN DATES (Hiroshima/Nagasaki Aug 6/9, surrender Aug 15, Tohoku Mar 11, Abe Jul 8) recur and draw heavy coverage.
Only assert a specific future date if it appears in today's articles; otherwise describe the event as recurring/estimated."""


# ─────────────────────────────────────────────────────────────────────────────
# USER PROMPT BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def _has_tier4_data(payload: dict) -> bool:
    """Check whether any Tier 4 (gov / adversary) data was actually collected."""
    summary = payload.get("messaging_summary")
    has_summary = summary and summary.get("total_articles", 0) > 0
    has_tier4 = bool(payload.get("tier4"))
    return has_summary or has_tier4


_REGIONAL_NO_DATA_STUB = (
    "NO TIER 4 DATA COLLECTED TODAY — scrapers returned 0 articles.\n"
    "Do NOT fabricate Japanese-government or adversary statements. Return a minimal regional_watch (key: xinhua_delta) with:\n"
    " silence_today: true, output_volume: \"Unavailable — 0 articles collected (scraper failure)\",\n"
    " pm_appearance_today: false (unless PM APPEARANCE REPORTS above confirm otherwise),\n"
    " pm_days_since_last_appearance: use tracker data above,\n"
    " china_signal: null, dprk_signal: null, russia_signal: null, senkaku_status: null,\n"
    " key_quotes: [], watch_flag: false,\n"
    " bottom_line: \"No Tier 4 data collected — scraper issue, not an absence of activity.\""
)


_REGIONAL_FULL_INSTRUCTIONS = (
    "Return a SINGLE regional_watch object (TOP-LEVEL KEY MUST BE NAMED \"xinhua_delta\") analyzing adversary pressure toward Japan and the PM's public posture:\n"
    "- pm_appearance_today: boolean — cross-reference PM APPEARANCE REPORTS above and today's articles. True if the Prime Minister made any confirmed public appearance, statement, Diet appearance, or meeting in the last 24h. (The PM appears near-daily; true should be common.)\n"
    "- pm_activity: if appeared, 1 sentence on what the PM did, else null\n"
    "- pm_days_since_last_appearance: integer — use the CONFIRMED PM APPEARANCES tracker data above as ground truth.\n"
    "- china_signal: 1-2 sentences on today's notable China activity or statements toward Japan — China Coast Guard / PLA activity near the Senkakus, China MOFA statements on Japan/Senkaku/Taiwan, survey vessels. null if nothing notable today.\n"
    "- dprk_signal: 1-2 sentences on North Korean missile/nuclear activity affecting Japan (launches, EEZ splashdowns, overflights, KCNA statements naming Japan). null if nothing notable.\n"
    "- russia_signal: 1-2 sentences on Russian activity bearing on Japan — Northern Territories, Sea of Okhotsk, air-sea incursions near Hokkaido, statements on the territorial dispute. null if nothing notable.\n"
    "- senkaku_status: 1 sentence on the current Senkaku / East China Sea status (e.g. CCG patrol-day pattern, intrusions, scrambles), drawing on today's articles. null if no data.\n"
    "- key_quotes: up to 2 direct quotes most analytically significant today from an adversary government (China MOFA, KCNA, Russian MFA/TASS) OR from a Japanese government response. Each: quote (exact text, translated if needed), source_article (title), speaker (if attributed). Empty array if nothing notable.\n"
    "- output_volume: string assessment of how much Tier 4 material came in today (e.g. \"Normal — 14 items\"). Use the SUMMARY above for the count.\n"
    "- silence_today: boolean — true only if complete Tier 4 blackout (rare)\n"
    "- watch_flag: boolean — true if today's adversary activity is escalation-level (missile overflight, airspace intrusion, CCG use-of-force, major Russian deployment) or if the PM is unusually absent (7+ days).\n"
    "- bottom_line: 1-2 sentences MAX. The single most important regional-pressure takeaway and what to watch. Ruthlessly concise."
)


def _build_messaging_summary_block(payload: dict) -> str:
    """Format the pre-collected Tier 4 messaging summary into a prompt block."""
    summary = payload.get("messaging_summary")
    if not summary or not summary.get("total_articles"):
        return ""

    gov = summary.get("gov_count", 0)
    adversary = summary.get("adversary_count", 0)

    lines = [
        "TIER 4 OUTPUT SUMMARY (scraped today — Japanese government primary + adversary signal):",
        f"Total unique items: {summary['total_articles']} "
        f"(Japanese government: {gov}, adversary signal: {adversary})",
    ]

    sources = summary.get("sources", {})
    if sources:
        src_strs = [f"{src}: {count}" for src, count in
                   sorted(sources.items(), key=lambda x: -x[1])]
        lines.append(f"Sources: {', '.join(src_strs)}")

    headlines = summary.get("headlines", [])
    if headlines:
        lines.append(f"\nToday's headlines ({len(headlines)} items):")
        for h in headlines:
            lines.append(f"  • {h}")

    lines.append("")
    return "\n".join(lines)


def build_user_prompt(payload: dict, date_str: str, db_context: str = "") -> str:
    def tier_json(articles: list, max_items: int = 60) -> str:
        trimmed = articles[:max_items]
        result = []
        for a in trimmed:
            item = {
                "title": a.get("title", ""),
                "url": a.get("url", ""),
                "summary": a.get("summary", "")[:800],
                "source": a.get("source", ""),
                "lang": a.get("lang", "EN"),
                "prestige_tier": a.get("prestige_tier"),
                "japan_primary": a.get("japan_primary", False),
                "journal_tier": a.get("journal_tier"),
            }
            if a.get("tags"):
                item["tags"] = a["tags"]
            result.append(item)
        return json.dumps(result, ensure_ascii=False, indent=1)

    # Market data block
    market_block = ""
    markets = payload.get("market_indicators")
    if markets:
        market_block = f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MARKET DATA (pre-collected, include as-is in output)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{json.dumps(markets, indent=1)}

Pass this data through directly as the market_indicators field in your output. Do NOT modify the values."""

    # Reference context (Japan timelines)
    db_block = ""
    if db_context:
        db_block = f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
JAPAN REFERENCE CONTEXT (verified timelines)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{db_context}

Use this for on_this_day, calendar_watch, and pattern_note fields."""

    # PM appearance tracker
    pm_block = ""
    pm_articles = payload.get("pm_tracker_articles", [])
    if pm_articles:
        pm_block += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PM APPEARANCE REPORTS (scraped from multiple sources, last 72h)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{tier_json(pm_articles, max_items=20)}

Cross-reference these reports with Tier 4 data."""

    try:
        from pm_tracker import build_context_block as pm_context
        pm_history = pm_context()
        if pm_history:
            pm_block += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{pm_history}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    except Exception:
        pass

    # Regional pressure history
    region_block = ""
    try:
        from region_tracker import build_context_block as region_context
        region_history = region_context()
        if region_history:
            region_block = f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{region_history}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    except Exception:
        pass

    # Tier 4 block — gate on actual data
    if _has_tier4_data(payload):
        tier4_block = (
            f"{_build_messaging_summary_block(payload)}\n"
            f"{tier_json(payload.get('tier4', []), max_items=30)}\n"
            f"{_REGIONAL_FULL_INSTRUCTIONS}"
        )
    else:
        tier4_block = _REGIONAL_NO_DATA_STUB

    return f"""Today's date: {date_str}

Process each tier according to its instructions and return a single JSON object.

CRITICAL — SOURCE GROUNDING: Every name, title, number, and fact you write MUST come from the source articles below. Do NOT fill in names from memory. Use the CURRENT POLITICAL LEADERS reference below only when the source article clearly refers to that role. The sitting Prime Minister may have changed since your training cutoff — always use the name from today's articles.

CRITICAL — SOURCE URLs: Every article, op-ed, academic paper, and statement MUST include the original source URL from the input data. Use the exact URL provided in the feed data. Never use "#" or placeholder URLs.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POLITICAL LEADERS REFERENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{_POLITICAL_LEADERS}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
US-JAPAN ALLIANCE & TRADE BASELINES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{_TRADE_BASELINES}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VERIFIED HISTORICAL DATES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{_KEY_DATES}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VERIFIED UPCOMING DATES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{_VERIFIED_UPCOMING}
{market_block}
{pm_block}
{region_block}
{db_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIER 1: NEWS ARTICLES (last 24h)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{tier_json(payload.get("tier1", []))}

Score and triage these Tier 1 articles INTERNALLY — do NOT emit a per-article array for Tier 1. Use them to populate the curated output sections defined under DIGEST SYNTHESIS below (top_stories, overnight_items, also_today, indo_pacific, business_economy). Only those synthesized sections are part of the output.

When triaging, for each article weigh:
- categories: Alliance / China-Japan / Korea-Japan / DPRK / Economy-BOJ / Politics-Diet / Defense / Technology / Indo-Pacific / Energy
- relevance to a Japan policy analyst today (10 = essential)
- whether it is a reaction source (Global Times, Xinhua, KCNA, TASS, RT) — attribute accordingly
- US-Japan alliance implications, and any escalation/anomaly precedent that appears in today's articles or the reference databases (never cite precedent from memory)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIER 2: OP-EDS & PRESTIGE COMMENTARY → OUTPUT: opeds_today
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{tier_json(payload.get("tier2", []), max_items=30)}

ANTI-HALLUCINATION — OP-EDS: Only include op-eds/commentary that appear as actual articles in the Tier 2 input data above with a real URL. Do NOT fabricate think tank entries or authors. If no qualifying Tier 2 articles are present today, return an empty opeds_today array.

Each article in the Tier 2 input has fields: prestige_tier ("A" = top tier, "B" = standard), japan_primary (true for all Tier-A sources — already computed). Use these directly; do not override them.

For EACH qualifying piece output: title (verbatim from input), url (verbatim from input — do not alter), source, prestige_tier (from input), authors (from article metadata if available, else null), japan_primary (from input), relevance_score (1-10), central_argument (single sentence stating the thesis directly), summary (2-3 sentences), policy_so_what (1 sentence, score >= 6 only).

Inclusion thresholds: prestige_tier "A" with japan_primary=true → always include. prestige_tier "B" or "A" without japan_primary → include if relevance_score >= 7.

CSIS PRODUCTS (CSIS Japan Chair): MANDATORY inclusion whenever present in input — these are our own in-house products.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIER 3: ACADEMIC JOURNALS → OUTPUT: academic_today
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{tier_json(payload.get("tier3", []), max_items=20)}

ANTI-HALLUCINATION — ACADEMIC: Only include journal articles that appear in the Tier 3 input data above with a real URL. Do NOT fabricate journal articles, authors, or journal names. News outlets are NEVER journal authors — if a source is not a recognized academic journal, skip it.

For EACH qualifying piece output: title (verbatim from input), url (verbatim from input — do not alter), source (journal name from input), journal_tier (from input: A+/A/B), authors (from article metadata if available, else null), japan_relevance_score (1-10), framework, summary (2-3 sentences), policy_implication (1 sentence).

Inclusion thresholds: journal_tier "A+" → include if score >= 4. journal_tier "A" → include if score >= 6. journal_tier "B" → include if score >= 8.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIER 4: JAPANESE GOVERNMENT PRIMARY + ADVERSARY SIGNAL (last 48h)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{tier4_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DIGEST SYNTHESIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TARGET LENGTH — HARD MINIMUM 1,000 WORDS (5-minute read). Aim for 1,200-1,400 words.

Return a digest object with:

- digest_date: "{date_str}"

- re_line: one-line RE: summary (max 120 chars, key themes separated by ·)

- editor_note: 1-2 sentence framing of today's news. Factual, no editorializing.

- market_indicators: pass through the pre-collected market data object exactly as provided.

- morning_memo: EXACTLY 3 items. Each one sentence summarizing one of today's top Japan stories. What a Japan desk officer tells their boss in the elevator. Lead with the verb. Sourced from today's actual articles.

- on_this_day: array with at most 1 historical Japan event matching TODAY's EXACT calendar date (month + day). Use VERIFIED JAPAN DATES list ONLY. Empty array if no verified event falls on today's date. Each: date (e.g. "August 15, 1945"), event (1 sentence), relevance (1 sentence connecting to current situation).

- key_stat: a single striking statistic from TODAY's articles — must be different from yesterday. Object: number (e.g. "¥2.3T", "53%", "12"), label (under 60 chars), context (1 sentence), source (article it came from).

- prc_government: REPURPOSED AS JAPANESE GOVERNMENT — array of Japanese government actions from today's news (Kantei/PMO, Chief Cabinet Secretary, MOFA, MOD/Joint Staff, METI, MOF, BOJ, NSS). Each: ministry (English, e.g. "Ministry of Foreign Affairs"), ministry_jp (Japanese, e.g. 外務省, 防衛省, 経済産業省, 日本銀行, 官邸), official (name + title, only if named in an article), action (1-line headline), detail (1-2 sentences), source_label (e.g. "MOFA", "MOD/Joint Staff", "BOJ", "Kantei"), url.

- npc_politburo: REPURPOSED AS DIET SESSIONS / LDP — array of Diet floor activity, committee action, LDP/coalition leadership moves, or party-politics developments from today's news. Each: body (e.g. "House of Representatives", "House of Councillors", "LDP", "CDP"), action, detail (1-2 sentences), url. Empty array if no relevant activity.

- congressional_watch: REPURPOSED AS DIET WATCH — array of legislative activity: key bills, budget, Diet committee sessions, party maneuvering (House of Representatives / House of Councillors). Optionally include US Congress action specifically on Japan. Each: committee (the chamber/committee/party), action (1 line), detail (1-2 sentences), members (key names if named in articles), url. Empty if nothing today.

- calendar_watch: array of 4-5 key upcoming events in next 14-30 days (MIN 4, MAX 5). Only use events from (a) today's articles with dates, (b) VERIFIED UPCOMING DATES, or (c) baselines. Each: month (3-letter), day (int), headline, detail (1-2 sentences).

- overnight_items: 6 items MAX. Source diversity MANDATORY (max 3 from any single source). Topic diversity MANDATORY. Each: url (verbatim from input), source, category, headline (under 100 chars), body_text (2-3 sentences, 50-70 words).

- top_stories: 2-4 biggest HARD NEWS stories — aim for 3 typical, 2 slow days, 4 when multiple major stories. From wires/correspondents/Japanese press/government — NOT op-eds or think tank commentary. TOPIC DIVERSITY MANDATORY. Each: url (verbatim from input), source, category_tag (Alliance/China-Japan/Korea-Japan/DPRK/Economy-BOJ/Politics-Diet/Defense/Technology/Indo-Pacific/Energy), headline, body (MAX 3 sentences, aim for 2 — facts: who/what/when/specifics), so_what (1 sentence — specific decision/meeting/timeline this affects, only if it appears in today's articles or calendar_watch), pattern_note (1 sentence with historical precedent ONLY if it appears in today's articles or reference data; else null), src_line.

- also_today: up to 6 remaining articles score >= 4. Each: url (verbatim from input), source, category, headline, body_text (1-2 sentences), color_bar_class (cb-navy=Alliance, cb-red=Defense, cb-lt=Trade/Economy, cb-mid=Diplomacy, cb-tech=Technology, cb-biz=Politics).

- us_china_trade: REPURPOSED AS US-JAPAN ALLIANCE & TRADE — object with sub-blocks (NO REPETITION across sub-blocks):
  - tariff_tracker: object with headline_auto_rate (current Section 232 auto rate as applied to Japan), section_232_rates (object: steel, aluminum, autos), section_122_surcharge (string), trade_deal_status (1 phrase — verify), last_change (string), next_trigger (string). Use the ALLIANCE & TRADE BASELINES above as default; only change if today's articles report new action.
  - alliance_tracker: object with defense_spending_goal ("2% of GDP by FY2027"), article5_senkaku ("affirmed — covers Senkakus"), host_nation_support (1 phrase, verify), usfj_realignment ("Futenma → Henoko, contested"). Carry forward unless today's articles update.
  - deals: array of NEW US-Japan agreements, investment pledges, or defense-cooperation announcements reported TODAY. Each: url, source, headline, value (or null), parties, detail (1 sentence).

- business_economy: array up to 6 Japan business/economy items. Each: url (verbatim from input), source, headline, body_text (1-2 sentences with specific numbers), companies (array of names), sector (tech/auto/energy/finance/manufacturing/semiconductors/macro).

- indo_pacific: array of 4-6 items covering China-Japan, Korea-Japan, DPRK, US-Japan-ROK trilateral, Quad, Taiwan, Southeast Asia, Australia, India as they relate to Japan. Each: url (verbatim from input), source, headline, body_text (1-2 sentences), category (china-japan, senkaku, korea-japan, dprk-missile, trilateral, quad, taiwan, southeast-asia, australia, india), region_tag ("China-Japan" / "Korea-Japan" / "DPRK" / "Trilateral" / "Indo-Pacific").

- social_statements: 3-6 quotes from senior officials. ATTRIBUTION RULE: quote MUST be a statement made BY the named person in their OFFICIAL CAPACITY on a policy-relevant topic. Prioritize the Japanese PM, Chief Cabinet Secretary, Foreign/Defense/Finance Ministers, BOJ Governor; US officials (Trump, Rubio, Hegseth, Bessent, Greer); and relevant foreign leaders. Use the name from the article.

Each: avatar_initials (2 letters), who (name), handle_context (title/role), platform_date (source · date), quote_text (direct quote), analyst_note (1 sentence factual context only from today's articles or reference data; no interpretation), badge_class (sb-p=policy, sb-r=security/red, sb-s=specialist/purple), url.

- personnel_changes: array of Japan cabinet/ministerial/SDF/ambassador personnel changes from today's news. Each: position, name, action (appointed/resigned/dismissed/nominated/confirmed/reshuffled), detail (1-2 sentences), predecessor (if relevant).

- public_sentiment: Japan cabinet approval & party-support polling block. SAME-POLL-DATE RULE: all figures in approval_polling must come from ONE survey by ONE pollster for ONE date range. Object with:
  - approval_polling: object or null with pollster (NHK / Jiji / Yomiuri / Asahi / Kyodo), poll_date (date range string), cabinet_approval (e.g. "42%"), cabinet_disapproval (e.g. "38%"), approval_change (vs prior same-pollster poll, e.g. "↓3" or null), source_article (title). null if no poll in today's articles (or carry forward the most recent cited poll, clearly labeled with its original date).
  - party_support: array (max 6) of {{party, support_pct}} from the SAME poll as approval_polling. Empty if no poll.
  - discourse_flag: 1 sentence on a notable domestic-political dynamic from today's articles (e.g. coalition strain, leadership challenge, scandal), or null.

- opeds_today: qualifying Tier 2 pieces, ordered by prestige then score
- academic_today: qualifying Tier 3 pieces, ordered by journal_tier then score
- xinhua_delta: the REGIONAL PRESSURE WATCH object built per the Tier 4 instructions above (keep the top-level key name "xinhua_delta")
- timeline_candidates: list of urls flagged for any CSIS bilateral event database (Senkaku/ECS incidents, DPRK launches over/near Japan, US-Japan alliance milestones)

PLACEMENT PRIORITY (highest wins): top_stories > overnight_items > indo_pacific > us_china_trade > business_economy > also_today. Each article appears in exactly ONE section — deduplicate by URL AND topic.

- story_count: total Tier 1 articles processed
- oped_count: qualifying Tier 2 count
- academic_count: qualifying Tier 3 count

Return ONLY valid JSON. No markdown fences, no preamble."""


# ─────────────────────────────────────────────────────────────────────────────
# JSON PARSE + STREAM HELPERS
# ─────────────────────────────────────────────────────────────────────────────

_TEXT_FIELDS = ("body", "body_text", "summary", "detail", "quote_text",
               "so_what", "pattern_note", "central_argument", "analyst_note")


def _count_digest_words(digest: dict) -> int:
    words = 0
    for mi in (digest.get("morning_memo") or []):
        if isinstance(mi, dict):
            for v in mi.values():
                if isinstance(v, str):
                    words += len(v.split())
        elif isinstance(mi, str):
            words += len(mi.split())

    for section_key in ("top_stories", "overnight_items", "also_today", "business_economy",
                       "opeds_today", "academic_today", "social_statements",
                       "indo_pacific", "congressional_watch", "prc_government"):
        for item in (digest.get(section_key) or []):
            if not isinstance(item, dict):
                continue
            for field in _TEXT_FIELDS:
                val = item.get(field, "")
                if val:
                    words += len(str(val).split())

    delta = digest.get("xinhua_delta") or {}
    for field in ("bottom_line", "china_signal", "dprk_signal", "russia_signal", "senkaku_status"):
        val = delta.get(field, "")
        if val:
            words += len(str(val).split())

    return words


def _check_content_minimums(digest: dict) -> list[str]:
    failures = []
    word_count = _count_digest_words(digest)
    if word_count < 1000:
        failures.append(f"WORD COUNT: {word_count} words (hard minimum 1000)")
    top = len(digest.get("top_stories") or [])
    if top < 2:
        failures.append(f"TOP STORIES: {top} (minimum 2)")
    overnight = len(digest.get("overnight_items") or [])
    if overnight < 3:
        failures.append(f"OVERNIGHT ITEMS: {overnight} (minimum 3)")
    memo = len(digest.get("morning_memo") or [])
    if memo != 3:
        failures.append(f"MORNING MEMO: {memo} (must be exactly 3)")
    return failures


def _strip_fences(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r'^```\w*\s*$', '', text, flags=re.MULTILINE)
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```\w*', '', text, count=1)
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _robust_json_parse(raw: str) -> dict:
    text = raw.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    stripped = _strip_fences(text)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace:last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    preview = text[:200]
    raise json.JSONDecodeError(
        f"All JSON extraction strategies failed. Response starts with: {preview!r}",
        text, 0,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CLAUDE API CALL — Sonnet primary, Opus retry
# ─────────────────────────────────────────────────────────────────────────────

FAST_MODEL = "claude-sonnet-4-6"
PRIMARY_MODEL = "claude-opus-4-8"


def _stream_claude(client, messages: list, max_tokens: int = 32000,
                  retries: int = 3, model: str | None = None) -> dict:
    use_model = model or PRIMARY_MODEL
    model_label = use_model.split("-")[1]

    # NOTE: The Claude 4.6/4.7/4.8 family does not support assistant-message
    # prefill — a trailing {"role":"assistant"} turn returns a 400. The prompt
    # already requires pure JSON; _robust_json_parse() strips any stray fences.
    request_messages = list(messages)

    for attempt in range(retries):
        try:
            t0 = time.time()
            collected = []
            with client.messages.stream(
                model=use_model,
                max_tokens=max_tokens,
                system=[{
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }],
                messages=request_messages,
            ) as stream:
                for text in stream.text_stream:
                    collected.append(text)
                response = stream.get_final_message()

            if response.stop_reason == "max_tokens":
                print(f"   ⚠ Response truncated ({response.usage.output_tokens} tokens)")

            elapsed = time.time() - t0
            raw_text = "".join(collected)

            if not raw_text.strip():
                raise ValueError("Empty response from Claude API")

            cache_read = getattr(response.usage, 'cache_read_input_tokens', 0) or 0
            cache_create = getattr(response.usage, 'cache_creation_input_tokens', 0) or 0
            cache_info = ""
            if cache_read:
                cache_info = f" / {cache_read} cache-hit"
            elif cache_create:
                cache_info = f" / {cache_create} cache-write"

            print(f"   ⏱ {model_label} call: {elapsed:.0f}s "
                  f"({response.usage.input_tokens} in / {response.usage.output_tokens} out{cache_info})")

            return _robust_json_parse(raw_text)

        except (httpx.RemoteProtocolError, httpx.ReadError, httpx.StreamError) as e:
            if attempt < retries - 1:
                wait = 5 * (attempt + 1)
                print(f"   ⚠ Stream interrupted ({type(e).__name__}), retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


def _call_claude(client, user_prompt: str, max_tokens: int = 32000,
                model: str | None = None) -> dict:
    return _stream_claude(client, [{"role": "user", "content": user_prompt}],
                         max_tokens, model=model)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY
# ─────────────────────────────────────────────────────────────────────────────

def generate_digest(payload: dict, db_context: str = "") -> dict:
    """Call Claude and return structured digest JSON. Retries on failure and enforces content minimums."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ANTHROPIC_API_KEY environment variable.")

    client = anthropic.Anthropic(api_key=api_key)
    date_str = datetime.now(ZoneInfo("America/New_York")).strftime("%A, %B %-d, %Y")
    user_prompt = build_user_prompt(payload, date_str, db_context=db_context)

    total_articles = sum(len(v) for k, v in payload.items() if isinstance(v, list))
    print(f"   {total_articles} articles → Claude")

    MAX_ATTEMPTS = 4
    digest = None
    best_digest = None
    best_word_count = 0
    content_failures = []

    for attempt in range(MAX_ATTEMPTS):
        try:
            retry_model = FAST_MODEL if attempt == 0 else PRIMARY_MODEL

            if attempt == 0 or digest is None:
                digest = _call_claude(client, user_prompt, model=retry_model)
            else:
                word_deficit = max(0, 1000 - _count_digest_words(digest))
                expansion_prompt = (
                    f"Your previous digest output failed content minimums:\n"
                    + "\n".join(f"  • {f}" for f in content_failures)
                    + f"\n\nYou are ~{word_deficit} words short of the 1000-word minimum.\n"
                    + "\nHere is your previous output:\n"
                    + json.dumps(digest, ensure_ascii=False)[:8000]
                    + "\n\nRevise and return a COMPLETE updated digest JSON that fixes ALL failures. "
                      "Add MORE items from available articles to reach 1000+ words — do not inflate existing bodies. "
                      "Return ONLY valid JSON."
                )
                messages = [
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": json.dumps(digest, ensure_ascii=False)[:4000]},
                    {"role": "user", "content": expansion_prompt},
                ]
                digest = _stream_claude(client, messages, model=retry_model)

            # Preserve market data
            if payload.get("market_indicators") and not digest.get("market_indicators"):
                digest["market_indicators"] = payload["market_indicators"]

            # Track best across attempts
            word_count = _count_digest_words(digest)
            if word_count > best_word_count:
                best_digest = json.loads(json.dumps(digest))
                best_word_count = word_count

            content_failures = _check_content_minimums(digest)
            top_count = len(digest.get("top_stories") or [])
            overnight_count = len(digest.get("overnight_items") or [])

            if content_failures and attempt < MAX_ATTEMPTS - 1:
                print(f"   ⚠ Attempt {attempt + 1}: ~{word_count} words, "
                      f"{top_count} top, {overnight_count} overnight — retrying")
                time.sleep(2)
                continue

            if content_failures:
                if best_digest and best_word_count > word_count:
                    print(f"   ⚠ Using best attempt (~{best_word_count} words)")
                    digest = best_digest
                    word_count = best_word_count
                    top_count = len(digest.get("top_stories") or [])
                    overnight_count = len(digest.get("overnight_items") or [])
                else:
                    print(f"   ⚠ All attempts below minimums (~{word_count} words)")
            else:
                print(f"   ✓ ~{word_count} words, {top_count} top stories, {overnight_count} overnight")

            return digest

        except (anthropic.APIError, anthropic.APIConnectionError,
               httpx.RemoteProtocolError, httpx.StreamError,
               json.JSONDecodeError, ValueError) as e:
            # JSONDecodeError/ValueError usually mean a truncated or fence-wrapped
            # response — retry (escalating to Opus on attempt >= 1) rather than crash.
            if attempt < MAX_ATTEMPTS - 1:
                wait = 5 * (attempt + 1)
                print(f"   ⚠ Generation error (retrying in {wait}s): {type(e).__name__}: {str(e)[:160]}")
                time.sleep(wait)
            else:
                raise

    return digest or {}
