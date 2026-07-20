"""
Japan Daily Brief — HTML Renderer
CSIS Japan Chair

Mirrors the Daily-Korea/China-Digest visual language (ported from the
Korea brief's Q3-2026 renderer):
- Navy #1B2A4A header + Hinomaru red #BC002D accents (flag disc mark)
- System font stack; monospace for machine-measured numbers/dates
- Shadowed, rounded story cards; floating card wrapper on a #F2F3F5 ground
- Dark Regional Pressure Watch panel (repurposed dark section)
- Table-based layout, inline CSS, with a proper <style> head: CSS reset,
  full dark-mode support (prefers-color-scheme), mobile + tablet
  breakpoints, and Outlook (MSO) conditionals
"""

import re as _re
from datetime import datetime, timezone
from urllib.parse import urlparse as _urlparse


# ── Palette ───────────────────────────────────────────────────────────────
NAVY = "#1B2A4A"
HINOMARU_RED = "#BC002D"          # official Japanese flag crimson (JIS)
HINOMARU_RED_SOFT = "rgba(188,0,45,0.5)"
# On-dark (navy panel) readable variants — dark red/text is unreadable on near-black
PANEL_NAVY   = "#0E1C33"          # Regional Pressure Watch ground (lighter than near-black)
RED_ON_NAVY  = "#F2718A"          # Hinomaru red lightened for legibility on navy
SLATE_LABEL  = "#9DB2CE"          # muted slate-blue label on navy
TEXT_ON_NAVY = "#E4EAF2"          # near-white body text on navy

# Observing Japan cabinet-approval poll aggregator (Govella review)
OBSERVING_JAPAN_POLLS = "https://observingjapan.substack.com/p/tracking-the-japanese-governments-423"


def _hinomaru(size: int = 16) -> str:
    """Inline Hinomaru (Japanese flag) red-disc mark."""
    return (f'<span style="display:inline-block;width:{size}px;height:{size}px;'
            f'border-radius:50%;background:{HINOMARU_RED};vertical-align:middle;'
            f'margin-right:9px;"></span>')


def _clean_src(raw: str) -> str:
    if not raw:
        return raw
    stripped = raw.strip()
    if _re.match(r'^https?://', stripped) and ' ' not in stripped:
        try:
            host = _urlparse(stripped).hostname or ""
            if host.startswith("www."):
                host = host[4:]
            return host if host else raw
        except Exception:
            return raw
    cleaned = _re.sub(r'https?://\S+', '', raw).strip()
    cleaned = _re.sub(r' +', ' ', cleaned)
    return cleaned if cleaned else raw


def _str(val) -> str:
    if isinstance(val, list):
        return val[0] if val else ""
    return val if isinstance(val, str) else str(val) if val is not None else ""


def _esc(text) -> str:
    if text is None or text == "":
        return ""
    text = str(text)
    if text == "None":
        return ""
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace('"', "&quot;"))


def _social_badge(badge_class: str) -> str:
    return {"sb-p": "#1B2A4A", "sb-r": "#C0392B", "sb-s": "#1B2A4A"}.get(badge_class, "#1B2A4A")


def _arrow(val) -> str:
    try:
        val = float(val)
    except (TypeError, ValueError):
        return '<span style="color:#7F8C8D;">—</span>'
    if val > 0:
        return f'<span style="color:#27AE60;">&#9650; +{val:.2f}%</span>'
    if val < 0:
        return f'<span style="color:#C0392B;">&#9660; {val:.2f}%</span>'
    return '<span style="color:#7F8C8D;">— flat</span>'


def _cds_arrow(val) -> str:
    try:
        val = float(val)
    except (TypeError, ValueError):
        return '<span style="color:#7F8C8D;">—</span>'
    if val > 0:
        return f'<span style="color:#C0392B;">&#9650; +{val:.1f} bps</span>'
    if val < 0:
        return f'<span style="color:#27AE60;">&#9660; {val:.1f} bps</span>'
    return '<span style="color:#7F8C8D;">— flat</span>'


def _link_or_text(text: str, url: str,
                  style: str = "color:#1B2A4A;text-decoration:underline;") -> str:
    if url and url != "#" and url.startswith("http"):
        return f'<a href="{_esc(url)}" style="{style}">{text}</a>'
    return text


_SEC = 'style="padding:20px 32px;border-bottom:1px solid #EBEBEB;" class="sec"'
_SEC_ALERT = 'style="padding:20px 32px;border-top:3px solid #C0392B;border-bottom:1px solid #EBEBEB;" class="sec"'

def _sec_label(label: str, color: str = NAVY, rule: str = HINOMARU_RED) -> str:
    """Section label — navy small-caps over a Hinomaru-red rule, no pill."""
    return (f'<div style="font-size:10px;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:2px;color:{color};font-family:Arial,sans-serif;'
            f'margin-bottom:14px;padding-bottom:8px;border-bottom:2px solid {rule};">'
            f'{label}</div>')


def _word_count(d: dict) -> int:
    """Count words in ALL visible text — headlines, bodies, notes, every section."""
    w = 0

    def _w(s):
        return len(str(s).split()) if s else 0

    # Header
    w += _w(d.get("re_line"))

    # Morning memo
    for mi in (d.get("morning_memo") or []):
        w += _w(mi) if isinstance(mi, str) else _w(mi.get("text", "")) if isinstance(mi, dict) else 0

    # Δ Since Yesterday
    for item in ((d.get("delta_since_yesterday") or {}).get("items") or []):
        w += _w(item)

    # Top stories
    for s in (d.get("top_stories") or []):
        for f in ("headline", "body", "so_what", "pattern_note", "src_line"):
            w += _w(s.get(f, ""))

    # Lists with headline + body_text
    for key in ("overnight_items", "also_today", "business_economy", "indo_pacific"):
        for it in (d.get(key) or []):
            w += _w(it.get("headline", ""))
            w += _w(it.get("body_text", ""))

    # Op-eds + academic
    for o in (d.get("opeds_today") or []):
        for f in ("title", "summary", "central_argument", "policy_so_what", "authors"):
            w += _w(o.get(f, ""))
    for a in (d.get("academic_today") or []):
        for f in ("title", "summary", "authors"):
            w += _w(a.get(f, ""))

    # Japanese government / Diet Watch / Diet sessions / Personnel
    for g in (d.get("prc_government") or []):
        for f in ("action", "detail", "official", "ministry"):
            w += _w(g.get(f, ""))
    for c in (d.get("congressional_watch") or []):
        for f in ("committee", "action", "detail"):
            w += _w(c.get(f, ""))
    for n in (d.get("npc_politburo") or []):
        for f in ("body", "action", "detail"):
            w += _w(n.get(f, ""))
    for p in (d.get("personnel_changes") or []):
        for f in ("name", "position", "detail", "predecessor"):
            w += _w(p.get(f, ""))

    # Calendar + on this day
    for c in (d.get("calendar_watch") or []):
        for f in ("headline", "detail"):
            w += _w(c.get(f, ""))
    for o in (d.get("on_this_day") or []):
        for f in ("event", "relevance"):
            w += _w(o.get(f, ""))

    # Key stat
    ks = d.get("key_stat") or {}
    for f in ("label", "context", "source"):
        w += _w(ks.get(f, ""))

    # Regional Pressure Watch (key: xinhua_delta)
    xd = d.get("xinhua_delta") or {}
    for f in ("bottom_line", "china_signal", "dprk_signal", "russia_signal",
              "senkaku_status", "output_volume", "pm_activity"):
        w += _w(xd.get(f, ""))
    for q in (xd.get("key_quotes") or []):
        if isinstance(q, dict):
            w += _w(q.get("quote", ""))
            w += _w(q.get("source_article", ""))

    # Social statements
    for s in (d.get("social_statements") or []):
        for f in ("who", "handle_context", "platform_date", "quote_text", "analyst_note"):
            w += _w(s.get(f, ""))

    # Public sentiment (approval polling — array or legacy single object)
    ps = d.get("public_sentiment") or {}
    _polls = ps.get("approval_polls")
    if not _polls:
        _legacy = ps.get("approval_polling")
        _polls = [_legacy] if isinstance(_legacy, dict) else []
    for ap in _polls:
        if isinstance(ap, dict):
            for f in ("pollster", "poll_date", "cabinet_approval", "cabinet_disapproval"):
                w += _w(ap.get(f, ""))
    for p in (ps.get("party_support") or []):
        w += _w(p.get("party", ""))
    w += _w(ps.get("discourse_flag", ""))

    return w


