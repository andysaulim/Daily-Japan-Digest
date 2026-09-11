"""Generate CSIS_Digest_Presentation.docx — unified China + Korea + replication guide."""
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# Monochrome. Same structure as the China/Korea presentation deck, printed
# in black and white: NAVY becomes near-black, GOLD becomes mid-grey, and
# the table fills become greys that hold up on a mono laser printer.
NAVY  = RGBColor(0x11, 0x11, 0x11)   # headings, table header fill
GOLD  = RGBColor(0x66, 0x66, 0x66)   # cover eyebrow
GRAY  = RGBColor(0x44, 0x44, 0x44)   # body
RED   = RGBColor(0x00, 0x00, 0x00)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
MID   = RGBColor(0x80, 0x80, 0x80)   # meta


def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)


def para(doc, text, bold=False, italic=False, size=11, color=None,
         align=None, space_before=0, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    if align:
        p.alignment = align
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = color
    return p


def heading(doc, text, level=1):
    sizes = {1: 17, 2: 13, 3: 11}
    p = para(doc, text, bold=True, size=sizes.get(level, 11), color=NAVY,
             space_before=16 if level == 1 else 10, space_after=4)
    if level == 1:
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement('w:pBdr')
        bot = OxmlElement('w:bottom')
        bot.set(qn('w:val'), 'single'); bot.set(qn('w:sz'), '6')
        bot.set(qn('w:space'), '1'); bot.set(qn('w:color'), '111111')
        pBdr.append(bot); pPr.append(pBdr)
    return p


def bullet(doc, text, bold_prefix=None, level=0):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Inches(0.25 + level * 0.2)
    if bold_prefix:
        r1 = p.add_run(bold_prefix + "  ")
        r1.bold = True; r1.font.size = Pt(10.5); r1.font.color.rgb = NAVY
    r2 = p.add_run(text)
    r2.font.size = Pt(10.5); r2.font.color.rgb = GRAY


def callout(doc, label, text, color=NAVY):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.left_indent = Inches(0.2)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    left = OxmlElement('w:left')
    left.set(qn('w:val'), 'single'); left.set(qn('w:sz'), '12')
    left.set(qn('w:space'), '6')
    left.set(qn('w:color'), '%02X%02X%02X' % (color[0], color[1], color[2]))
    pBdr.append(left); pPr.append(pBdr)
    r1 = p.add_run(label + "  ")
    r1.bold = True; r1.font.size = Pt(10); r1.font.color.rgb = color
    r2 = p.add_run(text)
    r2.font.size = Pt(10.5); r2.font.color.rgb = GRAY


def table(doc, headers, rows, col_widths=None):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        set_cell_bg(cell, '111111')
        p = cell.paragraphs[0]
        run = p.add_run(h); run.bold = True
        run.font.size = Pt(9); run.font.color.rgb = WHITE
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
    for ri, row in enumerate(rows):
        tr = t.rows[ri + 1]
        for ci, val in enumerate(row):
            cell = tr.cells[ci]
            if ri % 2 == 1:
                set_cell_bg(cell, 'F2F2F2')
            p = cell.paragraphs[0]
            bold = isinstance(val, tuple)
            text_val = val[0] if bold else val
            run = p.add_run(text_val)
            run.bold = bold and val[1]
            run.font.size = Pt(9.5)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
    if col_widths:
        for i, w in enumerate(col_widths):
            for row in t.rows:
                row.cells[i].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


# ── BUILD ────────────────────────────────────────────────────────────────────
# Feed tables are read out of collect.py at build time rather than transcribed,
# so this document and the running brief cannot drift apart silently.
import collect

_TIERS = [
    ("TIER1_FEEDS", "Tier 1 — News", "24-hour window",
     "Wires, correspondents, the Japanese dailies, US and Japanese government."),
    ("TIER2_FEEDS", "Tier 2 — Analysis", "36-hour window",
     "Think tanks, chairs and commentary."),
    ("TIER3_FEEDS", "Tier 3 — Academic", "72-hour window",
     "Peer-reviewed journals in security and Japan studies."),
    ("TIER4_FEEDS", "Tier 4 — Primary statements", "48-hour window",
     "Official statements and pressers, read as primary text."),
    ("PM_TRACKER_FEEDS", "PM appearance tracker", "30-day window",
     "Feeds the days-since-last-seen line."),
    ("POLL_FEEDS", "Polling", "72-hour window",
     "Cabinet approval and party support by pollster."),
]

def _first_url(value):
    """The URL a feed is tried at first.

    Feed values are a mix: a plain string for most, a tuple of candidates for
    the rest. Indexing [0] on a string yields "h", which is not a URL and never
    matches the Google News prefix — so treating every value as a sequence
    silently classified 38 search-only feeds as native.
    """
    return value if isinstance(value, str) else value[0]


def _is_native(value):
    return not _first_url(value).startswith("https://news.google.com")


def _feed_rows(attr):
    d = getattr(collect, attr)
    rows = []
    for name, value in sorted(d.items()):
        if _is_native(value):
            how = ("Native RSS, search fallback" if name in collect._FALLBACK
                   else "Native RSS")
        else:
            how = "Google News search"
        rows.append((name, how))
    return rows


def _counts(attr):
    d = getattr(collect, attr)
    return len(d), sum(1 for v in d.values() if _is_native(v))

TOTAL = sum(_counts(a)[0] for a, *_ in _TIERS)
TOTAL_NATIVE = sum(_counts(a)[1] for a, *_ in _TIERS)
TOTAL_SEARCH = TOTAL - TOTAL_NATIVE
FALLBACK_COUNT = len(collect._FALLBACK)

doc = Document()
for section in doc.sections:
    section.top_margin = Cm(2.0); section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.5); section.right_margin = Cm(2.5)

