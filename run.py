"""
Japan Daily Brief — Pipeline Entry Point
Orchestrates collect → digest → validate → render → send → archive.
"""
import argparse
import json
import os
import re as _re
import sys
import time
import traceback
import requests as _requests
from concurrent.futures import ThreadPoolExecutor as _ThreadPoolExecutor, as_completed as _as_completed
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent
COLLECTED_JSON = ROOT / "collected.json"
DIGEST_JSON = ROOT / "digest.json"
DIGEST_HTML = ROOT / "digest.html"
PUBLIC_DIR = ROOT / "public"
# Rolling record of what has already been published, so a story that ran in a
# recent edition isn't repeated on a later day. Cached across GitHub Actions runs
# like pm_tracker.json / region_tracker.json.
LEDGER_JSON = ROOT / "published_ledger.json"
_LEDGER_WINDOW_DAYS = 14


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION GATE
# ─────────────────────────────────────────────────────────────────────────────

PRESTIGE_SOURCES = {
    "WSJ Japan", "NYT Japan", "WaPo Japan", "Bloomberg Japan", "FT Japan",
    "Economist Japan", "CNN Japan", "Reuters Japan", "Nikkei Asia", "Japan Times",
}

ENTERTAINMENT_BLOCK = ("celebrity", "j-pop", "idol", "anime", "manga",
                      "fashion", "concert tour")


# Minimum readable words (validation gate). Loosened from 1000 so light news
# days don't trip the gate. Note _count_words below is narrower than the
# header/display counter, so this maps to a higher displayed word count.
MIN_WORD_COUNT = 650


def _count_words(digest: dict) -> int:
    """Count readable words across all text fields."""
    text_fields = ("body", "body_text", "summary", "detail", "quote_text",
                   "so_what", "pattern_note", "central_argument", "analyst_note",
                   "headline", "action")
    words = 0

    for mi in (digest.get("morning_memo") or []):
        if isinstance(mi, dict):
            for v in mi.values():
                if isinstance(v, str):
                    words += len(v.split())
        elif isinstance(mi, str):
            words += len(mi.split())

    for key in ("top_stories", "overnight_items", "also_today", "business_economy",
                "indo_pacific", "social_statements", "opeds_today", "academic_today",
                "prc_government", "congressional_watch", "npc_politburo",
                "personnel_changes"):
        for item in (digest.get(key) or []):
            if not isinstance(item, dict):
                continue
            for field in text_fields:
                val = item.get(field, "")
                if val:
                    words += len(str(val).split())

    delta = digest.get("xinhua_delta") or {}
    for field in ("bottom_line", "china_signal", "dprk_signal", "russia_signal",
                  "senkaku_status"):
        val = delta.get(field, "")
        if val:
            words += len(str(val).split())

    return words


def _validate_digest(digest: dict) -> list[str]:
    """Run pre-send quality checks. Returns list of failures (empty = pass)."""
    failures = []

    word_count = _count_words(digest)
    if word_count < MIN_WORD_COUNT:
        failures.append(f"WORD COUNT: {word_count} words (minimum {MIN_WORD_COUNT})")

    top_count = len(digest.get("top_stories") or [])
    if top_count < 2:
        failures.append(f"TOP STORIES: {top_count} (minimum 2)")
    if top_count > 4:
        failures.append(f"TOP STORIES: {top_count} (maximum 4)")

    overnight_count = len(digest.get("overnight_items") or [])
    if overnight_count < 3:
        failures.append(f"OVERNIGHT ITEMS: {overnight_count} (minimum 3)")

    memo = digest.get("morning_memo") or []
    if len(memo) != 3:
        failures.append(f"MORNING MEMO: {len(memo)} items (must be exactly 3)")

    # Source diversity check
    all_items = (digest.get("top_stories") or []) + (digest.get("overnight_items") or [])
    source_counts = {}
    for item in all_items:
        src = (item.get("source") or "").strip()
        if src:
            source_counts[src] = source_counts.get(src, 0) + 1
    for src, count in source_counts.items():
        if count > 3:
            failures.append(f"SOURCE DIVERSITY: '{src}' appears {count} times "
                          f"in top + overnight (max 3)")

    # Date integrity
    digest_date = digest.get("digest_date", "")
    today_str = datetime.now(ZoneInfo("America/New_York")).strftime("%A, %B %-d, %Y")
    if digest_date and digest_date != today_str:
        failures.append(f"DATE MISMATCH: digest_date='{digest_date}' vs today='{today_str}'")

    # Placeholder URL check
    for key in ("top_stories", "overnight_items", "also_today"):
        for item in (digest.get(key) or []):
            url = (item.get("url") or "").strip()
            if url in ("#", "None", "null", ""):
                continue
            if "example.com" in url or "placeholder" in url.lower():
                failures.append(f"PLACEHOLDER URL in {key}: {url}")

    return failures


# ─────────────────────────────────────────────────────────────────────────────
# ARCHIVE TO GITHUB PAGES
# ─────────────────────────────────────────────────────────────────────────────

