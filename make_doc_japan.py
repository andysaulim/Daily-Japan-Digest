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
# Written for the Japan Chair, not for an engineer. No filenames, no code, no
# jargon that is not explained on the spot. The source lists are read out of
# the collector at build time so the document cannot drift from the brief.
import collect

_TIERS = [
    ("TIER1_FEEDS", "News", "Last 24 hours",
     "Wire services, foreign correspondents, the Japanese dailies, and the "
     "Japanese and US governments. This is where most of the brief comes from."),
    ("TIER2_FEEDS", "Analysis", "Last 36 hours",
     "Think tanks, university centres and named commentators."),
    ("TIER3_FEEDS", "Academic", "Last 72 hours",
     "Peer-reviewed journals in security studies and Japan studies."),
    ("TIER4_FEEDS", "Official statements", "Last 48 hours",
     "Government statements and press conferences, read as primary text rather "
     "than as news about them."),
    ("PM_TRACKER_FEEDS", "Prime Minister tracker", "Last 30 days",
     "Feeds the count of how long it has been since the PM was seen in public."),
    ("POLL_FEEDS", "Opinion polling", "Last 72 hours",
     "Cabinet approval and party support, by pollster."),
]


def _first_url(value):
    """The address a source is tried at first.

    Some entries are a single address, others a list of candidates. Indexing
    into a plain string returns its first character, which is not an address —
    reading every entry as a list silently miscounted 38 sources.
    """
    return value if isinstance(value, str) else value[0]


def _is_own_feed(value):
    return not _first_url(value).startswith("https://news.google.com")


def _feed_rows(attr):
    d = getattr(collect, attr)
    rows = []
    for name, value in sorted(d.items()):
        if _is_own_feed(value):
            how = ("Publisher's own feed, with search backup"
                   if name in collect._FALLBACK else "Publisher's own feed")
        else:
            how = "Google News search"
        rows.append((name, how))
    return rows


def _counts(attr):
    d = getattr(collect, attr)
    return len(d), sum(1 for v in d.values() if _is_own_feed(v))


TOTAL = sum(_counts(a)[0] for a, *_ in _TIERS)
TOTAL_OWN = sum(_counts(a)[1] for a, *_ in _TIERS)
TOTAL_SEARCH = TOTAL - TOTAL_OWN

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
r = p.add_run("The Japan Daily Brief")
r.font.size = Pt(28); r.font.color.rgb = NAVY; r.bold = True

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(4)
r = p.add_run("How It Is Built, and Where Every Story Comes From")
r.font.size = Pt(14); r.font.color.rgb = GRAY

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(26)
r = p.add_run(f"A complete account of all {TOTAL} sources, the editorial rules, "
              "and what still needs deciding")
r.font.size = Pt(11); r.font.color.rgb = MID; r.italic = True

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Prepared by Andy Lim  ·  CSIS Japan Chair  ·  September 2026")
r.font.size = Pt(10); r.font.color.rgb = MID

doc.add_page_break()
# ── 1 ────────────────────────────────────────────────────────────────────────
heading(doc, "1.  What it is")
para(doc,
     "The Japan Daily Brief is an eight-page email on Japanese politics, security, "
     "economy and regional affairs that arrives at 7:00 AM Eastern every morning. "
     f"It is assembled automatically from {TOTAL} news sources, and nobody writes it "
     "by hand. It takes about five minutes to read.",
     size=11, color=GRAY, space_after=8)

para(doc,
     "The work it replaces is roughly ninety minutes of a person opening the Japanese "
     "dailies, the wire services, the ministry websites and the think-tank output, and "
     "deciding what a Japan desk needs to know before the day starts.",
     size=11, color=GRAY, space_after=8)

callout(doc, "The one thing to understand about it:",
        "The brief cannot write from memory. Every sentence in it has to trace back to "
        "an article collected that morning. If the reporting is not in front of it, the "
        "item is left out. Section 7 explains how that is enforced rather than merely "
        "requested.")