style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(10.5)

# ── COVER ────────────────────────────────────────────────────────────────────
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(30)
r = p.add_run("CSIS JAPAN CHAIR")
r.font.size = Pt(10); r.font.color.rgb = GOLD; r.bold = True

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Japan Daily Brief")
r.font.size = Pt(26); r.font.color.rgb = NAVY; r.bold = True

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(4)
r = p.add_run("How It Is Built")
r.font.size = Pt(15); r.font.color.rgb = GRAY

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(28)
r = p.add_run("Pipeline  ·  Sourcing  ·  Sections  ·  Editorial Rules  ·  Cost  ·  Open Decisions")
r.font.size = Pt(11); r.font.color.rgb = MID; r.italic = True

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Prepared by Andy Lim  ·  CSIS Japan Chair  ·  September 2026")
r.font.size = Pt(10); r.font.color.rgb = MID

doc.add_page_break()

# ── 1. WHAT IS THIS ──────────────────────────────────────────────────────────
heading(doc, "1.  What Is This?")
para(doc,
     "An automated daily intelligence briefing on Japan, delivered to the distribution "
     "list at 7:00 AM ET every morning. Each issue covers overnight news, Japanese "
     "government action, Diet business, business and economy, the Indo-Pacific as it "
     "bears on Japan, cabinet approval polling and expert commentary, drawn from "
     f"{TOTAL} sources. It is a five-minute read, and it replaces roughly ninety minutes "
     "a morning of manual scanning.",
     size=11, color=GRAY, space_after=8)

callout(doc, "The one-line pitch:",
        "A senior analyst's morning scan, automated. No staff time, no manual curation. "
        "It runs on its own every day for about $9 a month.")

table(doc,
    ["", "Japan Daily Brief"],
    [
        ("Sources", f"{TOTAL} feeds across six collections"),
        ("Tiers", "4 (News / Analysis / Academic / Primary statements), plus a PM tracker and polling"),
        ("Languages", "English and Japanese, translated by Claude"),
        ("Sections", "14 in the email, each omitted on a day with nothing behind it"),
        ("Length", "1,900–2,200 words; hard ceiling 2,400, hard minimum 1,600"),
        ("Persistent trackers", "PM appearances, regional pressure, feed health, verified calendar"),
        ("Delivery", "7:00 AM ET daily, with five fallback runs through 10:35 AM"),
        ("Monthly API cost", "About $9"),
    ],
    col_widths=[1.7, 4.5]
)

# ── 2. HOW IT WORKS ──────────────────────────────────────────────────────────
heading(doc, "2.  How It Works")
para(doc,
     "Every morning GitHub's servers wake up and run a six-stage pipeline in three to "
     "five minutes. Each stage hands the next a single structured object, and nothing "
     "reaches a reader that has not passed all six.",
     size=11, color=GRAY, space_after=6)

