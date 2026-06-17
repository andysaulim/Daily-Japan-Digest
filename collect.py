"""
Japan Daily Brief — Collector

Scrapes RSS feeds across four tiers + market data + PM-appearance feeds.
Mirrors the Daily-Korea-Digest / Daily-China-Digest collector architecture with
Japan-specific sources.

Uses threaded fetching for performance (~15s vs ~60s sequential).
"""

import feedparser
import requests
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta


# ─────────────────────────────────────────────────────────────────────────────
# FEED CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

def _gnews(query: str) -> str:
    """Build a Google News RSS search URL."""
    return f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"


# ── TIER 1: NEWS (24h window) ─────────────────────────────────────────────────
TIER1_FEEDS = {
    # ── Major international — Japan coverage ────────────────────────────────
    "WSJ Japan":          _gnews("Japan+site:wsj.com"),
    "NYT Japan":          _gnews("Japan+site:nytimes.com"),
    "WaPo Japan":         _gnews("Japan+site:washingtonpost.com"),
    "FT Japan":           _gnews("Japan+site:ft.com"),
    "Reuters Japan":      _gnews("Japan+site:reuters.com"),
    "AP Japan":           _gnews("Japan+site:apnews.com"),
    "AFP Japan":          _gnews("Japan+site:afp.com"),
    "Bloomberg Japan":    _gnews("Japan+site:bloomberg.com"),
    "BBC Japan":          _gnews("Japan+site:bbc.com"),
    "CNN Japan":          _gnews("Japan+site:cnn.com"),
    "CNBC Japan":         _gnews("Japan+site:cnbc.com"),
    "Economist Japan":    _gnews("Japan+site:economist.com"),
    "Guardian Japan":     _gnews("Japan+site:theguardian.com"),

    # ── Japanese press in English ───────────────────────────────────────────
    "NHK World":          _gnews("site:www3.nhk.or.jp/nhkworld"),
    "Kyodo News":         _gnews("site:english.kyodonews.net"),
    "Japan Times":        _gnews("site:japantimes.co.jp"),
    "Mainichi":           _gnews("site:mainichi.jp/english"),
    "Asahi AJW":          _gnews("site:asahi.com/ajw"),
    "Japan News (Yomiuri)": _gnews("site:the-japan-news.com"),
    "Nikkei Asia":        _gnews("Japan+site:asia.nikkei.com"),
    "Jiji Press":         _gnews("Japan+site:jiji.com+OR+%22Jiji+Press%22"),
    "Japan Forward":      _gnews("site:japan-forward.com"),

    # ── US Government — Japan-relevant ──────────────────────────────────────
    "White House Japan":  _gnews("Japan+site:whitehouse.gov"),
    "State Dept Japan":   _gnews("Japan+site:state.gov"),
    "Pentagon Japan":     _gnews("Japan+site:defense.gov"),
    "Treasury Japan":     _gnews("Japan+site:treasury.gov"),
    "USTR Japan":         _gnews("Japan+site:ustr.gov"),
    "Commerce Japan":     _gnews("Japan+site:commerce.gov"),
    "INDOPACOM":          _gnews("Japan+OR+%22Self-Defense%22+site:pacom.mil"),
    "USFJ":               _gnews("%22U.S.+Forces+Japan%22+OR+site:usfj.mil"),

    # ── Japanese Government (English) ───────────────────────────────────────
    "Kantei / PMO":       _gnews("site:japan.kantei.go.jp"),
    "MOFA Japan":         _gnews("site:mofa.go.jp"),
    "MOD Japan":          _gnews("site:mod.go.jp"),
    "METI Japan":         _gnews("site:meti.go.jp"),
    "MOF Japan":          _gnews("site:mof.go.jp"),
    "Bank of Japan":      _gnews("site:boj.or.jp"),

    # ── Regional reaction layer ─────────────────────────────────────────────
    "Yonhap re Japan":    _gnews("Japan+site:en.yna.co.kr"),
    "Korea Herald re Japan": _gnews("Japan+site:koreaherald.com"),
    "Global Times re Japan": _gnews("Japan+site:globaltimes.cn"),
    "Xinhua re Japan":    _gnews("Japan+site:xinhuanet.com"),
    "TASS re Japan":      _gnews("Japan+site:tass.com"),

    # ── Specialist Japan outlets ────────────────────────────────────────────
    "The Diplomat Japan": _gnews("Japan+site:thediplomat.com"),
    "Tokyo Review":       _gnews("site:tokyoreview.net"),
    "Observing Japan":    _gnews("site:observingjapan.com+OR+%22Observing+Japan%22"),
}