def _chapter(label: str) -> str:
    """Chapter divider — dark navy band with Hinomaru-red rule, white letterspaced label."""
    return f"""
<div style="padding:12px 32px;background:#1B2A4A;text-align:center;" class="sec">
<div style="height:1px;background:rgba(188,0,45,0.5);margin-bottom:10px;"></div>
<span style="font-size:9px;font-family:Arial,sans-serif;color:rgba(255,255,255,0.65);text-transform:uppercase;letter-spacing:5px;font-weight:700;">{label}</span>
<div style="height:1px;background:rgba(188,0,45,0.5);margin-top:10px;"></div>
</div>"""


def render_html(digest: dict) -> str:
    from zoneinfo import ZoneInfo
    now = datetime.now(ZoneInfo("America/New_York"))
    date_str = now.strftime("%A, %B %-d, %Y")
    gen_time = now.strftime("%-I:%M %p ET")
    re_line = _esc(digest.get("re_line", ""))
    wc = _word_count(digest)
    read_min = max(1, round(wc / 250))
    web_url = digest.get("web_url", "")
    # Chapter buckets
    sections_pre = []       # View-in-browser, header, markets, Δ Since Yesterday
    sections_today = []     # Morning Memo, Top Stories, Overnight Flash, Key Stat
    sections_analysis = []  # Regional Pressure Watch, Expert Analysts, Public Sentiment, Social Statements
    sections_trackers = []  # Security Watch, Japanese Gov, US-Japan Alliance & Trade, Diet Watch
    sections_wire = []      # Business, Indo-Pacific, Also Today, On This Day
    sections_post = []      # Footer

    # 0. View in browser
    if web_url:
        sections_pre.append(f"""
<div style="background:#F0F0F0;padding:6px 32px;text-align:center;font-size:11px;color:#888;" class="sec">
Email not rendering? <a href="{_esc(web_url)}" style="color:{HINOMARU_RED};text-decoration:none;">Read online &#8594;</a>
</div>""")

    # 1. Header
    sections_pre.append(f"""
<div style="background:#1B2A4A;color:#fff;padding:18px 32px 14px;" class="sec">
<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
<td style="vertical-align:top;">
<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:#BC002D;font-family:Arial,sans-serif;margin-bottom:6px;">CSIS Japan Chair</div>
<h1 style="margin:0 0 4px 0;font-size:28px;font-weight:700;font-family:Georgia,serif;color:#fff;letter-spacing:0.3px;">{_hinomaru(16)}Japan Daily Brief</h1>
<div style="font-size:16px;font-weight:400;color:rgba(255,255,255,0.85);font-family:Georgia,serif;">{_esc(date_str)}</div>
</td>
<td style="vertical-align:top;text-align:right;">
<div style="font-size:10px;text-transform:uppercase;letter-spacing:1px;color:rgba(255,255,255,0.55);margin-bottom:3px;font-family:'Courier New',Courier,monospace;">{gen_time}</div>
<div style="font-size:10px;color:rgba(255,255,255,0.4);font-family:'Courier New',Courier,monospace;">{wc:,} words &middot; {read_min} min read</div>
</td>
</tr></table>
{"<div style='margin-top:12px;padding-top:12px;border-top:1px solid #BC002D;font-size:13px;color:rgba(255,255,255,0.9);font-family:Georgia,serif;'><strong style='color:#BC002D;font-family:Arial,sans-serif;font-size:11px;letter-spacing:1px;'>RE:</strong>&nbsp; " + re_line + "</div>" if re_line else ""}
</div>""")

    # 2. Market strip (3 rows)
    m = digest.get("market_indicators") or {}
    if m:
        nikkei = m.get("nikkei") or {}
        topix = m.get("topix") or {}
        usd_jpy = m.get("usd_jpy") or {}
        eur_jpy = m.get("eur_jpy") or {}
        brent = m.get("brent") or {}
        jgb = m.get("jgb_10y") or {}
        cds = m.get("japan_cds") or {}
        boj = m.get("boj_rate") or {}
        gdp = m.get("gdp_yoy") or {}
        _topix_val = str(topix.get("value", "—"))
        _has_topix = _topix_val not in ("—", "", "None")
        _asof = now.strftime("%b %-d")
        _nikkei_cell = f"""<div style="font-size:9px;text-transform:uppercase;letter-spacing:1.2px;opacity:0.55;">Nikkei 225</div>
<div style="font-size:20px;font-weight:700;margin:2px 0;">{_esc(str(nikkei.get("value", "—")))}</div>
<div style="font-size:11px;">{_arrow(nikkei.get("change_pct", 0))}</div>
<div style="font-size:9px;opacity:0.4;margin-top:2px;">as of {_asof}</div>"""
        _usdjpy_cell = f"""<div style="font-size:9px;text-transform:uppercase;letter-spacing:1.2px;opacity:0.55;">USD/JPY</div>
<div style="font-size:20px;font-weight:700;margin:2px 0;">{_esc(str(usd_jpy.get("value", "—")))}</div>
<div style="font-size:11px;">{_arrow(usd_jpy.get("change_pct", 0))}</div>
<div style="font-size:9px;opacity:0.4;margin-top:2px;">as of {_asof}</div>"""
        if _has_topix:
            _topix_cell = f"""<div style="font-size:9px;text-transform:uppercase;letter-spacing:1.2px;opacity:0.55;">TOPIX</div>
<div style="font-size:20px;font-weight:700;margin:2px 0;">{_esc(_topix_val)}</div>
<div style="font-size:11px;">{_arrow(topix.get("change_pct", 0))}</div>
<div style="font-size:9px;opacity:0.4;margin-top:2px;">as of {_asof}</div>"""
            _top_row = (f'<td width="33%" align="center" style="padding:12px 8px 10px;">{_nikkei_cell}</td>'
                        f'<td width="34%" align="center" style="padding:12px 8px 10px;border-left:1px solid rgba(255,255,255,0.12);border-right:1px solid rgba(255,255,255,0.12);">{_topix_cell}</td>'
                        f'<td width="33%" align="center" style="padding:12px 8px 10px;">{_usdjpy_cell}</td>')
        else:
            # TOPIX unavailable from data sources — show Nikkei | USD/JPY two-across, no broken cell.
            _top_row = (f'<td width="50%" align="center" style="padding:12px 8px 10px;">{_nikkei_cell}</td>'
                        f'<td width="50%" align="center" style="padding:12px 8px 10px;border-left:1px solid rgba(255,255,255,0.12);">{_usdjpy_cell}</td>')
        sections_pre.append(f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" class="mkt-table" style="background:#1B2A4A;color:#fff;border-bottom:1px solid rgba(255,255,255,0.1);">
<tr>
{_top_row}
</tr>
</table>
<table width="100%" cellpadding="0" cellspacing="0" border="0" class="mkt-table" style="background:#162340;color:#fff;border-bottom:1px solid rgba(255,255,255,0.08);">
<tr>
<td width="25%" align="center" style="padding:8px;">
<div style="font-size:10px;text-transform:uppercase;letter-spacing:1px;opacity:0.6;">EUR/JPY</div>
<div style="font-size:15px;font-weight:700;">{_esc(str(eur_jpy.get("value", "—")))}</div>
<div style="font-size:10px;">{_arrow(eur_jpy.get("change_pct", 0))}</div>
</td>
<td width="25%" align="center" style="padding:8px;border-left:1px solid rgba(255,255,255,0.1);">
<div style="font-size:10px;text-transform:uppercase;letter-spacing:1px;opacity:0.6;">Brent</div>
<div style="font-size:15px;font-weight:700;">${_esc(str(brent.get("value", "—")))}</div>
<div style="font-size:10px;">{_arrow(brent.get("change_pct", 0))}</div>
</td>
<td width="25%" align="center" style="padding:8px;border-left:1px solid rgba(255,255,255,0.1);">
<div style="font-size:10px;text-transform:uppercase;letter-spacing:1px;opacity:0.6;">10Y JGB</div>
<div style="font-size:15px;font-weight:700;">{_esc(str(jgb.get("value", "—")))}</div>
<div style="font-size:10px;opacity:0.5;">yield</div>
</td>
<td width="25%" align="center" style="padding:8px;border-left:1px solid rgba(255,255,255,0.1);">
<div style="font-size:10px;text-transform:uppercase;letter-spacing:1px;opacity:0.6;">Japan 5Y CDS</div>
<div style="font-size:15px;font-weight:700;">{_esc(str(cds.get("value", "—")))} bps</div>
<div style="font-size:10px;">{_cds_arrow(cds.get("change_bps", 0))}</div>
</td>
</tr>
</table>
<table width="100%" cellpadding="0" cellspacing="0" border="0" class="mkt-table" style="background:#0F1B30;color:#fff;border-bottom:1px solid rgba(255,255,255,0.08);">
<tr>
<td width="50%" align="center" style="padding:8px;">
<div style="font-size:10px;text-transform:uppercase;letter-spacing:1px;opacity:0.6;">BOJ Policy Rate</div>
<div style="font-size:15px;font-weight:700;">{_esc(str(boj.get("value", "—")))}</div>
<div style="font-size:10px;opacity:0.6;">{_esc(str(boj.get("last_change", "")))}</div>
</td>
<td width="50%" align="center" style="padding:8px;border-left:1px solid rgba(255,255,255,0.1);">
<div style="font-size:10px;text-transform:uppercase;letter-spacing:1px;opacity:0.6;">GDP (annualized)</div>
<div style="font-size:15px;font-weight:700;">{_esc(str(gdp.get("value", "—")))}</div>
<div style="font-size:10px;opacity:0.6;">{_esc(str(gdp.get("source", "Cabinet Office")))}{" · " + _esc(str(gdp.get("period", ""))) if gdp.get("period") else ""}</div>
</td>
</tr>
</table>""")

    # 2c. Δ Since Yesterday Bar
    delta = digest.get("delta_since_yesterday") or {}
    items = delta.get("items") or []
    if items:
        chip_html = ""
        for it in items[:6]:
            chip_html += (f'<span style="display:inline-block;margin:0 4px 4px 0;'
                          f'padding:3px 10px;background:rgba(255,255,255,0.06);'
                          f'border:1px solid rgba(255,255,255,0.12);border-radius:14px;'
                          f'font-size:11px;color:rgba(255,255,255,0.85);'
                          f'font-family:Arial,sans-serif;">{_esc(it)}</span>')
        sections_pre.append(f"""
<div style="padding:10px 32px;background:#0a0f1e;color:#fff;border-bottom:1px solid rgba(255,255,255,0.08);" class="sec">
<span style="font-size:10px;text-transform:uppercase;letter-spacing:1.2px;color:rgba(255,255,255,0.55);margin-right:8px;vertical-align:middle;">Δ Since Yesterday</span>
{chip_html}
</div>""")

    # 3. Morning Memo
    memo = digest.get("morning_memo") or []
    if memo:
        memo_html = ""
        for idx, mi in enumerate(memo[:3], 1):
            t = _esc(mi) if isinstance(mi, str) else _esc(mi.get("text", "") if isinstance(mi, dict) else str(mi or ""))
            memo_html += f"""<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:10px;">
<tr>
<td width="28" style="vertical-align:top;padding-top:1px;">
<div style="width:22px;height:22px;border-radius:50%;background:#1B2A4A;color:#fff;font-size:11px;font-weight:700;text-align:center;line-height:22px;font-family:Arial,sans-serif;">{idx}</div>
</td>
<td style="vertical-align:top;padding-left:8px;">
<div style="font-size:14px;line-height:1.5;color:#222;font-family:Georgia,serif;">{t}</div>
</td>
</tr>
</table>"""
        sections_today.append(f"""
<div style="padding:20px 32px;border-bottom:1px solid #EBEBEB;" class="sec">
<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:#BC002D;font-family:Arial,sans-serif;margin-bottom:14px;padding-bottom:8px;border-bottom:2px solid #BC002D;">Today at a Glance</div>
{memo_html}
</div>""")

    # 4. Top Stories
    stories = digest.get("top_stories") or []
    if stories:
        sh = ""
        for s in stories:
            cat = _esc(_str(s.get("category_tag", s.get("category", ""))))
            h = _esc(s.get("headline", ""))
            b_raw = s.get("body", "") or ""
            b = _esc(b_raw) if b_raw.strip() and b_raw.strip() != s.get("headline", "").strip() else ""
            sw = _esc(s.get("so_what", ""))
            pn = _esc(s.get("pattern_note", ""))
            sl = _esc(_clean_src(s.get("src_line", s.get("source", ""))))
            url = s.get("url", "")
            sh += f"""
<div class="story-card" style="margin-bottom:14px;padding:14px 16px;background:#fff;border-radius:3px;border-left:4px solid #1B2A4A;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
<div style="font-size:9px;text-transform:uppercase;letter-spacing:1.5px;color:#888;font-weight:700;margin-bottom:6px;">{cat}</div>
<h3 style="margin:0 0 8px 0;font-size:16px;line-height:1.4;color:#1B2A4A;font-family:Georgia,serif;font-weight:700;">{_link_or_text(h, url, style="color:#1B2A4A;text-decoration:none;")}</h3>
{"<p style='margin:0 0 10px 0;font-size:13px;line-height:1.55;color:#444;'>" + b + "</p>" if b else ""}
{"<p style='margin:0 0 6px 0;font-size:12px;line-height:1.5;color:#555;font-style:italic;'><strong style='color:#1B2A4A;font-style:normal;'>So what:</strong> " + _link_or_text(sw, url, style="color:#555;text-decoration:underline;") + "</p>" if sw else ""}
{"<p style='margin:0 0 6px 0;font-size:12px;line-height:1.5;color:#777;font-style:italic;'><strong style='color:#555;font-style:normal;'>Pattern:</strong> " + pn + "</p>" if pn else ""}
<div style="font-size:10px;color:#aaa;margin-top:6px;text-transform:uppercase;letter-spacing:0.5px;">{sl}</div>
</div>"""
        sections_today.append(f'<div {_SEC}>{_sec_label("Top Stories")}{sh}</div>')

    # 4b. Overnight Flash
    overnight = digest.get("overnight_items") or []
    if overnight:
        cat_colors = {}  # single navy accent for all overnight bars
        fh = ""
        for it in overnight:
            cat_raw = _str(it.get("category", ""))
            cat = _esc(cat_raw)
            h = _esc(it.get("headline", ""))
            b = _esc(it.get("body_text", ""))
            src = _esc(_clean_src(it.get("source", "")))
            url = it.get("url", "")
            bar = cat_colors.get(cat_raw, "#1B2A4A")
            fh += f"""
<div style="margin-bottom:10px;padding-left:12px;border-left:3px solid {bar};">
<div style="font-size:9px;color:#888;text-transform:uppercase;letter-spacing:1px;font-weight:600;margin-bottom:2px;">{cat} &middot; {src}</div>
<div style="font-size:13px;font-weight:600;color:#1B2A4A;">{_link_or_text(h, url)}</div>
<div style="font-size:12px;line-height:1.4;color:#555;">{b}</div>
</div>"""
        sections_today.append(f'<div {_SEC_ALERT}>{_sec_label("&#9889; Overnight Flash", color="#C0392B", rule="#C0392B")}{fh}</div>')

    # 5. Key Stat
    stat = digest.get("key_stat") or {}
    if stat and stat.get("number"):
        sections_today.append(f"""
<div style="padding:12px 32px;background:#1B2A4A;color:#fff;border-bottom:1px solid #E0E0E0;text-align:center;" class="sec">
<div style="font-size:10px;text-transform:uppercase;letter-spacing:1.5px;opacity:0.6;margin-bottom:2px;">Stat of the Day</div>
<div class="key-stat-num" style="font-size:32px;font-weight:700;font-family:Georgia,serif;">{_esc(str(stat.get("number", "")))}</div>
<div style="font-size:12px;opacity:0.85;margin-top:2px;">{_esc(stat.get("label", ""))}</div>
<div style="font-size:11px;opacity:0.65;margin-top:4px;font-style:italic;">{_esc(stat.get("context", ""))}</div>
{"<div style='font-size:10px;opacity:0.45;margin-top:4px;'>Source: " + _esc(stat.get("source", "")) + "</div>" if stat.get("source") else ""}
</div>""")

    # 6. Regional Pressure Watch — DARK SECTION (key: xinhua_delta)
    xd = digest.get("xinhua_delta") or {}
    if xd:
        def _signal_row(label, color, text):
            if not text:
                return ""
            return (f'<div style="margin-bottom:12px;padding-left:12px;border-left:3px solid {color};">'
                    f'<div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;'
                    f'color:{color};font-weight:700;margin-bottom:3px;">{label}</div>'
                    f'<div style="font-size:13px;line-height:1.6;color:{TEXT_ON_NAVY};">'
                    f'{_esc(text)}</div></div>')

        # Single accent for the whole panel — labels differentiate, color doesn't
        signals_html = ""
        signals_html += _signal_row("China", RED_ON_NAVY, xd.get("china_signal"))
        signals_html += _signal_row("North Korea", RED_ON_NAVY, xd.get("dprk_signal"))
        signals_html += _signal_row("Russia", RED_ON_NAVY, xd.get("russia_signal"))

        senkaku = _esc(xd.get("senkaku_status", ""))
        senkaku_html = (f'<div style="margin:6px 0 12px;padding:9px 13px;background:rgba(255,255,255,0.07);'
                        f'border-radius:4px;font-size:13px;line-height:1.55;color:{TEXT_ON_NAVY};">'
                        f'<strong style="color:{RED_ON_NAVY};">Senkaku / ECS:</strong> {senkaku}</div>'
                        if senkaku else "")

        # PM appearance line
        pm_appeared = xd.get("pm_appearance_today")
        pm_days = xd.get("pm_days_since_last_appearance")
        pm_activity = _esc(xd.get("pm_activity", ""))
        pm_html = ""
        if pm_appeared is not None or pm_days is not None:
            pm_status = "PM appeared today" if pm_appeared else "No confirmed PM appearance today"
            days_str = (f" · {pm_days} day(s) since last confirmed appearance"
                        if isinstance(pm_days, int) else "")
            pm_html = (f'<div style="margin-bottom:10px;font-size:13px;color:{TEXT_ON_NAVY};">'
                       f'<strong style="color:{RED_ON_NAVY};">PM Watch:</strong> {_esc(pm_status)}{_esc(days_str)}'
                       f'{(" — " + pm_activity) if pm_activity else ""}</div>')

        # Key quotes
        quotes_html = ""
        for q in (xd.get("key_quotes") or [])[:2]:
            if isinstance(q, dict) and q.get("quote"):
                spk = _esc(q.get("speaker", ""))
                src = _esc(q.get("source_article", ""))
                meta = " &middot; ".join(x for x in (spk, src) if x)
                qtext = _esc(q.get("quote", ""))
                meta_html = (f'<div style="font-style:normal;font-size:11px;color:{SLATE_LABEL};'
                             f'margin-top:4px;">{meta}</div>') if meta else ""
                quotes_html += (f'<blockquote style="margin:8px 0;padding:9px 13px;'
                                f'background:rgba(255,255,255,0.07);border-left:3px solid {RED_ON_NAVY};'
                                f'font-style:italic;font-size:13px;line-height:1.55;'
                                f'color:{TEXT_ON_NAVY};">&ldquo;{qtext}&rdquo;'
                                f'{meta_html}</blockquote>')

        bottom = _esc(xd.get("bottom_line", ""))
        vol = _esc(xd.get("output_volume", ""))
        watch = xd.get("watch_flag")
        watch_badge = ('<span style="display:inline-block;padding:2px 8px;border-radius:3px;'
                       'font-size:9px;font-weight:700;color:#fff;background:#C0392B;'
                       'letter-spacing:0.5px;margin-left:8px;">WATCH</span>') if watch else ""

        sections_analysis.append(f"""
<div style="padding:20px 32px;background:{PANEL_NAVY};color:{TEXT_ON_NAVY};border-top:3px solid #BC002D;border-bottom:1px solid rgba(255,255,255,0.1);" class="sec watch-dark">
<div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:{RED_ON_NAVY};font-family:Arial,sans-serif;margin-bottom:14px;padding-bottom:8px;border-bottom:2px solid rgba(242,113,138,0.55);">Regional Pressure Watch{watch_badge}</div>
{("<div style='font-size:11px;color:" + SLATE_LABEL + ";margin-top:-8px;margin-bottom:12px;'>" + vol + "</div>") if vol else ""}
{pm_html}
{signals_html if signals_html else "<div style='font-size:13px;color:" + SLATE_LABEL + ";'>No notable adversary activity flagged today.</div>"}
{senkaku_html}
{quotes_html}
{("<div style='margin-top:12px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.15);font-size:14px;line-height:1.55;color:#FFFFFF;'><strong style='color:" + RED_ON_NAVY + ";'>Bottom line:</strong> " + bottom + "</div>") if bottom else ""}
</div>""")

    # 8. Japanese Government (gov cards + personnel + Diet sessions + calendar)
    prc_gov = digest.get("prc_government") or []
    personnel = digest.get("personnel_changes") or []
    npc = digest.get("npc_politburo") or []
    calendar = digest.get("calendar_watch") or []
    if prc_gov or personnel or npc or calendar:
        gov_rows_html = ""
        for it in prc_gov:
            mn = _esc(it.get("ministry", ""))
            mjp = _esc(it.get("ministry_jp", ""))
            act = _esc(it.get("action", ""))
            det = _esc(it.get("detail", ""))
            url = it.get("url", "")
            lbl = _esc(it.get("source_label", ""))
            off = _esc(it.get("official", ""))
            hdr_parts = []
            if mjp:
                hdr_parts.append(f'<span style="font-size:11px;color:#666;">{mjp}</span>')
            if mn:
                hdr_parts.append(f'<span style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.6px;">{mn}</span>')
            if off:
                hdr_parts.append(f'<span style="font-size:11px;color:#999;font-style:italic;">{off}</span>')
            hdr = ' <span style="color:#ccc;">·</span> '.join(hdr_parts)
            slink = ""
            if url and url != "#" and url.startswith("http"):
                sl = lbl if lbl else mn.lower()
                slink = f'<div style="margin-top:6px;font-size:11px;color:#888;">→ <a href="{_esc(url)}" style="color:#888;text-decoration:none;">{_esc(sl)} ↗</a></div>'
            elif lbl:
                slink = f'<div style="margin-top:6px;font-size:11px;color:#888;">→ {_esc(lbl)}</div>'
            gov_rows_html += f"""
<div style="margin-bottom:12px;padding:12px 14px;border-left:3px solid #1B2A4A;border-bottom:1px solid #F0F0F0;">
<div style="margin-bottom:6px;">{hdr}</div>
<div style="font-size:14px;font-weight:700;color:#1B2A4A;line-height:1.4;margin-bottom:5px;">{act}</div>
<div style="font-size:12px;line-height:1.55;color:#555;">{det}</div>
{slink}
</div>"""
        gov_grid = gov_rows_html if prc_gov else ""

        pers_html = ""
        if personnel:
            ac = {}  # single accent — the action word carries the meaning, not the color
            pi = ""
            for p in personnel:
                pos = _esc(p.get("position", ""))
                nm = _esc(p.get("name", ""))
                a = p.get("action", "appointed")
                det = _esc(p.get("detail", ""))
                pred = _esc(p.get("predecessor", "")) if p.get("predecessor") else ""
                ac_c = ac.get(a, "#1B2A4A")
                bg = f'<span style="display:inline-block;padding:1px 6px;border-radius:3px;font-size:10px;font-weight:600;color:#fff;background:{ac_c};text-transform:uppercase;margin-left:6px;">{_esc(a)}</span>'
                pl = f'<div style="font-size:11px;color:#888;margin-top:2px;">Succeeds: {pred}</div>' if pred else ""
                pi += f"""<div style="margin-bottom:10px;padding-left:12px;border-left:3px solid {ac_c};">
<div style="font-size:13px;font-weight:600;color:#1B2A4A;">{nm}{bg}</div>
<div style="font-size:12px;color:#555;">{pos}</div>
<div style="font-size:12px;line-height:1.4;color:#555;">{det}</div>
{pl}
</div>"""
            pers_html = f"""<div style="margin-top:16px;">
<div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:#2C3E50;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #E8E8E8;">Personnel Changes</div>
{pi}
</div>"""

        npc_html = ""
        if npc:
            ni = ""
            for n in npc:
                body = _esc(n.get("body", ""))
                act = _esc(n.get("action", ""))
                det = _esc(n.get("detail", ""))
                url = n.get("url", "")
                ni += f"""<div style="margin-bottom:8px;padding-left:12px;border-left:3px solid #7F8C8D;">
<div style="font-size:11px;color:#7F8C8D;font-weight:600;text-transform:uppercase;">{body}</div>
<div style="font-size:13px;font-weight:600;color:#1B2A4A;">{_link_or_text(act, url)}</div>
<div style="font-size:12px;line-height:1.4;color:#555;">{det}</div>
</div>"""
            npc_html = f"""<div style="margin-top:16px;">
<div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:#7F8C8D;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #E8E8E8;">Diet Sessions / LDP</div>
{ni}
</div>"""

        cal_html = ""
        if calendar:
            ci = ""
            for c in calendar:
                cm = _esc(c.get("month", ""))
                cd = _esc(str(c.get("day", "")))
                ch = _esc(c.get("headline", ""))
                cdet = _esc(c.get("detail", ""))
                ci += f"""<table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-bottom:1px solid #E8E8E8;">
<tr>
<td width="50" style="padding:10px 10px 10px 0;text-align:center;vertical-align:top;">
<div style="font-size:10px;text-transform:uppercase;color:#888;letter-spacing:0.5px;">{cm}</div>
<div style="font-size:18px;font-weight:300;color:#1B2A4A;line-height:1.2;">{cd}</div>
</td>
<td style="padding:10px 0;vertical-align:top;">
<div style="font-size:13px;font-weight:600;color:#1B2A4A;margin-bottom:2px;">{ch}</div>
<div style="font-size:12px;line-height:1.4;color:#555;">{cdet}</div>
</td>
</tr>
</table>"""
            cal_html = f"""<div style="margin-top:20px;">
<div style="padding:8px 0;border-bottom:1px solid #1B2A4A;margin-bottom:4px;">
<span style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:#1B2A4A;">Upcoming</span>
</div>
{ci}
</div>"""

        ds = _esc(str(digest.get("digest_date", "")))
        sections_trackers.append(f"""
<div {_SEC}>
{_sec_label("Japanese Government")}
<div style="font-size:10px;color:#aaa;text-transform:uppercase;letter-spacing:1px;margin-top:-10px;margin-bottom:14px;">Kantei · Cabinet · MOFA · MOD · METI · MOF · BOJ{(" · " + ds) if ds else ""}</div>
{gov_grid}{pers_html}{npc_html}{cal_html}
</div>""")

    # 9. US–Japan Alliance & Trade
    trade = digest.get("us_china_trade") or {}
    if trade:
        body = ""
        tt = trade.get("tariff_tracker") or {}
        if tt:
            h_auto = _esc(str(tt.get("headline_auto_rate", "")))
            s122 = _esc(str(tt.get("section_122_surcharge", "")))
            deal = _esc(str(tt.get("trade_deal_status", "")))
            lc = _esc(str(tt.get("last_change", "")))
            nt = _esc(str(tt.get("next_trigger", "")))
            s301 = _esc(str(tt.get("section_301_watch", "") or ""))
            invf = _esc(str(tt.get("investment_framework", "") or ""))
            s232 = tt.get("section_232_rates", {})
            # Headline numbers → clean navy metric strip (readable, one accent)
            strip_cells = [c for c in (("Autos · 2025 deal", h_auto), ("Section 122 surcharge", s122)) if c[1]]
            strip_html = ""
            if strip_cells:
                w = 100 // len(strip_cells)
                tds = ""
                for i, (lab, val) in enumerate(strip_cells):
                    bl = "border-left:1px solid rgba(255,255,255,0.12);" if i else ""
                    tds += (f'<td width="{w}%" align="center" style="padding:12px 10px;{bl}">'
                            f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:1px;color:{SLATE_LABEL};margin-bottom:4px;">{lab}</div>'
                            f'<div style="font-size:18px;font-weight:700;color:#fff;font-family:\'Courier New\',Courier,monospace;">{val}</div></td>')
                strip_html = (f'<table class="mkt-table" width="100%" cellpadding="0" cellspacing="0" border="0" '
                              f'style="background:{NAVY};border-radius:4px;margin-bottom:10px;"><tr>{tds}</tr></table>')
            # Section 232 rates — navy label, single red accent on the value
            sr = ""
            for sec, rate in s232.items():
                sr += (f'<tr style="border-bottom:1px solid #EEE;">'
                       f'<td style="padding:5px 6px 5px 0;font-size:12px;font-weight:600;color:{NAVY};">{_esc(str(sec).title())}</td>'
                       f'<td style="padding:5px 6px;font-size:14px;font-weight:700;color:{HINOMARU_RED};text-align:center;">{_esc(str(rate))}</td>'
                       f'<td style="padding:5px 6px;font-size:10px;color:#999;text-transform:uppercase;">Section 232</td></tr>')
            s232_html = (f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:6px;">{sr}</table>') if sr else ""
            il = (f'<div style="margin-top:6px;font-size:12px;line-height:1.5;color:#333;">'
                  f'<strong style="color:{NAVY};">Investment framework:</strong> {invf}</div>') if invf else ""
            s3l = (f'<div style="margin-top:6px;font-size:12px;line-height:1.5;color:#333;">'
                   f'<span style="display:inline-block;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:700;letter-spacing:0.5px;color:#fff;background:{HINOMARU_RED};margin-right:6px;">PROPOSED</span>'
                   f'<strong style="color:{NAVY};">Section 301 watch:</strong> {s301}</div>') if s301 else ""
            meta_parts = [x for x in ((("Deal: " + deal) if deal else ""),
                                      (("Next: " + nt) if nt else ""), lc) if x]
            meta_line = (f'<div style="margin-top:10px;padding-top:8px;border-top:1px solid #EEE;font-size:11px;color:#888;">'
                         + " &middot; ".join(meta_parts) + "</div>") if meta_parts else ""
            body += f"""<div class="tariff-box" style="margin-bottom:16px;padding:14px;background:#FBFBFD;border-radius:6px;border:1px solid #E6E6EC;">
<div style="font-size:10px;text-transform:uppercase;letter-spacing:1px;color:{HINOMARU_RED};font-weight:700;margin-bottom:10px;">US Tariffs on Japan</div>
{strip_html}
{s232_html}
{il}
{s3l}
{meta_line}
</div>"""

        al = trade.get("alliance_tracker") or {}
        if al:
            ds_goal = _esc(str(al.get("defense_spending_goal", "")))
            art5 = _esc(str(al.get("article5_senkaku", "")))
            hns = _esc(str(al.get("host_nation_support", "")))
            usfj = _esc(str(al.get("usfj_realignment", "")))
            rows = ""
            for label, val in (("Defense spending goal", ds_goal),
                               ("Article 5 / Senkakus", art5),
                               ("Host-nation support", hns),
                               ("USFJ realignment", usfj)):
                if val:
                    rows += (f'<tr style="border-bottom:1px solid #EEE;">'
                             f'<td style="padding:6px 10px 6px 0;font-size:12px;font-weight:600;color:{NAVY};white-space:nowrap;vertical-align:top;">{label}</td>'
                             f'<td style="padding:6px 0;font-size:12px;line-height:1.5;color:#333;">{val}</td></tr>')
            if rows:
                body += f"""<div class="alliance-box" style="margin-bottom:16px;padding:14px;background:#FBFBFD;border-radius:6px;border:1px solid #E6E6EC;">
<div style="font-size:10px;text-transform:uppercase;letter-spacing:1px;color:{HINOMARU_RED};font-weight:700;margin-bottom:8px;">Alliance Dashboard</div>
<table width="100%" cellpadding="0" cellspacing="0" border="0">{rows}</table>
</div>"""

        deals = trade.get("deals") or []
        if deals:
            dr = ""
            for d in deals[:4]:
                hd = _esc(d.get("headline", ""))
                val = _esc(d.get("value", "")) if d.get("value") else ""
                parties = _esc(d.get("parties", ""))
                det = _esc(d.get("detail", ""))
                url = d.get("url", "")
                dr += f"""<div style="margin-bottom:8px;padding-left:12px;border-left:3px solid {HINOMARU_RED};">
<div style="font-size:13px;font-weight:600;color:{NAVY};line-height:1.4;">{_link_or_text(hd, url)}{(' <span style="color:#888;font-weight:400;font-size:11px;">· ' + val + '</span>') if val else ''}</div>
<div style="font-size:12px;line-height:1.5;color:#444;">{parties}{(' — ' + det) if det else ''}</div>
</div>"""
            body += f"""<div style="margin-bottom:16px;">
<div style="font-size:10px;text-transform:uppercase;letter-spacing:1px;color:{HINOMARU_RED};font-weight:700;margin-bottom:8px;">New Agreements / Pledges</div>
{dr}
</div>"""

        if body:
            sections_trackers.append(f'<div {_SEC}>{_sec_label("US&ndash;Japan Alliance &amp; Trade")}{body}</div>')

    # 10. Business & Economy
    biz = digest.get("business_economy") or []
    if biz:
        bh = ""
        for b in biz[:6]:
            h = _esc(b.get("headline", ""))
            bt = _esc(b.get("body_text", ""))
            url = b.get("url", "")
            src = _esc(b.get("source", ""))
            sec = _esc(b.get("sector", ""))
            comps = b.get("companies", [])
            cs = ", ".join(_esc(c) for c in comps) if comps else ""
            bh += f"""<div style="margin-bottom:10px;padding-left:12px;border-left:3px solid #BC002D;">
<div style="font-size:11px;color:#888;text-transform:uppercase;">{sec} · {src}{(' · ' + cs) if cs else ''}</div>
<div style="font-size:13px;font-weight:600;color:#1B2A4A;">{_link_or_text(h, url)}</div>
<div style="font-size:12px;line-height:1.4;color:#555;">{bt}</div>
</div>"""
        sections_wire.append(f'<div {_SEC}>{_sec_label("Business &amp; Economy")}{bh}</div>')

    # 11. Indo-Pacific
    ip = digest.get("indo_pacific") or []
    if ip:
        ih = ""
        for it in ip[:6]:
            r = it.get("region_tag", "Indo-Pacific")
            bar = NAVY
            h = _esc(it.get("headline", ""))
            bt = _esc(it.get("body_text", ""))
            url = it.get("url", "")
            src = _esc(_clean_src(it.get("source", "")))
            ih += f"""<div style="margin-bottom:10px;padding-left:12px;border-left:3px solid {bar};">
<div style="font-size:11px;color:{bar};text-transform:uppercase;font-weight:600;">{_esc(r)} · {src}</div>
<div style="font-size:13px;font-weight:600;color:#1B2A4A;">{_link_or_text(h, url)}</div>
<div style="font-size:12px;line-height:1.4;color:#555;">{bt}</div>
</div>"""
        sections_wire.append(f'<div {_SEC}>{_sec_label("Indo-Pacific")}{ih}</div>')

    # 12. Diet Watch (key: congressional_watch)
    cw = digest.get("congressional_watch") or []
    if cw:
        ch = ""
        for c in cw:
            comm = _esc(c.get("committee", ""))
            act = _esc(c.get("action", ""))
            det = _esc(c.get("detail", ""))
            url = c.get("url", "")
            ch += f"""<div style="margin-bottom:10px;padding-left:12px;border-left:3px solid #2C3E50;">
<div style="font-size:11px;color:#7F8C8D;font-weight:600;text-transform:uppercase;">{comm}</div>
<div style="font-size:13px;font-weight:600;color:#1B2A4A;">{_link_or_text(act, url)}</div>
<div style="font-size:12px;line-height:1.4;color:#555;">{det}</div>
</div>"""
        sections_trackers.append(f'<div {_SEC}>{_sec_label("Diet Watch")}{ch}</div>')

    # 13. Expert Analysts
    opeds = digest.get("opeds_today") or []
    academics = digest.get("academic_today") or []
    if opeds or academics:
        body = ""
        if opeds:
            body += '<div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:#1B2A4A;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #E8E8E8;">Op-Eds &amp; Think Tank Commentary</div>'
            for o in opeds[:6]:
                title = _esc(o.get("title") or o.get("headline", ""))
                src = _esc(o.get("source", ""))
                auth = _esc(o.get("authors", ""))
                ca = _esc(o.get("central_argument", ""))
                sm = _esc(o.get("summary", ""))
                ps = _esc(o.get("policy_so_what", ""))
                url = o.get("url", "")
                body += f"""<div style="margin-bottom:14px;padding:12px 14px;background:#fff;border-radius:2px;border-left:3px solid #1B2A4A;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
<div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:4px;">{src}{(' · ' + auth) if auth else ''}</div>
<div style="font-size:14px;font-weight:700;color:#1B2A4A;font-family:Georgia,serif;line-height:1.35;margin-bottom:6px;">{_link_or_text(title, url, style="color:#1B2A4A;text-decoration:none;")}</div>
{"<div style='font-size:12px;color:#444;font-style:italic;line-height:1.45;margin-bottom:5px;padding-left:8px;border-left:2px solid #D5D5D5;'>" + ca + "</div>" if ca else ""}
{"<div style='font-size:11px;line-height:1.5;color:#666;'>" + sm + "</div>" if sm else ""}
{"<div style='font-size:11px;color:#1B2A4A;margin-top:4px;font-weight:600;'>" + ps + "</div>" if ps else ""}
</div>"""
        if academics:
            body += '<div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:#1B2A4A;margin:14px 0 8px 0;padding-bottom:4px;border-bottom:1px solid #E8E8E8;">Academic Journals</div>'
            for a in academics[:4]:
                title = _esc(a.get("title", ""))
                src = _esc(a.get("source", ""))
                tier = _esc(a.get("journal_tier", ""))
                auth = _esc(a.get("authors", ""))
                sm = _esc(a.get("summary", ""))
                url = a.get("url", "")
                body += f"""<div style="margin-bottom:12px;padding:12px 14px;background:#fff;border-radius:2px;border-left:3px solid #1B2A4A;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
<div style="font-size:10px;color:#1B2A4A;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:4px;">{src} · {tier}{(' · ' + auth) if auth else ''}</div>
<div style="font-size:13px;font-weight:700;color:#1B2A4A;font-family:Georgia,serif;line-height:1.35;margin-bottom:5px;">{_link_or_text(title, url, style="color:#1B2A4A;text-decoration:none;")}</div>
<div style="font-size:12px;line-height:1.5;color:#555;">{sm}</div>
</div>"""
        sections_analysis.append(f'<div {_SEC}>{_sec_label("Expert Analysts")}{body}</div>')

    # 14. Public Sentiment — cabinet approval & party support
    ps = digest.get("public_sentiment") or {}
    # Support the new multi-poll array and the legacy single object
    polls = ps.get("approval_polls")
    if not polls:
        legacy = ps.get("approval_polling")
        polls = [legacy] if isinstance(legacy, dict) else []
    polls = [p for p in polls if isinstance(p, dict) and p.get("cabinet_approval")][:3]
    party = ps.get("party_support") or []
    disc = _esc(ps.get("discourse_flag", ""))
    if polls or party or disc:
        poll_body = ""
        if len(polls) >= 2:
            # Multi-poll row — one cell per pollster, so the spread is visible
            n = len(polls)
            w = 100 // n
            cells = ""
            for i, p in enumerate(polls):
                pollster = _esc(p.get("pollster", ""))
                pdate = _esc(p.get("poll_date", ""))
                appr = _esc(str(p.get("cabinet_approval", "")))
                disappr = _esc(str(p.get("cabinet_disapproval", "") or ""))
                chg = _esc(str(p.get("approval_change", "") or ""))
                bl = "border-left:1px solid #E4E7EC;" if i else ""
                dis_html = (f'<div style="font-size:11px;color:#C0392B;margin-top:3px;">{disappr} disapprove</div>'
                            if disappr and disappr not in ("—", "None") else "")
                chg_html = f'<div style="font-size:10px;color:#888;margin-top:2px;">{chg}</div>' if chg else ""
                cells += (f'<td width="{w}%" align="center" style="padding:12px 6px;{bl}vertical-align:top;">'
                          f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:1px;color:{NAVY};font-weight:700;">{pollster}</div>'
                          f'<div style="font-size:9px;color:#999;margin-bottom:5px;">{pdate}</div>'
                          f'<div style="font-size:24px;font-weight:700;color:{NAVY};font-family:Georgia,serif;">{appr}</div>'
                          f'<div style="font-size:9px;color:#27AE60;text-transform:uppercase;letter-spacing:0.5px;">approve</div>'
                          f'{dis_html}{chg_html}</td>')
            poll_body += (f'<div style="font-size:10px;color:#888;margin-bottom:6px;">Cabinet approval by pollster — figures differ by house</div>'
                          f'<table class="sentiment-table" width="100%" cellpadding="0" cellspacing="0" border="0" '
                          f'style="margin-bottom:10px;background:#F7F8FA;border-radius:6px;"><tr>{cells}</tr></table>')
        elif len(polls) == 1:
            ap = polls[0]
            pollster = _esc(ap.get("pollster", ""))
            pdate = _esc(ap.get("poll_date", ""))
            appr = _esc(str(ap.get("cabinet_approval", "")))
            disappr = _esc(str(ap.get("cabinet_disapproval", "") or ""))
            chg = _esc(str(ap.get("approval_change", ""))) if ap.get("approval_change") else ""
            chg_html = f' <span style="font-size:11px;color:#888;">({chg})</span>' if chg else ""
            has_disappr = disappr and disappr not in ("—", "None")
            if has_disappr:
                stat_row = f"""<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:10px;">
<tr>
<td width="50%" align="center" class="sent-approve" style="padding:10px;background:#EAF5EA;border-radius:4px;">
<div style="font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#27AE60;font-weight:700;">Approve</div>
<div style="font-size:26px;font-weight:700;color:#1B2A4A;font-family:Georgia,serif;">{appr}{chg_html}</div>
</td>
<td width="4"></td>
<td width="50%" align="center" class="sent-disapprove" style="padding:10px;background:#FBECEC;border-radius:4px;">
<div style="font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#C0392B;font-weight:700;">Disapprove</div>
<div style="font-size:26px;font-weight:700;color:#1B2A4A;font-family:Georgia,serif;">{disappr}</div>
</td>
</tr>
</table>"""
            else:
                # Disapproval not reported in the same poll — show approval alone, no empty box.
                stat_row = f"""<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:10px;">
<tr>
<td align="center" class="sent-approve" style="padding:10px;background:#EAF5EA;border-radius:4px;">
<div style="font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#27AE60;font-weight:700;">Cabinet Approval</div>
<div style="font-size:26px;font-weight:700;color:#1B2A4A;font-family:Georgia,serif;">{appr}{chg_html}</div>
</td>
</tr>
</table>"""
            poll_body += stat_row + f"""<div style="font-size:10px;color:#888;margin-bottom:10px;">{pollster}{(' · ' + pdate) if pdate else ''}</div>"""

        if party:
            pr = ""
            for p in party[:6]:
                pn = _esc(p.get("party", ""))
                pp = _esc(str(p.get("support_pct", "")))
                pr += f"""<tr style="border-bottom:1px solid #EEE;">
<td style="padding:4px 6px 4px 0;font-size:12px;color:#1B2A4A;">{pn}</td>
<td style="padding:4px 0;font-size:12px;font-weight:700;color:#1B2A4A;text-align:right;">{pp}</td>
</tr>"""
            _party_note = "primary poll" if len(polls) >= 2 else "same poll"
            poll_body += f"""<div style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:#2C3E50;margin:6px 0;">Party Support ({_party_note})</div>
<table width="100%" cellpadding="0" cellspacing="0" border="0">{pr}</table>"""

        if disc:
            poll_body += f'<div style="font-size:12px;color:#555;margin-top:10px;padding-top:8px;border-top:1px solid #EEE;"><strong>Discourse:</strong> {disc}</div>'

        # Aggregator link (Observing Japan poll tracker)
        poll_body += (f'<div style="margin-top:12px;padding-top:8px;border-top:1px solid #EEE;font-size:11px;color:#888;">'
                      f'Poll tracker: '
                      + _link_or_text("Observing Japan approval-rating aggregator &#8594;", OBSERVING_JAPAN_POLLS,
                                      style="color:" + HINOMARU_RED + ";text-decoration:none;font-weight:600;")
                      + '</div>')

        sections_analysis.append(f'<div {_SEC}>{_sec_label("Public Sentiment &amp; Approval Polling")}{poll_body}</div>')

    # 15. Social Statements
    stmts = digest.get("social_statements") or []
    if stmts:
        sh = ""
        for s in stmts[:6]:
            who = _esc(s.get("who", ""))
            ctx = _esc(s.get("handle_context", ""))
            pd = _esc(s.get("platform_date", ""))
            q = _esc(s.get("quote_text", ""))
            nt = _esc(s.get("analyst_note", ""))
            initials = _esc(s.get("avatar_initials", (who[:2].upper() if who else "?")))
            url = s.get("url", "")
            meta = " &middot; ".join(x for x in (ctx, pd) if x)
            src_link = ("<div style='margin-top:6px;'>" + _link_or_text("Source &#8594;", url, style="font-size:11px;color:" + HINOMARU_RED + ";text-decoration:none;") + "</div>") if url and url != "#" and url.startswith("http") else ""
            sh += f"""<div style="margin-bottom:12px;padding:12px 14px;background:#F7F8FA;border-radius:6px;border-left:3px solid {HINOMARU_RED};">
<table cellpadding="0" cellspacing="0" border="0" style="margin-bottom:8px;"><tr>
<td width="38" style="vertical-align:middle;">
<div style="width:38px;height:38px;border-radius:50%;background:{HINOMARU_RED};color:#fff;text-align:center;line-height:38px;font-size:14px;font-weight:700;font-family:Arial,sans-serif;">{initials}</div>
</td>
<td style="padding-left:10px;vertical-align:middle;">
<div style="font-size:13px;font-weight:700;color:{NAVY};">{who}</div>
<div style="font-size:11px;color:#888;">{meta}</div>
</td>
</tr></table>
<p style="margin:0;font-size:13px;line-height:1.6;color:#2C3E50;font-style:italic;">&ldquo;{q}&rdquo;</p>
{"<p style='margin:6px 0 0 0;font-size:11px;color:#555;'><strong style='color:" + HINOMARU_RED + ";font-style:normal;'>Analyst:</strong> " + nt + "</p>" if nt else ""}
{src_link}
</div>"""
        sections_analysis.append(f'<div {_SEC}>{_sec_label("Social Statements")}{sh}</div>')

    # 16. Also Today
    also = digest.get("also_today") or []
    if also:
        wc_ = {}  # single navy accent for all wire bars
        ah = ""
        for a in also[:6]:
            cr_ = _str(a.get("category", ""))
            c = _esc(cr_)
            h = _esc(a.get("headline", ""))
            b = _esc(a.get("body_text", ""))
            url = a.get("url", "")
            src = _esc(_clean_src(a.get("source", "")))
            bar = wc_.get(cr_, "#7F8C8D")
            ah += f"""<div style="margin-bottom:10px;padding-left:12px;border-left:3px solid {bar};">
<div style="font-size:10px;color:#888;text-transform:uppercase;">{c} &middot; {src}</div>
<div style="font-size:13px;font-weight:600;color:#1B2A4A;">{_link_or_text(h, url)}</div>
<div style="font-size:12px;line-height:1.4;color:#555;">{b}</div>
</div>"""
        sections_wire.append(f'<div {_SEC}>{_sec_label("Also Today / The Wire")}{ah}</div>')

    # 17. On This Day
    otd = digest.get("on_this_day") or []
    if otd:
        oh = ""
        for it in otd[:1]:
            oh += f"""<div style="padding:12px 14px;background:#FAFAF5;border-radius:4px;border-left:3px solid #7F8C8D;">
<div style="font-size:11px;color:#7F8C8D;text-transform:uppercase;letter-spacing:0.5px;font-weight:600;">{_esc(it.get("date", ""))}</div>
<div style="font-size:14px;font-weight:600;color:#1B2A4A;font-family:Georgia,serif;margin:4px 0;">{_esc(it.get("event", ""))}</div>
<div style="font-size:12px;color:#555;font-style:italic;line-height:1.5;">{_esc(it.get("relevance", ""))}</div>
</div>"""
        sections_wire.append(f'<div {_SEC}>{_sec_label("On This Day")}{oh}</div>')

    # Footer
    sections_post.append(f"""
<div style="padding:20px 32px;background:#1B2A4A;text-align:center;" class="sec footer">
<div style="font-size:9px;text-transform:uppercase;letter-spacing:2px;color:rgba(255,255,255,0.45);font-family:Arial,sans-serif;line-height:2;">
CSIS Japan Chair &nbsp;·&nbsp; Japan Daily Brief &nbsp;·&nbsp; Generated <span style="font-family:'Courier New',Courier,monospace;">{gen_time}</span>
</div>
<a href="#top" style="font-size:10px;color:rgba(255,255,255,0.4);text-decoration:none;letter-spacing:1px;">&#8593; Back to top</a>
</div>""")

    sections = (
        sections_pre +
        sections_today +
        sections_analysis +
        ([_chapter("TRACKERS")] if sections_trackers else []) + sections_trackers +
        ([_chapter("WIRE")] if sections_wire else []) + sections_wire +
        sections_post
    )

    body_html = "\n".join(s for s in sections if s)
    return f"""<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<title>Japan Daily Brief &mdash; {_esc(date_str)}</title>
<style type="text/css">
  /* Reset */
  body, table, td, div, p {{ margin:0; padding:0; }}
  img {{ border:0; display:block; }}
  /* Data typography — monospace for machine-measured numbers */
  .mkt-table div[style*="font-weight:700"], .key-stat-num {{ font-family:'Courier New',Courier,monospace !important; }}
  /* Mobile responsive */
  @media only screen and (max-width: 620px) {{
    .wrapper {{ width:100% !important; }}
    .sec, .footer {{ padding:16px 16px !important; }}
    h1 {{ font-size:22px !important; }}
    .key-stat-num {{ font-size:26px !important; }}
    /* Market strip stays multi-across on phones — smaller mono, tighter pad */
    .mkt-table td {{ padding:8px 4px 10px !important; }}
    .mkt-table div[style*="font-size:20px"] {{ font-size:16px !important; }}
    .mkt-table div[style*="font-size:15px"] {{ font-size:13px !important; }}
    /* Story cards */
    .story-card {{ padding:12px 12px !important; }}
    /* Dark Regional Pressure Watch panel */
    .watch-dark td {{ padding-left:16px !important; padding-right:16px !important; }}
    /* Trade dashboard boxes */
    .tariff-box, .alliance-box {{ padding:10px 12px !important; }}
    /* Overflow + legibility safety */
    p, div, td {{ word-wrap:break-word !important; overflow-wrap:break-word !important; }}
    body, td, div, p, span {{ -webkit-text-size-adjust:100%; }}
    div[style*="font-size:9px"], span[style*="font-size:9px"] {{ font-size:10px !important; }}
    a {{ min-height:44px; }}
    p a, div a, td a {{ min-height:auto; padding:6px 0; }}
    img {{ max-width:100% !important; height:auto !important; }}
  }}
  /* Tablet breakpoint */
  @media only screen and (min-width: 621px) and (max-width: 768px) {{
    .wrapper {{ width:100% !important; }}
    .sec, .footer {{ padding:16px 22px !important; }}
    h1 {{ font-size:24px !important; }}
    .mkt-table td {{ padding:10px 10px 12px !important; }}
  }}
  /* Dark mode — scoped, non-destructive. The masthead, market strip,
     Regional Pressure Watch panel, key stat, and footer are already dark
     surfaces and need no inversion. */
  @media (prefers-color-scheme: dark) {{
    body {{ background:#121212 !important; }}
    .wrapper {{ background:#1a1a1a !important; }}
    .wrapper .sec {{ background:#1E2126 !important; border-bottom-color:#33373D !important; }}
    .wrapper h1, .wrapper h2, .wrapper h3 {{ color:#E8E6E1 !important; }}
    .wrapper .sec p {{ color:#C4C8CE !important; }}
    .wrapper a {{ color:#6FA8E8 !important; }}
    .wrapper .footer {{ background:#0F1B30 !important; }}
    .wrapper .story-card {{ background:#262A30 !important; border-color:#33373D !important; }}
    /* Trade dashboard light boxes → neutral dark equivalents */
    .wrapper .tariff-box, .wrapper .alliance-box {{ background:#22262C !important; border-color:#33373D !important; }}
    .wrapper .tariff-box strong, .wrapper .alliance-box strong {{ color:#C4C8CE !important; }}
    /* Public Sentiment stat boxes */
    .wrapper .sent-approve {{ background:#16261B !important; }}
    .wrapper .sent-disapprove {{ background:#2A1518 !important; }}
    .wrapper .mkt-table td {{ border-color:rgba(255,255,255,0.08) !important; }}
  }}
</style>
<!--[if mso]>
<style type="text/css">
  table {{ border-collapse:collapse; }}
  .wrapper {{ width:680px; }}
</style>
<![endif]-->
</head>
<body style="margin:0;padding:0;background:#F2F3F5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;">
<a name="top"></a>
<!--[if mso]><table width="680" cellpadding="0" cellspacing="0" border="0" align="center"><tr><td><![endif]-->
<div class="wrapper" style="max-width:680px;width:100%;margin:0 auto;background:#FFFFFF;overflow:hidden;box-shadow:0 2px 20px rgba(0,0,0,0.08);">
{body_html}
</div>
<!--[if mso]></td></tr></table><![endif]-->
</body>
</html>"""


if __name__ == "__main__":
    import json
    with open("test_digest.json") as f:
        d = json.load(f)
    html = render_html(d)
    with open("preview.html", "w") as f:
        f.write(html)
    print(f"Rendered {len(html):,} bytes")