def _decode_gnews_url(url: str, timeout: int = 8) -> str | None:
    """Decode a Google News RSS article URL to the real publisher URL via Google's
    batchexecute endpoint. Returns the real URL, or None on any failure.

    Modern Google News RSS links (news.google.com/rss/articles/CBMi...) do not
    HTTP-redirect; the real URL must be recovered by (1) scraping a per-article
    signature + timestamp from the article page, then (2) POSTing them to the
    batchexecute endpoint. (Algorithm per the widely-used gnews URL decoders.)
    """
    from urllib.parse import urlparse as _up, quote as _quote
    import re as _re
    try:
        art_id = _up(url).path.split("/")[-1]
        if not art_id or len(art_id) < 20:
            return None
        ua = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
        r = _requests.get(f"https://news.google.com/rss/articles/{art_id}",
                          timeout=timeout, headers=ua)
        if not r.ok:
            return None
        sg = _re.search(r'data-n-a-sg="([^"]+)"', r.text)
        ts = _re.search(r'data-n-a-ts="([^"]+)"', r.text)
        if not (sg and ts):
            return None
        inner = ('["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,'
                 'null,null,null,null,null,0,1],"X","X",1,[1,1,1],1,1,null,0,0,null,0],'
                 f'"{art_id}",{ts.group(1)},"{sg.group(1)}"]')
        freq = json.dumps([[["Fbv4je", inner]]])
        resp = _requests.post(
            "https://news.google.com/_/DotsSplashUi/data/batchexecute",
            data="f.req=" + _quote(freq),
            headers={"content-type": "application/x-www-form-urlencoded;charset=UTF-8", **ua},
            timeout=timeout,
        )
        if not resp.ok:
            return None
        # Response framing: )]}'\n\n<chunk-length>\n[["wrb.fr","Fbv4je",
        # "[\"garturlres\",\"https://REAL-PUBLISHER-URL\",...]",...]] . The old
        # json.loads(split("\n\n")[1]) choked on the chunk-length line and always
        # raised, so nothing ever decoded. Extract the publisher URL directly.
        text = resp.text
        if "garturlres" not in text:
            return None
        m = _re.search(r'https?://[^\s"\\]+', text.split("garturlres", 1)[1])
        real = m.group(0) if m else None
        return real if real and real.startswith("http") and "news.google.com" not in real else None
    except Exception:
        return None