# ── TIER 2: ANALYSIS (36h window) ─────────────────────────────────────────────
TIER2_FEEDS = {
    # CSIS in-house — highest priority
    "CSIS Japan Chair":        (_gnews("Japan+site:csis.org"), "A"),

    # Top-tier think tanks with named Japan experts
    "Brookings (Solís)":       (_gnews("Japan+site:brookings.edu"), "A"),
    "CFR (Sheila Smith)":      (_gnews("Japan+site:cfr.org"), "A"),
    "RAND (Hornung) Japan":    ("https://www.rand.org/topics/japan.xml", "A"),
    "Carnegie Japan":          (_gnews("Japan+site:carnegieendowment.org"), "A"),
    "Stimson Japan":           (_gnews("Japan+site:stimson.org"), "A"),
    "Hudson Japan":            (_gnews("Japan+site:hudson.org"), "B"),
    "Sasakawa USA":            (_gnews("site:spfusa.org+OR+%22Sasakawa+USA%22"), "A"),
    "Sasakawa Peace Fdn":      (_gnews("site:spf.org+Japan"), "B"),
    "NBR Japan":               (_gnews("Japan+site:nbr.org"), "A"),
    "East-West Center":        (_gnews("Japan+site:eastwestcenter.org"), "B"),
    "Lowy Japan":              (_gnews("Japan+site:lowyinstitute.org"), "B"),
    "IISS Japan":              (_gnews("Japan+site:iiss.org"), "A"),
    "Atlantic Council Japan":  (_gnews("Japan+site:atlanticcouncil.org"), "B"),
    "USIP Japan":              (_gnews("Japan+site:usip.org"), "B"),
    "GMF Japan":               (_gnews("Japan+site:gmfus.org"), "B"),
    "Asia Society Policy":     (_gnews("Japan+site:asiasociety.org/policy-institute"), "B"),

    # University Japan programs (via Google News)
    "MIT/Harvard/G'town Japan": (_gnews("Japan+(%22Reischauer%22+OR+%22MIT+Japan%22+OR+%22Georgetown%22)+policy"), "B"),

    # Generalist with strong Japan coverage
    "Foreign Affairs Japan":   (_gnews("Japan+site:foreignaffairs.com"), "A"),
    "Foreign Policy Japan":    (_gnews("Japan+site:foreignpolicy.com"), "B"),
    "War on the Rocks Japan":  (_gnews("Japan+site:warontherocks.com"), "B"),
}


# ── TIER 3: ACADEMIC JOURNALS (72h window) ────────────────────────────────────
TIER3_FEEDS = {
    # A+ tier — top IR/security journals
    "Int'l Security":          (_gnews("%22International+Security%22+%22Japan%22"), "A+"),
    "Int'l Organization":      (_gnews("%22International+Organization%22+%22Japan%22"), "A+"),

    # A tier — strong IR / security / area studies
    "Security Studies":        (_gnews("%22Security+Studies%22+%22Japan%22"), "A"),
    "Washington Quarterly":    (_gnews("%22Washington+Quarterly%22+%22Japan%22"), "A"),
    "Survival IISS":           (_gnews("%22Survival%22+IISS+%22Japan%22"), "A"),
    "J. Strategic Studies":    (_gnews("%22Journal+of+Strategic+Studies%22+%22Japan%22"), "A"),
    "J. East Asian Studies":   (_gnews("%22Journal+of+East+Asian+Studies%22+%22Japan%22"), "A"),

    # B tier — Japan / Asia specialist journals
    "Asian Survey":            (_gnews("%22Asian+Survey%22+%22Japan%22"), "B"),
    "Pacific Affairs":         (_gnews("%22Pacific+Affairs%22+%22Japan%22"), "B"),
    "J. Japanese Studies":     (_gnews("%22Journal+of+Japanese+Studies%22"), "B"),
    "Social Science Japan J.": (_gnews("%22Social+Science+Japan+Journal%22"), "B"),
}