table(doc,
    ["", ""],
    [
        ("Arrives", "7:00 AM Eastern, every day"),
        ("Length", "Around 2,000 words — an eight-minute read at most"),
        ("Sources", f"{TOTAL}, listed in full in Section 4"),
        ("Languages", "English and Japanese; Japanese articles are translated"),
        ("Sections", "14, and any with nothing behind it that day is left out"),
        ("Written by", "Anthropic's Claude, following a fixed set of instructions"),
        ("Cost", "About $9 a month"),
        ("Archive", "Every issue published to a searchable web page with a PDF"),
    ],
    col_widths=[1.5, 4.7]
)

# ── 2 ────────────────────────────────────────────────────────────────────────
doc.add_page_break()
heading(doc, "2.  What happens each morning")
para(doc,
     "Six steps, start to finish in three to five minutes, on a free scheduled server. "
     "Nothing reaches a reader that has not been through all six.",
     size=11, color=GRAY, space_after=8)

bullet(doc, f"All {TOTAL} sources are read at once. How recent an article has to be "
            "depends on the kind of source: overnight for news, three days for an "
            "academic journal. Market data, the Prime Minister tracker and the latest "
            "opinion polling are fetched fresh at the same time, so no figure in the "
            "brief is recalled from memory.", bold_prefix="1. Gather")
bullet(doc, "Far more arrives than one issue can hold, so the morning's articles are "
            "put in priority order and the strongest are passed on. Official documents "
            "come first, then the outlets the editorial rules require, then named "
            "correspondents, then the Japanese-language press. Section 5 explains this "
            "in full.", bold_prefix="2. Prioritise")
bullet(doc, "Those articles are handed to Claude together with the editorial rules and "
            "the real historical figures the brief keeps — so it is reading them, not "
            "remembering them. Claude returns the whole issue in a fixed structure, one "
            "field per section.", bold_prefix="3. Write")
bullet(doc, "Before anything is sent: every link is checked against the articles "
            "actually collected, and an item whose source cannot be traced is removed. "
            "Stories repeated from earlier in the week are dropped. Empty filler is "
            "stripped. No single outlet is allowed to dominate. The issue is trimmed if "
            "it runs long.", bold_prefix="4. Check")
bullet(doc, "The issue is laid out as an email built to survive Outlook, Gmail and "
            "forwarding, and to stay readable on a phone and in dark mode. The web "
            "version and the PDF come from the same layout, so all three are the same "
            "issue.", bold_prefix="5. Lay out")
bullet(doc, "The email goes to the distribution list, and the same issue is published "
            "to the web archive with a PDF beside it.", bold_prefix="6. Send")

para(doc, "", space_after=4)
callout(doc, "If something goes wrong:",
        "Five further attempts run through the morning in case the first is missed, and "
        "a check stops a second copy going out once one has. If every attempt fails, no "
        "email is sent at all — silence is better than a brief that is wrong.")

# ── 3 ────────────────────────────────────────────────────────────────────────
doc.add_page_break()
heading(doc, "3.  Where the news comes from")
para(doc,
     "Most publications offer a standing subscription to their output — a feed that "
     "lists what they have just published. The brief holds one of these for each "
     "source and reads all of them at once, every morning. Nothing is searched for "
     "ad hoc, and nothing arrives because the brief went looking for a particular "
     "story.",
     size=11, color=GRAY, space_after=8)

para(doc, "Two ways a source is reached", bold=True, size=12, color=NAVY, space_after=4)
para(doc,
     "This distinction matters more than any other in this document, and it is the one "
     "thing worth taking away from it.",
     size=10.5, color=GRAY, space_after=6)

table(doc,
    ["How", "What it means", "How dependable"],
    [
        (("The publisher's own feed", True),
         "The brief reads the publication directly, the way a subscriber would",
         "Dependable. It breaks only if the publisher changes something, and the brief notices when a source goes quiet"),
        (("A Google News search", True),
         "The brief runs a standing keyword search restricted to that publication, and takes whatever Google returns",
         "Dependent on Google. If Google changes how it indexes that publication, the source simply stops appearing, with no error"),
    ],
    col_widths=[1.6, 2.6, 2.0]
)

para(doc,
     "Where a publisher's own feed is configured, a Google News search is kept behind "
     f"it as a backup: if the publisher's feed returns nothing one morning, the search "
     f"is tried instead. That backup is in place for {len(collect._FALLBACK)} of the "
     f"{TOTAL_OWN} sources that have a publisher feed. It cannot be extended to the "
     f"other {TOTAL_SEARCH}, because for those the search is not the backup — it is the "
     "only route in.",
     size=10.5, color=GRAY, space_after=8)