def _resolve_google_url(url: str) -> str | None:
    """Resolve a Google News RSS URL to the real publisher article URL.

    Tries the batchexecute decoder first, then a plain redirect-follow. Returns
    None if BOTH fail — the caller then substitutes a durable Google News search
    link built from the headline. The raw RSS token (news.google.com/rss/articles/
    CBMi...) must NOT be kept: those tokens are not stable permalinks and 404 when
    opened later from the email, which is the whole bug this fixes.
    """
    if "news.google.com" not in url:
        return url
    decoded = _decode_gnews_url(url)
    if decoded:
        return decoded
    try:
        resp = _requests.get(
            url, allow_redirects=True, timeout=6,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        final = resp.url
        if final and not final.startswith("https://news.google.com"):
            return final
    except Exception:
        pass
    return None  # unresolved — caller substitutes a durable search link


# Fields a digest item may carry its display title under (see _item_identity).
_TITLE_FIELDS = ("headline", "title", "action", "committee", "statement", "body", "quote", "name")


def _item_title(item: dict) -> str:
    """Best available human title for a digest item, for the search-link fallback."""
    for f in _TITLE_FIELDS:
        v = item.get(f)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _gnews_search_url(title: str) -> str:
    """A DURABLE Google News link: a search for the headline. Unlike the RSS
    article token it never 404s, and it lands the reader on the story. Used when
    a Google News redirect can't be resolved to a publisher URL."""
    from urllib.parse import quote_plus
    q = quote_plus((title or "").strip())
    return f"https://news.google.com/search?q={q}&hl=en-US&gl=US&ceid=US:en" if q else ""


# Friendly names for the domains that show up as source links. Anything not listed
# falls back to its registrable hostname, so the label always names the REAL link
# target — never a government actor the story merely happens to be about.
_PUBLISHER_NAMES = {
    "mofa.go.jp": "MOFA", "mod.go.jp": "MOD", "japan.kantei.go.jp": "Kantei",
    "kantei.go.jp": "Kantei", "meti.go.jp": "METI", "mof.go.jp": "MOF",
    "boj.or.jp": "Bank of Japan",
    "kyodonews.net": "Kyodo News", "japantimes.co.jp": "The Japan Times",
    "nhk.or.jp": "NHK", "asia.nikkei.com": "Nikkei Asia", "nikkei.com": "Nikkei",
    "mainichi.jp": "Mainichi", "asahi.com": "Asahi", "yomiuri.co.jp": "Yomiuri",
    "the-japan-news.com": "The Japan News", "japan-forward.com": "Japan Forward",
    "thediplomat.com": "The Diplomat", "jiji.com": "Jiji Press",
    "reuters.com": "Reuters", "apnews.com": "AP", "afp.com": "AFP",
    "bloomberg.com": "Bloomberg", "wsj.com": "WSJ", "nytimes.com": "NYT",
    "washingtonpost.com": "Washington Post", "ft.com": "FT", "cnbc.com": "CNBC",
    "bbc.com": "BBC", "bbc.co.uk": "BBC", "cnn.com": "CNN",
    "theguardian.com": "The Guardian", "economist.com": "The Economist",
    "aa.com.tr": "Anadolu Agency", "scmp.com": "SCMP",
    "globaltimes.cn": "Global Times", "xinhuanet.com": "Xinhua", "tass.com": "TASS",
    "en.yna.co.kr": "Yonhap", "koreaherald.com": "Korea Herald",
    "news.google.com": "Google News",
}
_KNOWN_PUBLISHER_NAMES = frozenset(_PUBLISHER_NAMES.values())


def _publisher_label(url: str) -> str:
    """Human name for a URL's publisher, derived from its DOMAIN so the label can
    never misrepresent where the link goes (e.g. a MOFA protest reported by Anadolu
    labels 'Anadolu Agency', not 'MOFA'). Unknown domains fall back to the host."""
    from urllib.parse import urlparse
    try:
        h = (urlparse(url).hostname or "").lower()
    except Exception:
        return ""
    if h.startswith("www."):
        h = h[4:]
    if not h:
        return ""
    for dom, name in _PUBLISHER_NAMES.items():
        if h == dom or h.endswith("." + dom):
            return name
    return h   # unknown → the bare host (minus www.), always an honest label


def _mapped_publisher(url: str) -> str:
    """Friendly publisher name ONLY if the URL's domain is a known one, else ''.
    Used to align a news item's source attribution with its real link WITHOUT
    downgrading an unmapped outlet to a bare host."""
    label = _publisher_label(url)
    return label if label in _KNOWN_PUBLISHER_NAMES else ""


def _resolve_payload_urls(payload: dict) -> dict:
    """Resolve all Google News RSS redirect URLs in collected payload before Claude sees them."""
    all_gnews: dict = {}
    for tier in ("tier1", "tier2", "tier3", "tier4"):
        for art in (payload.get(tier) or []):
            u = art.get("url", "")
            if u and "news.google.com" in u:
                all_gnews[u] = u

    if not all_gnews:
        return payload

    print(f"   ↻ Pre-resolving {len(all_gnews)} Google News URLs in payload...")
    with _ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(_resolve_google_url, u): u for u in all_gnews}
        for future in _as_completed(futures):
            original = futures[future]
            all_gnews[original] = future.result()   # real URL or None

    resolved = sum(1 for v in all_gnews.values() if v and "news.google.com" not in v)
    print(f"   ✓ {resolved}/{len(all_gnews)} resolved to real article URLs")

    for tier in ("tier1", "tier2", "tier3", "tier4"):
        for art in (payload.get(tier) or []):
            u = art.get("url", "")
            if all_gnews.get(u):                    # keep original if unresolved (None)
                art["url"] = all_gnews[u]

    return payload


_URL_SECTIONS = (
    "top_stories", "overnight_items", "also_today", "business_economy",
    "indo_pacific", "opeds_today", "academic_today", "social_statements",
    "prc_government", "congressional_watch", "npc_politburo", "personnel_changes",
)


def _attach_orig_titles(digest: dict, collected_by_url: dict) -> dict:
    """Stamp each item with the ORIGINAL headline of the collected article it links
    to (matched by URL, before URLs are resolved). This keeps a verbatim, traceable
    source title behind any synthesized/paraphrased display headline, so the exact
    original article is always recoverable. Best-effort: no match → no orig_title."""
    def _stamp(item):
        if not isinstance(item, dict):
            return
        t = collected_by_url.get(item.get("url", ""))
        if t and str(t).strip():
            item["orig_title"] = str(t).strip()
    for section in _URL_SECTIONS:
        for item in (digest.get(section) or []):
            _stamp(item)
    for item in ((digest.get("us_china_trade") or {}).get("deals") or []):
        _stamp(item)
    return digest