# ── TIER 4: JAPANESE GOVERNMENT PRIMARY + ADVERSARY SIGNAL (48h window) ────────
TIER4_FEEDS = {
    # Japanese government primary
    "Kantei / PM":         _gnews("%22Prime+Minister%22+Japan+statement+OR+%22press+conference%22+site:japan.kantei.go.jp"),
    "Chief Cabinet Sec":   _gnews("%22Chief+Cabinet+Secretary%22+Japan+press+conference"),
    "MOFA presser":        _gnews("Japan+%22Foreign+Ministry%22+OR+%22MOFA%22+press+conference+OR+statement"),
    "MOD / Joint Staff":   _gnews("Japan+%22Joint+Staff%22+OR+%22Defense+Ministry%22+scramble+OR+incursion+OR+statement"),
    "METI statements":     _gnews("Japan+%22METI%22+OR+%22Ministry+of+Economy%22+statement+OR+policy"),
    "BOJ statements":      _gnews("%22Bank+of+Japan%22+statement+OR+%22policy+meeting%22+OR+Ueda"),

    # Adversary signal toward Japan
    "China MOFA re Japan": _gnews("China+%22Foreign+Ministry%22+Japan+OR+Senkaku+statement+OR+spokesperson"),
    "DPRK re Japan":       _gnews("%22North+Korea%22+missile+OR+launch+Japan+OR+%22Sea+of+Japan%22+OR+KCNA"),
    "Russia re Japan":     _gnews("Russia+Japan+%22Northern+Territories%22+OR+Kuril+statement+OR+TASS"),
}


# ── PM APPEARANCE TRACKER (72h window) ────────────────────────────────────────
# Robust to PM turnover: a generic "Japan Prime Minister" query plus a
# last-known-name secondary query ("Ishiba"). Live articles are authoritative.
PM_TRACKER_FEEDS = {
    "PM appearance":       _gnews("%22Japanese+Prime+Minister%22+OR+%22Japan%27s+Prime+Minister%22+attended+OR+visited+OR+met+OR+spoke"),
    "PM Diet":             _gnews("Japan+%22Prime+Minister%22+Diet+OR+%22Lower+House%22+OR+%22Upper+House%22+session"),
    "PM press conf":       _gnews("Japan+%22Prime+Minister%22+%22press+conference%22+OR+statement+OR+remarks"),
    "PM diplomacy":        _gnews("Japan+%22Prime+Minister%22+summit+OR+bilateral+OR+%22telephone+talks%22"),
    "PM (Ishiba)":         _gnews("%22Ishiba%22+Japan+Prime+Minister"),
}


# ── KEYWORD FILTERS ───────────────────────────────────────────────────────────
JAPAN_KEYWORDS = re.compile(
    r"\bjapan\b|\bjapanese\b|\btokyo\b|\bdiet\b|\bkantei\b|\bldp\b"
    r"|\bkomeito\b|\bcdp\b|\bdpp\b|\bself[\s-]?defense\b|\bjsdf\b|\bsdf\b"
    r"|\bsenkaku\b|\bdiaoyu\b|\bokinawa\b|\busfj\b|\bnansei\b|\bryukyu\b"
    r"|\bnikkei\b|\btopix\b|\bboj\b|\bbank\s*of\s*japan\b|\byen\b|\bueda\b"
    r"|\bprime\s*minister\b.*\bjapan\b|\bishiba\b|\bnorthern\s*territories\b"
    r"|\bkuril\b|\babe\b|\bkishida\b"
    r"|日本|日本人|東京|自民党|国会|尖閣|防衛省|外務省|日銀|沖縄|自衛隊",
    re.IGNORECASE,
)

# Filter out lifestyle/celebrity content (parallel to Korea's K-pop block).
# Blocks J-pop / idol / anime-only / celebrity items unless a policy/security angle.
_LIFESTYLE_FILTER = re.compile(
    r"\b(j-?pop|idol\s*group|boy\s*band|girl\s*band|anime|manga\s*review"
    r"|celebrity|gossip|fashion\s*week|movie\s*review|album\s*review"
    r"|red\s*carpet|paparazzi|reality\s*tv|netflix\s*series|cosplay)\b",
    re.IGNORECASE,
)


# ── PRESTIGE JOURNALIST FLAGGING (Japan correspondents) ───────────────────────
PRESTIGE_JOURNALISTS = {
    # NYT Tokyo
    "Motoko Rich", "River Akira Davis", "Hisako Ueno",
    # FT Tokyo
    "Leo Lewis", "Kana Inagaki", "Harry Dempsey",
    # WSJ Tokyo
    "Peter Landers", "Megumi Fujikawa", "Miho Inada",
    # Reuters Tokyo
    "Tim Kelly", "Kiyoshi Takenaka", "Sakura Murakami",
    # Bloomberg Tokyo
    "Isabel Reynolds", "Yuko Takeo",
    # Nikkei
    "Rurika Imahashi",
}