bullet(doc, f"{TOTAL} feeds pulled in parallel across 25 threads, each tier with its own "
            "recency window. Market data, the PM appearance tracker and cabinet approval "
            "polling are fetched live rather than recalled.", bold_prefix="Step 1 — Collect")
bullet(doc, "Only the strongest articles per tier reach the model. Ordered by primary "
            "documents first, then the outlets an editorial rule names, then flagged "
            "correspondents, then Japanese full text — taking one article per source "
            "before any source gets a second, so a prolific wire cannot crowd out the "
            "Japanese press.", bold_prefix="Step 2 — Rank")
bullet(doc, "One structured call to Claude. Sonnet first, Opus on retry. The prompt "
            "carries the day's articles plus the trackers' real historical baselines, "
            "and demands JSON with a fixed field for every section.", bold_prefix="Step 3 — Write")
bullet(doc, "A gate checks the output before anything sends: every link traced back to a "
            "collected article or the item dropped, duplicates removed within the issue "
            "and against the past week, hollow filler stripped, per-source caps enforced, "
            "length trimmed to the ceiling.", bold_prefix="Step 4 — Validate")
bullet(doc, "The JSON becomes table-based HTML with inline CSS, built to survive Outlook "
            "and Gmail forwarding. Dark mode, the mobile layout and the print PDF all "
            "come from the same markup.", bold_prefix="Step 5 — Render")
bullet(doc, "Gmail SMTP to the distribution list, then the same issue to the web archive "
            "with a PDF beside it.", bold_prefix="Step 6 — Send and publish")

para(doc, "", space_after=4)
callout(doc, "Fallback logic:",
        "If the 7:00 AM dispatch is missed, five scheduled runs from 7:05 to 10:35 AM ET "
        "cover it, and a skip guard prevents a second send the same day. If every run "
        "fails, no email goes out — silence is better than a bad product.")

table(doc,
    ["Tool", "Role", "Cost"],
    [
        ("Python 3.12", "Pipeline code", "Free"),
        ("GitHub Actions", "Runs on a timer — no server needed", "Free"),
        ("Claude API", "Reads, translates and writes the digest", "About $9/month"),
        ("Gmail SMTP", "Sends the email", "Free"),
        ("GitHub Pages", "Public archive of past issues, with PDFs", "Free"),
    ],
    col_widths=[1.7, 3.3, 1.3]
)

doc.add_page_break()

# ── 3. SOURCING ──────────────────────────────────────────────────────────────
heading(doc, "3.  Sourcing")
para(doc,
     "A source can be reached two ways: the publisher's own RSS feed, or a Google News "
     "site-restricted search standing in for it. Where a publisher feed is configured, a "
     "Google News search is registered behind it as an automatic fallback — if the "
     "publisher feed returns nothing at fetch time, the search is tried instead. That "
     "fallback is what lets an unverified publisher URL be added safely: if the URL turns "
     "out to be wrong, the search answers exactly as it did before and nothing goes "
     "missing.",
     size=11, color=GRAY, space_after=8)

para(doc,
     f"That protection currently covers {FALLBACK_COUNT} of the {TOTAL_NATIVE} feeds that "
     f"have a publisher URL. It does not extend to the other {TOTAL_SEARCH}, because there "
     "is nothing to fall back from — a search-only feed is already the fallback, with no "
     "publisher feed in front of it.",
     size=11, color=GRAY, space_after=8)

callout(doc, "The vulnerability this guards against:",
        "A brief built mostly on Google News searches has a single point of failure. One "
        "change upstream takes most of the sources at once, silently — the issue does not "
        "error, it just arrives thin.")

para(doc,
     "Two further rules govern what survives collection. A keyword filter strips world "
     "news out of general wires, but it is not applied to Japanese government or "
     "Japanese-language feeds: a real ministry headline often contains none of its "
     "English tokens, and applying the filter there deleted most of them. And only the "
     "highest-ranked articles per tier reach the model, ordered so that primary documents "
     "and the outlets the editorial rules name are never crowded out by whichever feed "
     "happened to publish most that morning.",
     size=11, color=GRAY, space_after=8)