def _sanitise_urls(digest: dict, collected_urls: set) -> dict:
    """Null out hallucinated URLs; resolve Google News redirects for real ones."""
    from urllib.parse import urlparse as _up

    collected_domains: set = set()
    for u in collected_urls:
        try:
            h = _up(u).hostname or ""
            if h.startswith("www."):
                h = h[4:]
            if h:
                collected_domains.add(h)
        except Exception:
            pass

    def _url_allowed(url: str) -> bool:
        if url in collected_urls:
            return True
        try:
            h = _up(url).hostname or ""
            if h.startswith("www."):
                h = h[4:]
            return bool(h) and h in collected_domains
        except Exception:
            return False

    google_urls = {}

    for section in _URL_SECTIONS:
        for item in (digest.get(section) or []):
            if not isinstance(item, dict):
                continue
            url = item.get("url", "")
            if not url or not url.startswith("http"):
                item["url"] = ""
                continue
            if not _url_allowed(url):
                item["url"] = ""  # unknown domain — hallucinated
            elif "news.google.com" in url:
                google_urls[url] = url

    # Also handle deals inside us_china_trade (US-Japan Alliance & Trade)
    trade = digest.get("us_china_trade") or {}
    for item in (trade.get("deals") or []):
        if not isinstance(item, dict):
            continue
        url = item.get("url", "")
        if not url or not url.startswith("http"):
            item["url"] = ""
            continue
        if not _url_allowed(url):
            item["url"] = ""
        elif "news.google.com" in url:
            google_urls[url] = url

    if google_urls:
        print(f"   ↻ Decoding {len(google_urls)} Google News URL(s)...")
        with _ThreadPoolExecutor(max_workers=6) as pool:
            futures = {pool.submit(_resolve_google_url, u): u for u in google_urls}
            for future in _as_completed(futures):
                original = futures[future]
                google_urls[original] = future.result()   # real publisher URL or None

        decoded = sum(1 for v in google_urls.values() if v and "news.google.com" not in v)
        print(f"   ✓ {decoded}/{len(google_urls)} decoded to publisher URLs "
              f"(rest → durable Google News search links, never the raw RSS token)")

        def _apply(item: dict) -> None:
            u = item.get("url", "")
            if u not in google_urls:
                return
            resolved = google_urls[u]
            if resolved and "news.google.com" not in resolved:
                item["url"] = resolved                      # real publisher deep link
            else:
                item["url"] = _gnews_search_url(_item_title(item))  # durable fallback

        for section in _URL_SECTIONS:
            for item in (digest.get(section) or []):
                if isinstance(item, dict):
                    _apply(item)
        for item in ((digest.get("us_china_trade") or {}).get("deals") or []):
            if isinstance(item, dict):
                _apply(item)

    # Japanese Government items render a source LINK next to the acting ministry.
    # Derive its label from the (now-resolved) URL's domain so it names the real
    # publisher — never the ministry the story is about. Runs after resolution so
    # the label matches where the link actually goes.
    for item in (digest.get("prc_government") or []):
        if not isinstance(item, dict):
            continue
        u = item.get("url", "")
        item["source_label"] = _publisher_label(u) if isinstance(u, str) and u.startswith("http") else ""

    # Across the other news sections, align each item's source attribution with its
    # real link when that link is a KNOWN publisher — so the shown source can't
    # disagree with where the link goes. Conservative: only overrides with a mapped
    # friendly name (never a bare host), only touches items that already carry a
    # "source", and skips Google News search fallbacks (keeps the model's publisher).
    for section in _URL_SECTIONS:
        if section == "prc_government":
            continue
        for item in (digest.get(section) or []):
            if not isinstance(item, dict):
                continue
            u = item.get("url", "")
            if isinstance(u, str) and u.startswith("http") and "news.google.com" not in u:
                # Authoritative primary source = the publisher the link actually
                # opens, derived from its domain. Render prefers this over the
                # model's free-text source line, so a synthesized item's shown
                # source can't disagree with where the link goes.
                item["link_source"] = _publisher_label(u)
                name = _mapped_publisher(u)
                if name and "source" in item:
                    item["source"] = name

    return digest


# Every content section carrying discrete items, in placement-priority order
# (highest first). An item kept in a higher-priority section is dropped from every
# lower one, so each story appears in exactly ONE place across the WHOLE brief.
# (Previously only eight sections were swept, which let the same story appear in,
# e.g., the MOFA tracker AND Personnel Changes at once.)
_DEDUPE_ORDER = (
    "top_stories", "overnight_items", "prc_government", "personnel_changes",
    "congressional_watch", "npc_politburo", "indo_pacific", "business_economy",
    "opeds_today", "academic_today", "social_statements", "also_today",
)

# Common brief words carrying no story identity — dropped before comparing titles
# so two items match on their substantive terms, not boilerplate.
_DEDUP_STOP = {
    "japan", "japans", "japanese", "tokyo", "the", "and", "for", "with", "over",
    "from", "into", "amid", "after", "before", "prime", "minister", "ministry",
    "government", "govt", "new", "first", "say", "says", "said", "report",
    "reports", "reported", "that", "this", "its", "are", "was", "were", "has",
    "have", "will", "would", "could", "takaichi", "today", "week", "plan",
    "plans", "move", "moves", "call", "calls", "amid",
}

# Fields that may carry an item's identifying text, across all section shapes.
_IDENTITY_FIELDS = (
    "headline", "title", "action", "detail", "name", "position", "committee",
    "who", "quote_text", "central_argument", "body", "summary",
)


def _norm_title(s) -> str:
    return _re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def _primary_title(item: dict) -> str:
    """The item's normalized primary title (first present identity field)."""
    for f in _IDENTITY_FIELDS:
        v = item.get(f)
        if isinstance(v, str) and v.strip():
            return _norm_title(v)
    return ""


def _item_text(item: dict) -> str:
    """All identifying text of an item concatenated (works across section shapes)."""
    return " ".join(str(item.get(f)) for f in _IDENTITY_FIELDS
                    if isinstance(item.get(f), str) and item.get(f).strip())