# ── INFRASTRUCTURE ────────────────────────────────────────────────────────────
REQUEST_TIMEOUT = 8
HEADERS = {"User-Agent": "CSISJapanDigest/1.0"}
MAX_WORKERS = 25

_source_health: dict[str, dict] = {}
MAJOR_FEEDS = {"Reuters Japan", "AP Japan", "WSJ Japan", "FT Japan",
               "Bloomberg Japan", "NHK World", "Kyodo News"}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _parse_feed(url: str) -> list:
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers=HEADERS)
            if resp.status_code in (401, 403):
                print(f"  ⚠ Feed blocked ({resp.status_code}): {url[:80]}")
                return []
            resp.raise_for_status()
            return feedparser.parse(resp.content).entries
        except (requests.ConnectionError, requests.Timeout) as e:
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            print(f"  ⚠ Feed error (after 3 tries): {e}")
            return []
        except Exception as e:
            print(f"  ⚠ Feed error: {e}")
            return []
    return []


def _real_url_from_gnews_entry(entry, gnews_link: str, raw_summary: str) -> str:
    """Extract the real article URL from a Google News RSS entry."""
    # Method 1 — feedparser alternate links
    for lk in (getattr(entry, "links", None) or []):
        href = lk.get("href", "")
        if href and href.startswith("http") and "news.google.com" not in href:
            return href

    # Method 2 — first non-Google href in summary HTML
    if raw_summary:
        m = re.search(r"""href=["'](https?://(?!news\.google\.com)[^"'<>\s]+)""", raw_summary)
        if m:
            return m.group(1).replace("&amp;", "&").replace("&#38;", "&")

    return gnews_link  # fallback — Google News URL (better than empty)


def _entry_to_article(entry, source: str, lang: str = "EN",
                      extra: dict | None = None) -> dict:
    title = entry.get("title", "").strip()
    raw_link = entry.get("link", "").strip()
    raw_summary = entry.get("summary", entry.get("description", ""))

    link = (_real_url_from_gnews_entry(entry, raw_link, raw_summary)
            if "news.google.com" in raw_link else raw_link)

    summary = re.sub(r"<[^>]+>", " ", raw_summary)
    summary = re.sub(r"\s+", " ", summary).strip()

    pub_date = None
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            pub_date = datetime(*parsed[:6], tzinfo=timezone.utc).isoformat()
            break

    tags = []
    for tag in getattr(entry, "tags", []) or []:
        term = tag.get("term", "").strip()
        if term:
            tags.append(term)

    article = {
        "title": title,
        "url": link,
        "summary": summary[:800],
        "source": source,
        "lang": lang,
        "pub_date": pub_date,
    }
    if tags:
        article["tags"] = tags
    if extra:
        article.update(extra)
    return article


def _is_recent(entry, hours: int = 48) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            return datetime(*parsed[:6], tzinfo=timezone.utc) >= cutoff
    return True


def _is_japan_related(entry) -> bool:
    text = f"{entry.get('title', '')} {entry.get('summary', entry.get('description', ''))}"
    return bool(JAPAN_KEYWORDS.search(text))


def _is_lifestyle(entry) -> bool:
    text = f"{entry.get('title', '')} {entry.get('summary', entry.get('description', ''))}"
    return bool(_LIFESTYLE_FILTER.search(text))


def _flag_journalist(article: dict) -> dict:
    text = f"{article['title']} {article['summary']}".lower()
    for name in PRESTIGE_JOURNALISTS:
        if name.lower() in text:
            article["flagged_journalist"] = name
            break
    return article


def _dedup(articles: list) -> list:
    seen = set()
    out = []
    for a in articles:
        if a["url"] and a["url"] not in seen:
            seen.add(a["url"])
            out.append(a)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# PARALLEL FEED FETCHER
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_feeds_parallel(feed_dict: dict, is_tiered: bool = False) -> dict:
    """Fetch all feeds in parallel. Returns {source: (entries, extra_info)}."""
    results = {}

    def _fetch_one(source, url_or_tuple):
        if is_tiered:
            url, tier_val = url_or_tuple
        else:
            url = url_or_tuple
            tier_val = None
        entries = _parse_feed(url)
        return source, entries, tier_val

    items = list(feed_dict.items())
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(_fetch_one, src, val): src for src, val in items}
        for future in as_completed(futures):
            src = futures[future]
            try:
                source, entries, tier_val = future.result()
                results[source] = (entries, tier_val)
                _source_health[source] = {
                    "articles": len(entries),
                    "success": len(entries) > 0,
                    "error_msg": None,
                }
            except Exception as e:
                print(f"  ⚠ Thread error: {e}")
                _source_health[src] = {
                    "articles": 0,
                    "success": False,
                    "error_msg": str(e),
                }

    return results