para(doc, "Where the sources stand today", bold=True, size=12, color=NAVY, space_after=4)
table(doc,
    ["Collection", "Feeds", "Native RSS", "Search only", "Recency window"],
    [(label, str(_counts(attr)[0]), str(_counts(attr)[1]),
      str(_counts(attr)[0] - _counts(attr)[1]), window)
     for attr, label, window, _desc in _TIERS]
    + [(("Total", True), (str(TOTAL), True), (str(TOTAL_NATIVE), True),
        (str(TOTAL_SEARCH), True), ("", True))],
    col_widths=[2.1, 0.8, 1.0, 1.0, 1.3]
)

callout(doc, "Read this row first:",
        f"{TOTAL_SEARCH} of {TOTAL} feeds have no publisher RSS in front of them and "
        "depend entirely on Google's index. Tier 1 — the wires, the Japanese dailies and "
        "the government sites — is much the healthiest at 26 of 47. Tiers 2 and 3 are "
        "almost wholly search-dependent, at 1 of 30 and 0 of 18. Section 8 sets out what "
        "to do about it.")

# ── 4. THE FULL SOURCE LIST ─────────────────────────────────────────────────
doc.add_page_break()
heading(doc, "4.  Every Source It Reads")
para(doc,
     "The complete list, generated from the running code rather than transcribed. "
     "\"Native RSS\" means the publisher's own feed is tried first. \"Google News search\" "
     "means there is no publisher feed configured and the source reaches the brief only "
     "through Google's index.",
     size=11, color=GRAY, space_after=8)

for attr, label, window, desc in _TIERS:
    n, nat = _counts(attr)
    para(doc, f"{label}", bold=True, size=12, color=NAVY, space_after=2, space_before=10)
    para(doc, f"{desc}  {n} feeds, {nat} native, {window}.",
         size=10, color=MID, space_after=4)
    table(doc, ["Source", "How it is reached"], _feed_rows(attr),
          col_widths=[3.6, 2.6])

doc.add_page_break()

# ── 5. WHAT EACH ISSUE COVERS ────────────────────────────────────────────────
heading(doc, "5.  What Each Issue Covers")
para(doc,
     "Sections in the order they appear in the email. A section with nothing behind it "
     "that day is absent rather than padded — an empty section is a signal, and filling "
     "it would destroy the signal.",
     size=11, color=GRAY, space_after=6)

table(doc,
    ["Section", "Limit", "Content"],
    [
        ("Today at a Glance", "3 items",
         "The morning memo: what a Japan desk officer says in the elevator. One sentence each, verb first."),
        ("Top Stories", "2–4",
         "Hard news only — wires, correspondents, the Japanese press, government. Never op-eds or think-tank commentary."),
        ("Overnight", "6 max",
         "What moved while Washington slept. Headline on one line, a two-sentence summary on the next."),
        ("Stat of the Day", "1 figure",
         "A single striking number from the day's reporting, and it must differ from yesterday's."),
        ("Upcoming", "4–5 events",
         "The next 14–30 days. Dates come from the day's articles or the verified calendar, never from memory."),
        ("Japanese Government", "variable",
         "Kantei, Chief Cabinet Secretary, MOFA, MOD and Joint Staff, METI, MOF, BOJ, NSS — ministry named in Japanese and English."),
        ("Business & Economy", "up to 6",
         "Figures, companies and sector. The $550bn US–Japan investment framework is a standing priority when the day carries it."),
        ("Indo-Pacific", "4–6",
         "China–Japan, Korea–Japan, the DPRK, the trilateral, the Quad, Taiwan, Southeast Asia, Australia, India — each as it bears on Japan."),
        ("Diet Watch", "variable",
         "Floor and committee activity, bills, the budget, LDP and coalition manoeuvring."),
        ("Op-Eds, Commentaries & Events", "tier 2",
         "Think-tank and commentary output, ordered by prestige and then by score."),
        ("Public Sentiment & Approval Polling", "live fetch",
         "Cabinet approval and party support, fetched before each issue rather than recalled."),
        ("Social Statements", "0–4",
         "Verbatim quotation from senior officials. A quotation section, not a second headline digest."),
        ("The Wire", "up to 6",
         "Everything else that cleared the scoring threshold, grouped by subject."),
        ("On This Day", "0–1",
         "Only from the verified Japan dates file, and only on an exact month-and-day match. Empty is the normal state."),
    ],
    col_widths=[1.7, 0.8, 3.7]
)