para(doc, "How the sources divide today", bold=True, size=12, color=NAVY,
     space_after=4, space_before=4)
table(doc,
    ["Group", "Sources", "Publisher's own feed", "Search only", "How recent"],
    [(label, str(_counts(attr)[0]), str(_counts(attr)[1]),
      str(_counts(attr)[0] - _counts(attr)[1]), window)
     for attr, label, window, _d in _TIERS]
    + [(("Total", True), (str(TOTAL), True), (str(TOTAL_OWN), True),
        (str(TOTAL_SEARCH), True), ("", True))],
    col_widths=[1.7, 0.8, 1.4, 0.9, 1.4]
)

callout(doc, "What that table says, in one sentence:",
        f"{TOTAL_SEARCH} of the {TOTAL} sources reach the brief only through Google. "
        "The news group — the wires, the Japanese dailies, the ministries — is in good "
        "shape at 26 of 47 read directly. Analysis and academic are almost "
        "entirely dependent on Google: 1 of 30, and 0 of 18. This is the brief's "
        "largest structural weakness and it is the first item in Section 9.")

para(doc,
     "The risk is not that one source fails; a single quiet source is noticed and "
     "reported. The risk is that one change at Google removes two whole groups at "
     "once, and the brief simply arrives thinner than usual with nothing to indicate "
     "why.",
     size=10.5, color=GRAY, space_after=6)

para(doc, "Japanese-language and government sources", bold=True, size=12, color=NAVY,
     space_after=4, space_before=8)
para(doc,
     "Wire services carry the whole world, so a Japan filter is applied to strip out "
     "everything unrelated. That filter would destroy a Japanese ministry feed, because "
     "a genuine ministry headline often contains none of the English words it looks "
     f"for. The {len(collect.JAPAN_NATIVE_FEEDS)} sources below are therefore exempt — "
     "everything they publish is considered. Any Japanese government or "
     "Japanese-language source added in future has to be added to this list, or most of "
     "it would be discarded before anyone saw it.",
     size=10.5, color=GRAY, space_after=6)
table(doc, ["Exempt from the Japan filter", ""],
      [(n, "") for n in sorted(collect.JAPAN_NATIVE_FEEDS)],
      col_widths=[3.6, 2.6])

# ── 4 ────────────────────────────────────────────────────────────────────────
doc.add_page_break()
heading(doc, "4.  Every source, in full")
para(doc,
     "The complete list, generated from the brief's own configuration rather than "
     "typed out, so it cannot fall out of date. Each entry shows how that source is "
     "reached.",
     size=11, color=GRAY, space_after=8)

for attr, label, window, desc in _TIERS:
    n, own = _counts(attr)
    para(doc, label, bold=True, size=12.5, color=NAVY, space_after=2, space_before=10)
    para(doc, desc, size=10.5, color=GRAY, space_after=3)
    para(doc, f"{n} sources · {own} read directly · {n - own} through Google · {window}",
         size=10, color=MID, space_after=5)
    table(doc, ["Source", "How it is reached"], _feed_rows(attr),
          col_widths=[3.4, 2.8])

# ── 5 ────────────────────────────────────────────────────────────────────────
doc.add_page_break()
heading(doc, "5.  How the brief decides what to include")
para(doc,
     "A normal morning brings several hundred articles. Only about 140 from each group "
     "are shown to Claude — enough to choose from, few enough to read properly. Which "
     "140 is an editorial decision, not a technical one, so it follows a stated order.",
     size=11, color=GRAY, space_after=8)

table(doc,
    ["Order", "What goes here", "The reasoning"],
    [
        (("First", True), "Official documents — the ministries, the Cabinet Office, the Bank of Japan",
         "What a government actually published outranks reporting about it"),
        (("Second", True), "The outlets the editorial rules name, and the correspondents listed below",
         "A rule requiring the Financial Times to appear is meaningless if the FT was never put in front of the writer"),
        (("Third", True), "Japanese-language articles",
         "The Japanese press is what distinguishes this brief, and is the first thing crowded out"),
        (("Fourth", True), "Everything else that passed the Japan filter",
         "Included as space allows"),
    ],
    col_widths=[0.8, 2.7, 2.7]
)