# ─────────────────────────────────────────────────────────────────────────────
# TIER COLLECTORS
# ─────────────────────────────────────────────────────────────────────────────

# Reserved for future Japanese-language source additions (lang="JP" tagging)
_JAPANESE_LANG_SOURCES: set[str] = set()


def _collect_tier1() -> list:
    articles = []
    results = _fetch_feeds_parallel(TIER1_FEEDS)
    for source, (entries, _) in results.items():
        lang = "JP" if source in _JAPANESE_LANG_SOURCES else "EN"
        for entry in entries:
            if not _is_recent(entry, hours=24):
                continue
            if not _is_japan_related(entry):
                continue
            if _is_lifestyle(entry):
                continue
            article = _entry_to_article(entry, source, lang=lang)
            article = _flag_journalist(article)
            articles.append(article)
    return _dedup(articles)


def _collect_tier2() -> list:
    articles = []
    results = _fetch_feeds_parallel(TIER2_FEEDS, is_tiered=True)
    for source, (entries, prestige) in results.items():
        for entry in entries:
            if not _is_recent(entry, hours=36):
                continue
            if not _is_japan_related(entry):
                continue
            article = _entry_to_article(entry, source, extra={
                "prestige_tier": prestige,
                "japan_primary": prestige == "A",
            })
            articles.append(article)
    return _dedup(articles)


def _collect_tier3() -> list:
    articles = []
    results = _fetch_feeds_parallel(TIER3_FEEDS, is_tiered=True)
    for source, (entries, tier) in results.items():
        for entry in entries:
            if not _is_recent(entry, hours=72):
                continue
            if not _is_japan_related(entry):
                continue
            text = f"{entry.get('title', '')} {entry.get('summary', entry.get('description', ''))}".lower()
            academic_signals = ("journal", "paper", "study", "research", "analysis",
                                "findings", "abstract", "doi", "vol.", "issue",
                                source.lower())
            if not any(s in text for s in academic_signals):
                continue
            article = _entry_to_article(entry, source, extra={"journal_tier": tier})
            articles.append(article)
    return _dedup(articles)


def _collect_tier4() -> list:
    """Japanese government primary + adversary signal toward Japan."""
    articles = []
    results = _fetch_feeds_parallel(TIER4_FEEDS)
    for source, (entries, _) in results.items():
        for entry in entries:
            if not _is_recent(entry, hours=48):
                continue
            article = _entry_to_article(entry, source, lang="EN")
            articles.append(article)
    return _dedup(articles)


def _collect_pm_tracker() -> list:
    """Collect recent Japanese Prime Minister appearance/activity reports."""
    articles = []
    results = _fetch_feeds_parallel(PM_TRACKER_FEEDS)
    for source, (entries, _) in results.items():
        for entry in entries:
            if not _is_recent(entry, hours=72):
                continue
            article = _entry_to_article(entry, source, lang="EN")
            articles.append(article)
    return _dedup(articles)


# ─────────────────────────────────────────────────────────────────────────────
# GOVERNMENT-MESSAGING / ADVERSARY-SIGNAL SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

_JP_GOV_SOURCES = {"Kantei / PM", "Chief Cabinet Sec", "MOFA presser",
                   "MOD / Joint Staff", "METI statements", "BOJ statements"}
_ADVERSARY_SOURCES = {"China MOFA re Japan", "DPRK re Japan", "Russia re Japan"}


def _build_messaging_summary(tier4_articles: list) -> dict:
    """Lightweight government-messaging + adversary-signal summary for the digest prompt.

    Keeps the same payload shape pattern as the China repo's propaganda summary,
    but reframed: counts Japanese-government primary vs adversary-signal items.
    """
    all_titles = set()
    sources = {}
    gov_count = 0
    adversary_count = 0

    for art in tier4_articles:
        title = art.get("title", "").strip()
        if title:
            all_titles.add(title.lower())
        src = art.get("source", "Unknown")
        sources[src] = sources.get(src, 0) + 1
        if src in _JP_GOV_SOURCES:
            gov_count += 1
        elif src in _ADVERSARY_SOURCES:
            adversary_count += 1

    headlines = []
    for art in tier4_articles[:50]:
        title = art.get("title", "")
        if title:
            src = art.get("source", "")
            headlines.append(f"[{src}] {title}" if src else title)

    return {
        "total_articles": len(all_titles),
        "gov_count": gov_count,
        "adversary_count": adversary_count,
        "sources": sources,
        "headlines": headlines[:50],
    }