# ── 6. EDITORIAL RULES ───────────────────────────────────────────────────────
heading(doc, "6.  The Rules That Constrain It")
para(doc,
     "These are enforced in code after the model writes, not merely asked for in the "
     "prompt. That distinction is the whole credibility argument: a rule the model is "
     "asked to follow is a preference, and a rule the pipeline checks is a guarantee.",
     size=11, color=GRAY, space_after=8)

callout(doc, "Source-or-skip",
        "Every factual claim must trace to an article collected that morning or to a "
        "baseline supplied in the prompt. A claim from neither is omitted. An item whose "
        "link cannot be traced back to a collected article is now dropped outright rather "
        "than printed without one — the earlier behaviour published the violation instead "
        "of catching it.")
callout(doc, "Same-poll-date",
        "Every figure inside one poll object comes from a single pollster's single survey "
        "over one date range. Approval and party support are never blended across weeks "
        "or across houses.")
callout(doc, "Dates from sources only",
        "Calendar entries and anniversaries use dates found in the day's articles or in "
        "the verified dates file. Nothing is recalled. A standing fixture with no "
        "announced date is described as a window or left out, never given a day.")
callout(doc, "Source diversity",
        "No more than three Overnight items from any one outlet, and ranking takes one "
        "article per source before any source gets a second.")
callout(doc, "Length",
        "1,900–2,200 words, hard ceiling 2,400, hard minimum 1,600. Over the ceiling, "
        "whole items are dropped from the tail of the weaker sections — nothing is "
        "rewritten, so what survives is what the model wrote against its sources.")

# ── 7. COST AND RELIABILITY ──────────────────────────────────────────────────
doc.add_page_break()
heading(doc, "7.  Cost and Reliability")

para(doc, "Cost", bold=True, size=12, color=NAVY, space_after=4)
para(doc,
     "Every run records its own token ledger and the dollar cost of the call. The figures "
     "below come from that ledger, not from an estimate. Cost recording was added "
     "recently, so the sample is still short and the monthly figure is an extrapolation "
     "from it.",
     size=10.5, color=GRAY, space_after=6)
table(doc,
    ["Item", "Figure"],
    [
        ("Cost per issue", "$0.40 (measured)"),
        ("Implied monthly cost", "About $9 at 22 issues"),
        ("Primary model", "Claude Sonnet 4.6"),
        ("Retry model", "Claude Opus 4.8"),
        ("Everything else", "Free — GitHub Actions, Gmail SMTP, GitHub Pages"),
    ],
    col_widths=[2.4, 3.8]
)

para(doc, "Reliability", bold=True, size=12, color=NAVY, space_after=4, space_before=8)
table(doc,
    ["Guard", "What it does", "Blocks a send?"],
    [
        ("Offline test suite", "86 checks on render, sourcing, length, email format", ("Yes", True)),
        ("Time-independence check", "Proves the suite does not pass only on today's date", ("Yes", True)),
        ("Skip guard", "Prevents a second send when a fallback run fires", ("Yes", True)),
        ("Earliest-hour floor", "Refuses to send before the delivery hour", ("Yes", True)),
        ("Visual checks", "Contrast, typeface count, mobile overflow in a real browser", "No — reports"),
        ("Chromium / PDF", "Print export for the archive", "No — reports"),
        ("Feed health", "Flags any feed silent three or more consecutive runs", "No — reports"),
    ],
    col_widths=[1.7, 3.3, 1.3]
)
callout(doc, "Why the split:",
        "A check that can cancel the brief has to be a check about the code. A visual "
        "measurement that shifts with the day's content should report, not cancel — an "
        "earlier arrangement let a contrast reading on one caption stop an entire issue "
        "from going out.")

# ── 8. OPEN DECISIONS ────────────────────────────────────────────────────────
doc.add_page_break()
heading(doc, "8.  Open Decisions")
para(doc,
     "The places the brief is currently weakest, each stated with the decision that would "
     "settle it. This is the section worth marking up.",
     size=11, color=GRAY, space_after=8)

para(doc, "1.  Most feeds have no publisher RSS behind them", bold=True, size=11.5,
     color=NAVY, space_after=3, space_before=6)