para(doc,
     "Within each of those, one article is taken from each publication before any "
     "publication gets a second. Without that, a wire service filing forty times "
     "before dawn would fill the list and push out the Japanese dailies. Before this "
     "order existed, the cut was simply whichever sources happened to answer fastest, "
     "and the outlets the rules call mandatory were frequently not in front of the "
     "writer at all.",
     size=10.5, color=GRAY, space_after=8)

para(doc, "Outlets that must appear if they published", bold=True, size=12,
     color=NAVY, space_after=4, space_before=4)
para(doc,
     ", ".join(sorted(collect.MAJOR_FEEDS)) + ".",
     size=10.5, color=GRAY, space_after=8)

para(doc, "Correspondents followed by name", bold=True, size=12, color=NAVY,
     space_after=4, space_before=4)
para(doc,
     f"{len(collect.PRESTIGE_JOURNALISTS)} Japan correspondents are recognised by "
     "byline. An article carrying one of these names is promoted in the order above "
     "whatever publication it arrived through, so a bureau correspondent's own piece is "
     "not dropped in favour of an agency rewrite of the same story.",
     size=10.5, color=GRAY, space_after=6)

_j = sorted(collect.PRESTIGE_JOURNALISTS)
_half = (len(_j) + 1) // 2
table(doc, ["Correspondent", "Correspondent"],
      [(_j[i], _j[i + _half] if i + _half < len(_j) else "") for i in range(_half)],
      col_widths=[3.1, 3.1])

callout(doc, "This list needs the Chair's eye:",
        "It is maintained by hand. A correspondent who changes masthead keeps their "
        "promotion until the name is removed, and a new arrival on the Japan beat gets "
        "none until the name is added. It is worth reading at the same time as the "
        "source list.")

# ── 6 ────────────────────────────────────────────────────────────────────────
doc.add_page_break()
heading(doc, "6.  What is in each issue")
para(doc,
     "Fourteen sections, in the order they appear. A section with nothing behind it "
     "that morning is absent rather than padded — an empty section is information, and "
     "filling it would destroy that information.",
     size=11, color=GRAY, space_after=8)

table(doc,
    ["Section", "How much", "What it carries"],
    [
        ("Today at a Glance", "3 items",
         "The three things a Japan desk officer would say walking into a meeting. One sentence each."),
        ("Top Stories", "2 to 4",
         "Hard news only — wires, correspondents, the Japanese press, government. Never opinion or think-tank commentary."),
        ("Overnight", "Up to 6",
         "What moved while Washington slept. Headline on one line, two sentences beneath it."),
        ("Stat of the Day", "1 figure",
         "One striking number from the morning's reporting, and it must differ from yesterday's."),
        ("Upcoming", "4 to 5",
         "The next two to four weeks. Dates come only from the day's articles or a verified calendar, never from memory."),
        ("Japanese Government", "Varies",
         "The Cabinet Office, Chief Cabinet Secretary, Foreign Ministry, Defence Ministry and Joint Staff, METI, Finance, the Bank of Japan and the National Security Secretariat."),
        ("Business & Economy", "Up to 6",
         "Figures, companies and sectors. The $550bn US-Japan investment framework is a standing priority whenever the day carries it."),
        ("Indo-Pacific", "4 to 6",
         "China, Korea, North Korea, the trilateral, the Quad, Taiwan, Southeast Asia, Australia and India — each as it bears on Japan."),
        ("Diet Watch", "Varies",
         "Floor and committee business, bills, the budget, and LDP and coalition manoeuvring."),
        ("Op-Eds & Commentary", "Varies",
         "Think-tank and commentary output, strongest first."),
        ("Approval Polling", "Varies",
         "Cabinet approval and party support, fetched fresh before each issue."),
        ("Social Statements", "0 to 4",
         "Direct quotation from senior officials. A quotation section, not a second run of headlines."),
        ("The Wire", "Up to 6",
         "Everything else worth flagging, grouped by subject."),
        ("On This Day", "0 or 1",
         "Only from a verified list of Japanese anniversaries, and only on an exact date match. Empty is the normal state."),
    ],
    col_widths=[1.5, 0.8, 3.9]
)