# ─────────────────────────────────────────────────────────────────────────────
# MARKET DATA
# ─────────────────────────────────────────────────────────────────────────────

def _collect_markets() -> dict:
    """Fetch Japan market strip with Yahoo primary + Stooq fallback.

    Symbols:
      - Nikkei 225
      - TOPIX (may be unreliable — falls back gracefully)
      - USD/JPY
      - EUR/JPY
      - Brent crude
      - 10Y JGB yield
      - BOJ policy rate
      - Japan 5Y CDS
      - GDP estimate (annualized)
      - Macro indicators (CPI, core CPI, Tankan, unemployment)
    """
    YAHOO_SYMBOLS = {
        "nikkei":   "^N225",
        "topix":    "^TPX",
        "usd_jpy":  "JPY=X",
        "eur_jpy":  "EURJPY=X",
        "brent":    "BZ=F",
    }
    STOOQ_SYMBOLS = {
        "nikkei":   "^nkx",
        "topix":    "^tpx",
        "usd_jpy":  "usdjpy",
        "eur_jpy":  "eurjpy",
        "brent":    "cb.f",
    }
    _SANITY_RANGES = {
        "nikkei":   (20000, 60000),
        "topix":    (1500, 4000),
        "usd_jpy":  (100, 200),
        "eur_jpy":  (110, 220),
        "brent":    (40, 200),
    }

    def _format_value(key, price):
        if key in ("nikkei", "topix"):
            return f"{price:,.2f}"
        return f"{price:.2f}"

    def _validate(key, price, mkt_time):
        lo, hi = _SANITY_RANGES.get(key, (0, float("inf")))
        if not price or price < lo or price > hi:
            return False, f"price {price} outside sanity range ({lo}-{hi})"
        if mkt_time:
            age_days = (datetime.now(timezone.utc) - mkt_time).days
            if age_days > 5:
                return False, f"data is {age_days} days old"
        return True, ""

    def _fetch_yahoo(key):
        symbol = YAHOO_SYMBOLS[key]
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }
        for host in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
            try:
                url = f"https://{host}/v8/finance/chart/{symbol}?range=5d&interval=1d"
                resp = requests.get(url, timeout=10, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                meta = data["chart"]["result"][0]["meta"]
                price = meta.get("regularMarketPrice", 0)
                prev_close = meta.get("chartPreviousClose",
                                      meta.get("previousClose", price))
                mkt_ts = meta.get("regularMarketTime", 0)
                mkt_time = (datetime.fromtimestamp(mkt_ts, tz=timezone.utc)
                            if mkt_ts else None)
                ok, reason = _validate(key, price, mkt_time)
                if not ok:
                    print(f"  ⚠ {key}: Yahoo {host} {reason}")
                    continue
                change_pct = (((price - prev_close) / prev_close * 100)
                              if prev_close else 0)
                return {
                    "value": _format_value(key, price),
                    "change_pct": round(change_pct, 2),
                    "as_of": mkt_time.strftime("%b %d") if mkt_time else "",
                }
            except (requests.RequestException, KeyError, ValueError, TypeError) as e:
                print(f"  ⚠ {key}: Yahoo {host} error: {e}")
                continue
        return None

    def _fetch_stooq(key):
        import csv as _csv
        import io as _io
        symbol = STOOQ_SYMBOLS[key]
        try:
            url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
            resp = requests.get(url, timeout=10,
                                headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            text = resp.text.strip()
            if not text or "no data" in text.lower():
                return None
            reader = _csv.DictReader(_io.StringIO(text))
            rows = [r for r in reader if r.get("Close")]
            if len(rows) < 2:
                return None
            latest = rows[-1]
            prev = rows[-2]
            price = float(latest["Close"])
            prev_close = float(prev["Close"])
            try:
                latest_dt = datetime.strptime(
                    latest["Date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except (ValueError, KeyError):
                latest_dt = None
            ok, reason = _validate(key, price, latest_dt)
            if not ok:
                print(f"  ⚠ {key}: Stooq {reason}")
                return None
            change_pct = (((price - prev_close) / prev_close * 100)
                          if prev_close else 0)
            return {
                "value": _format_value(key, price),
                "change_pct": round(change_pct, 2),
                "as_of": latest_dt.strftime("%b %d") if latest_dt else "",
            }
        except (requests.RequestException, KeyError, ValueError, TypeError) as e:
            print(f"  ⚠ {key}: Stooq error: {e}")
            return None

    def _fetch_symbol(key):
        result = _fetch_yahoo(key)
        if result:
            return key, result
        print(f"  ↻ {key}: Yahoo failed — falling back to Stooq")
        result = _fetch_stooq(key)
        if result:
            return key, result
        return key, {"value": "—", "change_pct": 0, "as_of": ""}

    result = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        symbol_futures = {pool.submit(_fetch_symbol, k): k
                          for k in YAHOO_SYMBOLS.keys()}
        jgb_f = pool.submit(_fetch_10y_jgb)
        boj_f = pool.submit(_fetch_boj_rate)
        cds_f = pool.submit(_fetch_japan_cds)
        gdp_f = pool.submit(_fetch_japan_gdp)
        macro_f = pool.submit(_fetch_japan_macro)

        for future in as_completed(symbol_futures):
            k, v = future.result()
            result[k] = v

        result["jgb_10y"]      = jgb_f.result()
        result["boj_rate"]     = boj_f.result()
        result["japan_cds"]    = cds_f.result()
        result["gdp_yoy"]      = gdp_f.result()

        macro = macro_f.result()
        if macro:
            result["japan_macro"] = macro

    return result


def _fetch_10y_jgb() -> dict:
    """Fetch Japan 10-year government bond yield."""
    try:
        url = "https://www.worldgovernmentbonds.com/country/japan/"
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        if resp.ok:
            match = re.search(
                r'10\s*[Yy]ears?.*?(\d+\.\d{2,3})\s*%',
                resp.text,
                re.DOTALL
            )
            if match:
                return {"value": f"{float(match.group(1)):.2f}%",
                        "as_of": datetime.now(timezone.utc).strftime("%b %d")}
    except Exception as e:
        print(f"  ⚠ 10Y JGB fetch error: {e}")
    print("  ⚠ 10Y JGB: using fallback (1.50%)")
    return {"value": "1.50%", "as_of": ""}


def _fetch_boj_rate() -> dict:
    """Fetch the BOJ policy rate (short-term policy interest rate)."""
    try:
        url = _gnews("%22Bank+of+Japan%22+%22policy+rate%22+OR+%22interest+rate%22+%22held%22+OR+%22raised%22+OR+%22cut%22")
        entries = _parse_feed(url)
        for entry in entries[:5]:
            text = f"{entry.get('title', '')} {entry.get('summary', '')}"
            m = re.search(r"(\d\.\d{1,2})\s*(?:%|percent)", text)
            if m:
                return {"value": f"{m.group(1)}%",
                        "last_change": "",
                        "as_of": datetime.now(timezone.utc).strftime("%b %d")}
    except Exception as e:
        print(f"  ⚠ BOJ rate fetch error: {e}")
    print("  ⚠ BOJ policy rate: using fallback (0.50%)")
    return {"value": "0.50%", "last_change": "", "as_of": ""}


def _fetch_japan_cds() -> dict:
    """Fetch Japan 5-year sovereign CDS spread (bps)."""
    try:
        url = "https://www.worldgovernmentbonds.com/cds-historical-data/japan/5-years/"
        resp = requests.get(url, timeout=12, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        if resp.ok:
            matches = re.findall(
                r'<td[^>]*>\s*(\d{1,2}\s+\w+\s+\d{4})\s*</td>\s*<td[^>]*>\s*([\d.]+)\s*</td>',
                resp.text
            )
            if len(matches) >= 2:
                latest_date, latest_val = matches[0]
                _, prev_val = matches[1]
                spread = float(latest_val)
                prev_spread = float(prev_val)
                change = spread - prev_spread
                as_of = ""
                try:
                    as_of = datetime.strptime(latest_date.strip(), "%d %B %Y").strftime("%b %d")
                except ValueError:
                    pass
                return {"value": f"{spread:.0f}", "change_bps": round(change, 1), "as_of": as_of}
    except Exception as e:
        print(f"  ⚠ Japan CDS fetch error: {e}")
    print("  ⚠ Japan 5Y CDS: using fallback (20 bps)")
    return {"value": "20", "change_bps": 0, "as_of": ""}


def _fetch_japan_gdp() -> dict:
    """Fetch latest Japan GDP growth (quarterly, annualized)."""
    try:
        url = _gnews("Japan+GDP+%22annualized%22+OR+%22annual+rate%22+quarter")
        entries = _parse_feed(url)
        for entry in entries[:5]:
            text = f"{entry.get('title', '')} {entry.get('summary', '')}"
            m = re.search(r"(-?\d\.\d)\s*(?:%|percent).*?(?:annual|annualized)", text, re.IGNORECASE)
            if m:
                return {"value": f"{m.group(1)}%", "period": "latest Q (annualized)",
                        "source": "Cabinet Office"}
    except Exception:
        pass
    print("  ⚠ Japan GDP: using fallback (0.9% annualized, estimate)")
    return {"value": "0.9%", "period": "latest Q (annualized, est.)", "source": "estimate"}


def _fetch_japan_macro() -> dict | None:
    """Fetch additional Japan macro indicators (CPI, core CPI, Tankan, unemployment)."""
    indicators = {}
    queries = {
        "cpi_yoy":      "Japan+CPI+%22year-on-year%22+%22consumer+prices%22",
        "core_cpi_yoy": "Japan+%22core+CPI%22+%22year-on-year%22",
        "unemployment": "Japan+%22unemployment+rate%22+%22percent%22",
        "tankan":       "Japan+%22Tankan%22+%22business+sentiment%22+OR+%22large+manufacturers%22",
    }
    for key, q in queries.items():
        try:
            entries = _parse_feed(_gnews(q))
            for entry in entries[:3]:
                text = f"{entry.get('title', '')} {entry.get('summary', '')}"
                if key in ("cpi_yoy", "core_cpi_yoy", "unemployment"):
                    m = re.search(r"(-?\d\.\d)\s*(?:%|percent)", text)
                    if m:
                        v = float(m.group(1))
                        sign = "+" if v >= 0 and key != "unemployment" else ""
                        indicators[key] = f"{sign}{v:.1f}%"
                        break
                elif key == "tankan":
                    m = re.search(r"[+-]?\b\d{1,2}\b", text)
                    if m and ("Tankan" in text or "tankan" in text):
                        indicators[key] = m.group(0)
                        break
        except Exception:
            continue
    return indicators if indicators else None


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def collect_all() -> dict:
    """Run the full collection. Returns the payload dict for digest.py."""
    print("\n📡 Japan Daily Brief — Collector")
    print("=" * 60)

    t0 = time.time()

    print("\n🔍 Tier 1: News (24h window)...")
    tier1 = _collect_tier1()
    print(f"  ✔ {len(tier1)} articles from {len({a['source'] for a in tier1})} sources")

    print("\n🔍 Tier 2: Analysis (36h window)...")
    tier2 = _collect_tier2()
    print(f"  ✔ {len(tier2)} articles from {len({a['source'] for a in tier2})} sources")

    print("\n🔍 Tier 3: Academic (72h window)...")
    tier3 = _collect_tier3()
    print(f"  ✔ {len(tier3)} articles from {len({a['source'] for a in tier3})} sources")

    print("\n🔍 Tier 4: Japan Government Primary + Adversary Signal (48h window)...")
    tier4 = _collect_tier4()
    print(f"  ✔ {len(tier4)} articles from {len({a['source'] for a in tier4})} sources")

    print("\n🔍 PM appearance tracker (72h window)...")
    pm_articles = _collect_pm_tracker()
    print(f"  ✔ {len(pm_articles)} PM-related articles")

    print("\n💹 Market data...")
    markets = _collect_markets()
    print(f"  ✔ {sum(1 for v in markets.values() if v)} indicators")

    print("\n📊 Government-messaging summary...")
    msg_summary = _build_messaging_summary(tier4)
    print(f"  ✔ {msg_summary['total_articles']} unique items "
          f"({msg_summary['gov_count']} JP-gov, {msg_summary['adversary_count']} adversary)")

    elapsed = time.time() - t0
    print(f"\n⏱ Collection completed in {elapsed:.1f}s")

    payload = {
        "tier1": tier1,
        "tier2": tier2,
        "tier3": tier3,
        "tier4": tier4,
        "pm_tracker_articles": pm_articles,
        "market_indicators": markets,
        "messaging_summary": msg_summary,
        "source_health": _source_health,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }
    return payload


if __name__ == "__main__":
    out = collect_all()
    with open("collected.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    total = sum(len(v) for k, v in out.items() if isinstance(v, list))
    print(f"\n💾 Wrote collected.json ({total} articles total)")