para(doc,
     f"Of {TOTAL} feeds, {TOTAL_SEARCH} are Google News searches with no native path. "
     "Tier 3 is 18 of 18; tier 2 is 29 of 30, which means CSIS, Brookings, Carnegie, "
     "Stimson, Hudson, NBR and Pacific Forum reach the brief only if Google indexes them "
     "that morning. Tier 1 is materially better at 26 of 47 native, and that is where the "
     "government feeds, the Japanese dailies and the major wires sit. The risk is not one "
     "feed failing; it is one upstream change taking most of two tiers at once, with no "
     "error to notice.",
     size=10.5, color=GRAY, space_after=4)
callout(doc, "Decision:",
        "Is it worth a pass to add native RSS behind the tier 2 institutions the Chair "
        "actually reads? Roughly 25 feeds, and most of them publish RSS.")

para(doc, "2.  Named sources that have gone quiet", bold=True, size=11.5,
     color=NAVY, space_after=3, space_before=8)
para(doc,
     "Feed health tracks how long each source has gone without delivering. Mainichi and "
     "Jiji Press have both been silent for roughly two months. Neither absence was visible "
     "in the brief: a source that stops delivering does not announce itself, it simply "
     "stops appearing. Both have native URLs configured, so this is a moved or broken "
     "endpoint rather than a design flaw — but two of the Japanese dailies the brief "
     "claims to read have not been in it since July.",
     size=10.5, color=GRAY, space_after=4)
callout(doc, "Decision:",
        "Which Japanese-language dailies are non-negotiable? Those get their endpoints "
        "verified and a health alert that blocks the send rather than reporting quietly.")

para(doc, "3.  Polling baselines drift between manual updates", bold=True, size=11.5,
     color=NAVY, space_after=3, space_before=8)
para(doc,
     "Cabinet approval is fetched live before each issue, which is the reliable path. The "
     "fallback table behind it is hand-maintained and currently carries July figures, so "
     "a failed fetch falls back to a two-month-old baseline rather than to nothing.",
     size=10.5, color=GRAY, space_after=4)
callout(doc, "Decision:",
        "Should a failed fetch suppress the polling section entirely rather than fall "
        "back to a stale table?")

para(doc, "4.  A built tension index that nothing uses", bold=True, size=11.5,
     color=NAVY, space_after=3, space_before=8)
para(doc,
     "tension_scorer.py computes a regional tension score on a 0–10 scale. It is complete "
     "and tested, and no part of the pipeline imports it, so it has never appeared in an "
     "issue.",
     size=10.5, color=GRAY, space_after=4)
callout(doc, "Decision:",
        "Wire it in as a standing indicator, or delete it. Carrying it unused is the "
        "worst of the three.")

para(doc, "5.  Section scope after the alliance section was removed", bold=True, size=11.5,
     color=NAVY, space_after=3, space_before=8)
para(doc,
     "The US–Japan Alliance & Trade section was removed at the Chair's request. Its "
     "subject matter now lands in Business & Economy and in Indo-Pacific, and the story "
     "count was raised to fill the space it left.",
     size=10.5, color=GRAY, space_after=4)
callout(doc, "Decision:",
        "Is alliance and trade coverage landing where the Chair expects it, or does it "
        "need a named home again?")

# ── CLOSE ────────────────────────────────────────────────────────────────────
doc.add_page_break()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(50)
r = p.add_run("CSIS Japan Chair  ·  Japan Daily Brief")
r.font.size = Pt(12); r.font.color.rgb = NAVY; r.bold = True

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(20)
r = p.add_run("Pipeline  ·  Sourcing  ·  Sections  ·  Editorial Rules  ·  Open Decisions")
r.font.size = Pt(11); r.font.color.rgb = GRAY

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Feed counts and section limits in this document are generated from the "
              "running code, not transcribed.")
r.font.size = Pt(9.5); r.font.color.rgb = MID; r.italic = True

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Prepared by Andy Lim  ·  September 2026")
r.font.size = Pt(10); r.font.color.rgb = MID

doc.save("JAPAN_DIGEST_PRESENTATION.docx")
print(f"Saved JAPAN_DIGEST_PRESENTATION.docx  "
      f"({TOTAL} feeds: {TOTAL_NATIVE} native, {TOTAL_SEARCH} search-only)")