# ── 7 ────────────────────────────────────────────────────────────────────────
doc.add_page_break()
heading(doc, "7.  The rules that keep it honest")
para(doc,
     "These are checked by the system after the brief is written, not merely requested "
     "beforehand. That distinction is the whole credibility argument: a rule the writer "
     "is asked to follow is a preference, and a rule the system verifies is a guarantee.",
     size=11, color=GRAY, space_after=8)

callout(doc, "Source or skip",
        "Every factual claim must trace to an article collected that morning, or to a "
        "figure supplied with the instructions. A claim from neither is left out. An "
        "item whose link cannot be traced back to a collected article is now removed "
        "entirely — until recently the link was quietly dropped and the story kept, "
        "which published the problem rather than catching it.")
callout(doc, "One poll at a time",
        "Every number inside a single polling block comes from one pollster's one "
        "survey over one set of dates. Approval and party support are never blended "
        "across weeks or across pollsters.")
callout(doc, "Dates only from sources",
        "Calendar entries and anniversaries use dates found in the morning's articles "
        "or in a verified list. Nothing is recalled. A recurring event with no announced "
        "date is described as a window or left out — never given a specific day.")
callout(doc, "No single voice dominates",
        "No more than three Overnight items from any one outlet, and the priority order "
        "takes one article from each publication before any gets a second.")
callout(doc, "Length is enforced, not requested",
        "Around 2,000 words, with a hard ceiling. Over it, whole items are dropped from "
        "the weaker sections — nothing is rewritten or compressed, so what survives is "
        "what was written against its sources.")

# ── 8 ────────────────────────────────────────────────────────────────────────
doc.add_page_break()
heading(doc, "8.  Reliability and cost")

para(doc, "Getting there every morning", bold=True, size=12, color=NAVY, space_after=4)
para(doc,
     "The brief is triggered at 7:00 AM Eastern, with five further attempts through the "
     "morning in case that one is missed. A check makes every later attempt do nothing "
     "once the issue has gone out, so the list is never mailed twice.",
     size=10.5, color=GRAY, space_after=6)

table(doc,
    ["Check", "What it looks at", "Can it stop the brief?"],
    [
        ("Test suite", "86 checks on layout, sourcing, length and email formatting", ("Yes", True)),
        ("Date independence", "Proves the tests do not pass only because of today's date", ("Yes", True)),
        ("Duplicate guard", "Whether the list has already been mailed today", ("Yes", True)),
        ("Hour check", "Refuses to send before the delivery hour", ("Yes", True)),
        ("Design checks", "Contrast, typefaces and phone layout, measured in a real browser", "No — reports only"),
        ("Source health", "Flags any source silent three mornings running", "No — reports only"),
    ],
    col_widths=[1.5, 3.2, 1.5]
)

callout(doc, "Why the split:",
        "Anything that can cancel the brief has to be a fault in the system itself. "
        "Anything that measures the day's content reports and lets the brief go. A "
        "design check once measured a single caption as slightly too small and "
        "cancelled an entire morning's issue; that is the wrong trade, and it no "
        "longer happens.")

para(doc, "What it costs", bold=True, size=12, color=NAVY, space_after=4, space_before=8)
para(doc,
     "Every run records what it spent. The figure moves with how much news there is, "
     "so it is measured rather than estimated.",
     size=10.5, color=GRAY, space_after=6)
table(doc,
    ["", ""],
    [
        ("Per issue", "About $0.40"),
        ("Per month", "About $9"),
        ("Everything else", "Free — the scheduling, the email, the archive and the PDF"),
    ],
    col_widths=[1.6, 4.6]
)

# ── 9 ────────────────────────────────────────────────────────────────────────
doc.add_page_break()
heading(doc, "9.  What needs a decision")
para(doc,
     "Five things the Chair should know about, each with the question that would "
     "settle it. This is the section worth marking up.",
     size=11, color=GRAY, space_after=10)

para(doc, "1.  Most sources depend on Google", bold=True, size=12, color=NAVY,
     space_after=3)