def _sig_tokens(text: str) -> frozenset:
    """Significant title tokens (≥3 chars, minus boilerplate) — the fingerprint
    used for near-duplicate matching of the same story worded differently."""
    return frozenset(t for t in _re.findall(r"[a-z0-9]+", str(text).lower())
                     if len(t) >= 3 and t not in _DEDUP_STOP)


def _item_url(item: dict) -> str:
    u = (item.get("url") or "").strip()
    return u if u.startswith("http") else ""


def _near_dup(toks: frozenset, seen_tok_sets: list) -> bool:
    """True if `toks` is essentially contained in a previously-seen fingerprint —
    the same story reworded. Conservative: needs ≥5 shared substantive tokens and
    ≥80% of the smaller set, so genuinely distinct stories are not merged."""
    if len(toks) < 5:
        return False
    for s in seen_tok_sets:
        if len(s) < 5:
            continue
        inter = len(toks & s)
        if inter >= 5 and inter / min(len(toks), len(s)) >= 0.8:
            return True
    return False


def _dedupe_sections(digest: dict) -> dict:
    """Drop any item that already appeared in a higher-priority section — matched
    by URL, identical headline, OR a near-identical reworded title — so one story
    occupies exactly one section of the edition."""
    seen_urls: set = set()
    seen_titles: set = set()
    seen_tok_sets: list = []
    removed = 0

    def _sweep(items):
        nonlocal removed
        kept = []
        for it in (items or []):
            if not isinstance(it, dict):
                kept.append(it)
                continue
            url = _item_url(it)
            title = _primary_title(it)
            toks = _sig_tokens(_item_text(it))
            if (url and url in seen_urls) or (title and title in seen_titles) \
                    or _near_dup(toks, seen_tok_sets):
                removed += 1
                continue
            if url:
                seen_urls.add(url)
            if title:
                seen_titles.add(title)
            if toks:
                seen_tok_sets.append(toks)
            kept.append(it)
        return kept

    digest["top_stories"] = _sweep(digest.get("top_stories"))
    digest["overnight_items"] = _sweep(digest.get("overnight_items"))
    trade = digest.get("us_china_trade")
    if isinstance(trade, dict) and trade.get("deals"):
        trade["deals"] = _sweep(trade.get("deals"))
    for section in _DEDUPE_ORDER[2:]:
        digest[section] = _sweep(digest.get(section))

    if removed:
        print(f"   ✓ Removed {removed} within-edition duplicate item(s)")
    return digest


# ── Cross-day de-duplication: the "already published" ledger ──────────────────

def _load_ledger() -> list:
    """Load the rolling published-item ledger (list of {date,url,title}); [] if none."""
    try:
        data = json.loads(LEDGER_JSON.read_text(encoding="utf-8"))
        return data.get("entries", []) if isinstance(data, dict) else []
    except Exception:
        return []


def _ledger_recent_keys(entries: list, today, window: int = _LEDGER_WINDOW_DAYS):
    """URLs and titles published within the trailing `window` days."""
    cutoff = today - timedelta(days=window)
    urls, titles = set(), set()
    for e in entries:
        try:
            d = datetime.strptime(str(e.get("date", "")), "%Y-%m-%d").date()
        except Exception:
            continue
        if d < cutoff:
            continue
        if e.get("url"):
            urls.add(e["url"])
        if e.get("title"):
            titles.add(e["title"])
    return urls, titles


def _dedupe_cross_day(digest: dict, prev_urls: set, prev_titles: set) -> dict:
    """Drop items already published in a recent edition. Conservative: matches the
    SAME article URL or an identical headline, so genuine follow-up coverage (a new
    article advancing the story) still comes through — only literal repeats go."""
    removed = 0

    def _keep(it) -> bool:
        nonlocal removed
        if not isinstance(it, dict):
            return True
        u = _item_url(it)
        t = _primary_title(it)
        if (u and u in prev_urls) or (t and t in prev_titles):
            removed += 1
            return False
        return True

    for section in _DEDUPE_ORDER:
        items = digest.get(section)
        if isinstance(items, list):
            digest[section] = [it for it in items if _keep(it)]
    trade = digest.get("us_china_trade")
    if isinstance(trade, dict) and isinstance(trade.get("deals"), list):
        trade["deals"] = [it for it in trade["deals"] if _keep(it)]

    if removed:
        print(f"   ✓ Removed {removed} item(s) already published in the last "
              f"{_LEDGER_WINDOW_DAYS} days")
    return digest