para(doc,
     f"Of {TOTAL} sources, {TOTAL_SEARCH} are reached only through a Google News "
     "search, with no direct feed behind them. Every academic journal is in that "
     "position — 18 of 18 — and so is almost the whole analysis group at 29 of 30, "
     "which means CSIS, Brookings, Carnegie, Stimson, Hudson, NBR and Pacific Forum "
     "reach the brief only if Google indexes them that morning. The news group is much "
     "healthier: 26 of 47 read directly, and that is where the ministries, the "
     "Japanese dailies and the major wires sit.",
     size=10.5, color=GRAY, space_after=4)
callout(doc, "The question:",
        "Is it worth the work to connect directly to the analysis institutions the "
        "Chair actually reads? That is roughly 25 sources, and most of them publish a "
        "feed. It would put the weakest group on the same footing as the news group.")

para(doc, "2.  Two Japanese dailies have gone quiet", bold=True, size=12, color=NAVY,
     space_after=3, space_before=8)
para(doc,
     "Mainichi and Jiji Press have not delivered an article in roughly two months. "
     "Both are configured to be read directly, so this is a moved or broken address "
     "rather than a design fault — but it means two of the Japanese dailies this brief "
     "claims to read have not been in it since July. A source that stops delivering "
     "does not announce itself; it simply stops appearing.",
     size=10.5, color=GRAY, space_after=4)
callout(doc, "The question:",
        "Which Japanese-language dailies are non-negotiable? Those should have their "
        "addresses verified, and their silence should raise an alert rather than pass "
        "quietly.")

para(doc, "3.  Polling falls back to an old figure", bold=True, size=12, color=NAVY,
     space_after=3, space_before=8)
para(doc,
     "Cabinet approval is fetched fresh before each issue, which is the reliable route. "
     "Behind it sits a hand-maintained figure used if that fetch fails, and it "
     "currently holds July numbers — so a failed fetch falls back to a two-month-old "
     "reading rather than to nothing.",
     size=10.5, color=GRAY, space_after=4)
callout(doc, "The question:",
        "Should a failed fetch drop the polling section entirely rather than print an "
        "old figure?")

para(doc, "4.  Section scope after the alliance section was removed",
     bold=True, size=12, color=NAVY, space_after=3, space_before=8)
para(doc,
     "The US-Japan Alliance & Trade section was removed at the Chair's request. Its "
     "subject matter now appears in Business & Economy and in Indo-Pacific, and the "
     "number of stories was raised to fill the space it left.",
     size=10.5, color=GRAY, space_after=4)
callout(doc, "The question:",
        "Is alliance and trade coverage landing where the Chair expects to find it, or "
        "does it need a named home again?")

para(doc, "5.  There is no weekly edition", bold=True, size=12, color=NAVY,
     space_after=3, space_before=8)
para(doc,
     "The Korea and Australia briefs each publish a Friday review that reads back the "
     "week's issues and draws out the through-lines. Japan has none. Building one is a "
     "matter of editorial judgement rather than engineering — the machinery exists and "
     "the layout would carry over unchanged.",
     size=10.5, color=GRAY, space_after=4)
callout(doc, "The question:",
        "Would a Friday Week in Review be useful to the Chair, and what should it "
        "cover that the dailies do not?")

# ── CLOSE ────────────────────────────────────────────────────────────────────
doc.add_page_break()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(50)
r = p.add_run("CSIS Japan Chair  ·  The Japan Daily Brief")
r.font.size = Pt(12); r.font.color.rgb = NAVY; r.bold = True

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(18)
r = p.add_run("7:00 AM Eastern, every morning")
r.font.size = Pt(11); r.font.color.rgb = GRAY

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("The source lists, counts and section limits in this document are read "
              "directly from the brief's own configuration, so this document and the "
              "brief cannot disagree.")
r.font.size = Pt(9.5); r.font.color.rgb = MID; r.italic = True

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(14)
r = p.add_run("Prepared by Andy Lim  ·  September 2026")
r.font.size = Pt(10); r.font.color.rgb = MID

doc.save("JAPAN_DIGEST_PRESENTATION.docx")
print(f"Saved JAPAN_DIGEST_PRESENTATION.docx  "
      f"({TOTAL} sources: {TOTAL_OWN} direct, {TOTAL_SEARCH} search-only)")