def _record_ledger(digest: dict, today_iso: str) -> None:
    """Append this edition's items to the ledger and prune to the rolling window.
    Called only for real (archived) editions, so test runs don't poison it."""
    entries = _load_ledger()

    def _add(it):
        if not isinstance(it, dict):
            return
        u, t = _item_url(it), _primary_title(it)
        if u or t:
            entries.append({"date": today_iso, "url": u, "title": t})

    for section in _DEDUPE_ORDER:
        for it in (digest.get(section) or []):
            _add(it)
    trade = digest.get("us_china_trade")
    if isinstance(trade, dict):
        for it in (trade.get("deals") or []):
            _add(it)

    try:
        cutoff = datetime.strptime(today_iso, "%Y-%m-%d").date() - timedelta(days=_LEDGER_WINDOW_DAYS)
    except Exception:
        cutoff = None
    pruned = []
    for e in entries:
        try:
            d = datetime.strptime(str(e.get("date", "")), "%Y-%m-%d").date()
        except Exception:
            continue
        if cutoff is None or d >= cutoff:
            pruned.append(e)
    LEDGER_JSON.write_text(json.dumps({"entries": pruned}, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(f"   ✓ Published-ledger updated ({len(pruned)} entries kept, last {_LEDGER_WINDOW_DAYS}d)")


# Recognized Japanese pollsters — only these may appear in approval_polls.
_ALLOWED_POLLSTERS = ("nhk", "nikkei", "jiji", "yomiuri", "asahi", "kyodo",
                      "mainichi", "ann", "jnn", "fnn")
# A clean approval value is a bare percentage, e.g. "41%" / "~42%" / "40.5 %".
_PCT_RE = _re.compile(r"^\s*[~≈]?\s*\d{1,3}(\.\d)?\s*%\s*$")


def _clean_pct(v):
    """Return the value if it is a bare percentage string, else None."""
    if v is None:
        return None
    s = str(v).strip()
    return s if _PCT_RE.match(s) else None


def _pct_to_float(v):
    """Extract the numeric value of a percentage string ('49.0%' → 49.0), else None."""
    if v is None:
        return None
    m = _re.search(r"\d{1,3}(?:\.\d+)?", str(v))
    return float(m.group(0)) if m else None


def _wiki_agrees_with_baseline(wiki: list, baseline: list, tol: float = 5.0) -> bool:
    """SAFETY CROSS-CHECK for the live Wikipedia fetch, which can't be eyeballed
    from the dev sandbox. Trust the parsed set only if, for every pollster that
    appears in BOTH the fetch and the hand-verified baseline, the approval figures
    agree within `tol` points — and at least one such anchor exists. A subtly
    broken parse (wrong column, party vote-share, stale row) will miss the anchor
    and this returns False, so the pipeline falls back to the baseline instead of
    shipping a wrong number. No anchor overlap → not verifiable → not trusted."""
    base = {}
    for p in baseline:
        f = _pct_to_float(p.get("cabinet_approval"))
        if f is not None:
            base[str(p.get("pollster", "")).strip().lower()] = f
    anchors = 0
    for p in wiki:
        key = str(p.get("pollster", "")).strip().lower()
        if key in base:
            f = _pct_to_float(p.get("cabinet_approval"))
            if f is None or abs(f - base[key]) > tol:
                print(f"   ⚠ Polls: Wikipedia '{p.get('pollster')}' {p.get('cabinet_approval')} "
                      f"disagrees with verified {base[key]:g}% (>{tol:g} pts) — using baseline")
                return False
            anchors += 1
    return anchors > 0


def _resolve_tariffs(digest: dict) -> dict:
    """Force the US-tariffs-on-Japan reference figures to databases.TARIFF_FACTS,
    OVERRIDING the model — which repeatedly carried stale tariff facts forward (an
    expired Section 122 surcharge displayed for a month). Day-specific fields
    (last_change, next_trigger, deals) are left to the model. Update the figures in
    databases.TARIFF_FACTS, the single source of truth for the tariff box."""
    try:
        from databases import TARIFF_FACTS
    except Exception as e:
        print(f"   ⚠ Tariff facts unavailable ({e}) — leaving model values")
        return digest
    trade = digest.get("us_china_trade")
    if not isinstance(trade, dict):
        trade = {}
        digest["us_china_trade"] = trade
    tt = trade.get("tariff_tracker")
    if not isinstance(tt, dict):
        tt = {}
        trade["tariff_tracker"] = tt
    tt.update(TARIFF_FACTS)                 # authoritative reference figures win
    tt.pop("section_301_watch", None)       # drop the stale legacy key/label
    print("   ✓ Tariff facts set from authoritative baseline (databases.TARIFF_FACTS)")
    return digest


def _resolve_polls(digest: dict, wiki_polls: list | None = None) -> dict:
    """Populate the Public Sentiment table from AUTHORITATIVE structured data —
    the Wikipedia poll fetch if it returned a sane set that AGREES with the
    verified baseline on overlapping pollsters, else the verified
    RECENT_APPROVAL_POLLS baseline — overriding the model's unreliable
    news-scraped numbers (which produced wrong figures like Jiji '51%')."""
    try:
        from databases import RECENT_APPROVAL_POLLS
    except Exception:
        RECENT_APPROVAL_POLLS = []
    # The Wikipedia fetch is trusted over the baseline only when (a) TRUST_WIKI_POLLS
    # is enabled, (b) it returned ≥3 pollster rows, AND (c) it passes the anchor
    # cross-check against the hand-verified baseline. Any failure → baseline wins,
    # so no wrong figure can reach the email even though the live page can't be
    # inspected from the dev sandbox.
    trust_wiki = os.environ.get("TRUST_WIKI_POLLS", "").strip().lower() in ("1", "true", "yes")
    wiki = [p for p in (wiki_polls or []) if isinstance(p, dict)] if trust_wiki else []
    if len(wiki) >= 3 and _wiki_agrees_with_baseline(wiki, RECENT_APPROVAL_POLLS):
        structured = wiki
        source = "Wikipedia fetch (baseline-verified)"
    else:                                        # not trusted / thin / failed check → baseline
        structured = [dict(p) for p in RECENT_APPROVAL_POLLS]
        source = "verified baseline"
    if not structured:
        return digest
    ps = digest.get("public_sentiment")
    if not isinstance(ps, dict):
        ps = {}
        digest["public_sentiment"] = ps
    ps["approval_polls"] = structured
    ps.pop("approval_polling", None)
    print(f"   ✓ Polls: {len(structured)} authoritative pollster figures ({source})")
    return digest


def _sanitise_polls(digest: dict) -> dict:
    """Drop approval polls that don't cite a recognized Japanese pollster with a
    clean numeric percentage — prevents prose ('approximately 40% range…') and
    foreign/aggregate sources ('Multiple CGTN/Chosunbiz') from rendering."""
    ps = digest.get("public_sentiment")
    if not isinstance(ps, dict):
        return digest
    polls = ps.get("approval_polls")
    if not polls:
        legacy = ps.get("approval_polling")
        polls = [legacy] if isinstance(legacy, dict) else []
    clean = []
    for p in polls:
        if not isinstance(p, dict):
            continue
        pollster = str(p.get("pollster", "")).strip()
        if not any(a in pollster.lower() for a in _ALLOWED_POLLSTERS):
            continue  # foreign / "Multiple" / non-pollster → drop
        appr = _clean_pct(p.get("cabinet_approval"))
        if not appr:
            continue  # no clean approval % → drop the whole poll
        p2 = dict(p)
        p2["cabinet_approval"] = appr
        p2["cabinet_disapproval"] = _clean_pct(p.get("cabinet_disapproval"))
        clean.append(p2)
    ps["approval_polls"] = clean
    ps.pop("approval_polling", None)  # normalize to the array form
    dropped = len(polls) - len(clean)
    if dropped > 0:
        print(f"   ✓ Polls: kept {len(clean)}/{len(polls)} (dropped non-Japanese-pollster or non-numeric)")
    return digest


def _archive_html(html: str, digest: dict) -> None:
    """Write the dated HTML to public/ for GitHub Pages."""
    PUBLIC_DIR.mkdir(exist_ok=True)
    date_str = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")

    dated_file = PUBLIC_DIR / f"{date_str}.html"
    dated_file.write_text(html, encoding="utf-8")

    latest_file = PUBLIC_DIR / "index.html"
    latest_file.write_text(html, encoding="utf-8")

    archive_index = PUBLIC_DIR / "archive.json"
    archive = []
    if archive_index.exists():
        try:
            archive = json.loads(archive_index.read_text())
        except json.JSONDecodeError:
            archive = []

    entry = {
        "date": date_str,
        "filename": f"{date_str}.html",
        "top_stories": len(digest.get("top_stories") or []),
        "overnight_items": len(digest.get("overnight_items") or []),
        "word_count": _count_words(digest),
    }
    archive = [a for a in archive if a.get("date") != date_str]
    archive.insert(0, entry)
    archive_index.write_text(json.dumps(archive[:120], indent=2))

    print(f"📁 Archived to {dated_file.name}")


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(args: argparse.Namespace) -> int:
    """Execute the full pipeline. Returns exit code."""
    print(f"\n{'=' * 64}")
    print(f"  JAPAN DAILY BRIEF — {datetime.now(ZoneInfo('America/New_York')).strftime('%A, %B %-d, %Y at %I:%M %p ET')}")
    print(f"{'=' * 64}\n")

    pipeline_start = time.time()

    # ─── Collect ─────────────────────────────────────────────────────────
    if args.from_cache and COLLECTED_JSON.exists():
        print("📂 Loading cached collection from disk...")
        payload = json.loads(COLLECTED_JSON.read_text(encoding="utf-8"))
        print(f"   • Loaded {sum(len(v) for k, v in payload.items() if isinstance(v, list))} articles")
    else:
        print("🌐 Collecting from RSS feeds...")
        from collect import collect_all
        payload = collect_all()
        COLLECTED_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
        total = sum(len(v) for k, v in payload.items() if isinstance(v, list))
        unique_sources = set()
        for tier in ("tier1", "tier2", "tier3", "tier4"):
            for art in payload.get(tier, []):
                src = art.get("source")
                if src:
                    unique_sources.add(src)
        print(f"   • {total} articles from {len(unique_sources)} unique sources")

    if args.dry_run:
        print(f"\n✅ Dry run complete. Cached to {COLLECTED_JSON.name}")
        return 0

    # ─── Google News URLs are decoded post-digest in _sanitise_urls ──────
    # (only the ~30 URLs that actually land in the digest, not all ~120 —
    # avoids hammering Google's endpoint and tripping rate limits).

    # ─── Reference database context (Japan timelines) ────────────────────
    db_context = ""
    try:
        from databases import build_db_context
        db_context = build_db_context()
        if db_context:
            print(f"📊 Reference context loaded ({len(db_context)} chars)")
    except Exception as e:
        print(f"⚠ Reference context unavailable: {e}")

    # ─── Digest ──────────────────────────────────────────────────────────
    print("\n🤖 Generating digest...")
    from digest import generate_digest
    digest = generate_digest(payload, db_context=db_context)

    # ─── Sanitise URLs ───────────────────────────────────────────────────
    print("\n🔗 Sanitising URLs...")
    collected_by_url: dict = {}
    for tier in ("tier1", "tier2", "tier3", "tier4", "pm_tracker_articles"):
        for art in (payload.get(tier) or []):
            u = art.get("url", "")
            if u:
                collected_by_url.setdefault(u, art.get("title", ""))
    # Attach each item's ORIGINAL collected headline before URLs are resolved
    # (while item['url'] still matches the collected article) — preserves a
    # verbatim, traceable source title behind any synthesized display headline.
    digest = _attach_orig_titles(digest, collected_by_url)
    digest = _sanitise_urls(digest, set(collected_by_url))
    print(f"   ✓ URL sanitisation complete ({len(collected_by_url)} collected URLs as reference)")

    # ─── De-duplicate across sections (one article, one section) ─────────
    digest = _dedupe_sections(digest)
    # ─── De-duplicate across DAYS (drop stories already sent recently) ───
    today_et = datetime.now(ZoneInfo("America/New_York")).date()
    _prev_urls, _prev_titles = _ledger_recent_keys(_load_ledger(), today_et)
    digest = _dedupe_cross_day(digest, _prev_urls, _prev_titles)
    # ─── Polls: authoritative structured figures (Wikipedia fetch → baseline) ─
    digest = _resolve_polls(digest, payload.get("wiki_polls"))
    # ─── Clean approval polls (recognized Japanese pollsters + numeric only)
    digest = _sanitise_polls(digest)
    # ─── Tariffs: authoritative US-on-Japan figures (override the model) ──
    digest = _resolve_tariffs(digest)

    DIGEST_JSON.write_text(json.dumps(digest, ensure_ascii=False, indent=2),
                          encoding="utf-8")

    # ─── Update persistent trackers ──────────────────────────────────────
    try:
        from pm_tracker import update_from_digest as update_pm
        update_pm(digest)
    except Exception as e:
        print(f"⚠ PM tracker update failed (non-fatal): {e}")

    try:
        from region_tracker import update_from_digest as update_region
        update_region(digest)
    except Exception as e:
        print(f"⚠ Region tracker update failed (non-fatal): {e}")

    # ─── Validate ────────────────────────────────────────────────────────
    print("\n🔍 Validating digest...")
    failures = _validate_digest(digest)
    if failures:
        print("⚠ Validation failures:")
        for f in failures:
            print(f"   • {f}")
        if not args.force_send:
            print("\n   Use --force-send to override validation gate.")
    else:
        print("   ✓ All validation checks passed")

    # ─── Render ──────────────────────────────────────────────────────────
    print("\n🎨 Rendering HTML email...")
    from render import render_html
    html = render_html(digest)
    DIGEST_HTML.write_text(html, encoding="utf-8")
    print(f"   • Wrote {len(html):,} bytes to {DIGEST_HTML.name}")

    # ─── Archive ─────────────────────────────────────────────────────────
    if not args.no_archive:
        _archive_html(html, digest)
        # Record what actually went out, so later editions won't repeat it.
        # Only real (archived) editions update the ledger; test runs don't.
        _record_ledger(digest, today_et.isoformat())

    # ─── Update README ───────────────────────────────────────────────────
    try:
        from update_readme import update_readme
        update_readme()
    except Exception as e:
        print(f"⚠ README update failed (non-fatal): {e}")

    # ─── Send ────────────────────────────────────────────────────────────
    if args.no_send:
        print("\n📭 --no-send: skipping email send.")
    else:
        print("\n📧 Sending email...")
        from send_email import send_digest
        sent = send_digest(html)
        if not sent:
            print("   ⚠ Send failed or skipped")

    elapsed = time.time() - pipeline_start
    print(f"\n{'=' * 64}")
    print(f"  ✅ Pipeline complete in {elapsed:.0f}s")
    print(f"{'=' * 64}\n")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Japan Daily Brief — orchestration entry point"
    )
    parser.add_argument("--dry-run", action="store_true",
                       help="Collect only; skip digest/render/send")
    parser.add_argument("--from-cache", action="store_true",
                       help="Reuse cached collected.json (skip collection)")
    parser.add_argument("--no-send", action="store_true",
                       help="Generate HTML but don't email")
    parser.add_argument("--no-archive", action="store_true",
                       help="Skip writing to public/ archive")
    parser.add_argument("--force-send", action="store_true",
                       help="Send even if validation gates fail")
    args = parser.parse_args()

    try:
        return run_pipeline(args)
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
