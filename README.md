# Japan Daily Brief

Automated daily intelligence briefing on Japan and the US-Japan alliance for the CSIS Japan Chair. Sibling pipeline to [Daily-Korea-Digest](https://github.com/andysaulim/Daily-Korea-Digest) and [Daily-China-Digest](https://github.com/andysaulim/Daily-China-Digest). Collects from 60+ sources, generates an analyst-grade digest via Claude, and delivers a styled HTML email at **6:00 AM ET**.

**Live archive:** `andysaulim.github.io/Daily-Japan-Digest` (planned)

---

## Latest Run

| Metric | Value |
| --- | --- |
| Last generated | Jul 9, 2026 at 8:30 AM ET |
| Digest date | Thursday, July 9, 2026 |
| Articles collected | 52 |
| Unique sources | 9 |
| Top stories | 4 |
| Overnight items | 4 |
| Word count | ~1,371 |
| PM appeared | Yes |

## How It Works

```
collect.py          digest.py           render.py          send_email.py
60+ RSS feeds   -->  Claude Sonnet  -->  HTML email  -->  Gmail SMTP
  + market data       (Opus retry)       + archive        + GitHub Pages
  + PM tracker         + Japan refs       (public/)
  + region watch        (Senkaku, alliance, DPRK)
```

1. **Collect** — Scrapes 60+ RSS feeds in parallel across 4 tiers, plus market data (Nikkei 225, USD/JPY, EUR/JPY, Brent, 10Y JGB, BOJ policy rate, Japan 5Y CDS)
2. **Enrich** — Injects verified Japan reference timelines: Senkaku/East China Sea incidents, US-Japan alliance milestones, DPRK missiles over/near Japan
3. **Digest** — Claude Sonnet (`claude-sonnet-4-6`) generates the initial briefing; Opus (`claude-opus-4-8`) escalates on retry if content minimums aren't met (target 1,200–1,400 words)
4. **Validate** — Pre-send quality gate: word count, source diversity, duplicates, prestige outlet inclusion, data integrity
5. **Render** — JSON to table-based HTML email, inline CSS, optimized for Gmail / Outlook / Apple Mail
6. **Send** — Gmail SMTP with 3x retry, 5s backoff
7. **Archive** — Pushes to GitHub Pages

---

## Source Coverage

**Full feed-by-feed inventory (every source + exact query) is in [`SOURCES.md`](SOURCES.md).**

| Tier | Sources | Window | Content |
| --- | --- | --- | --- |
| **1 — News** | 40+ feeds | 24h | Wire services, correspondents, Japanese English-language press, US & Japan government, regional reaction |
| **2 — Analysis** | 21 feeds | 36h | Think tanks (CSIS Japan Chair, Brookings, CFR, RAND, Carnegie, Stimson, Sasakawa, NBR, IISS) — A/B prestige |
| **3 — Academic** | 11 feeds | 72h | Journals (Int'l Security, Asian Survey, Journal of Japanese Studies, Social Science Japan Journal) — A+/A/B tiers |
| **4 — Gov Primary + Adversary** | 9 feeds | 48h | Kantei, Chief Cabinet Sec, MOFA, MOD/Joint Staff, METI, BOJ + China/DPRK/Russia signals toward Japan |

*A separate PM-appearance tracker (5 feeds, 72h) flags the Prime Minister's public schedule.*

**Prestige outlet rule:** Japan stories from WSJ, NYT, WaPo, Bloomberg, FT, The Economist, CNN, Reuters, CNBC, NHK, Kyodo, Japan Times, Nikkei Asia are always included.

---

## Newsletter Sections (in delivery order)

| # | Section | Description |
| - | - | - |
| 1 | Header | Date · RE line · editor's note |
| 2 | Market Strip | Nikkei 225 · USD/JPY · EUR/JPY · Brent · 10Y JGB · Japan 5Y CDS · BOJ policy rate · GDP |
| 3 | Δ Since Yesterday | What moved: BOJ, tariffs, scrambles, CCG presence, DPRK launches |
| 4 | Morning Memo | Top 3 stories at a glance — elevator brief |
| 5 | Top Stories | 2–4 biggest hard news stories with "So what" + pattern_note |
| 6 | Overnight Flash | Up to 6 secondary items |
| 7 | Key Stat | Single striking number from today's news |
| 8 | Regional Pressure Watch | **DARK SECTION** — China / DPRK / Russia adversary signals toward Japan + PM watch |
| 9 | Expert Analysts | Op-eds + academic journals |
| 10 | Public Sentiment | Cabinet approval & party support (NHK/Jiji/Yomiuri/Asahi/Kyodo, same-poll rule) |
| 11 | Social Statements | Quotes from the PM, ministers, BOJ Governor, US/allied officials |
| 12 | Japanese Government | Kantei, Cabinet Sec, MOFA, MOD/Joint Staff, METI, MOF, BOJ + Personnel + Diet Sessions/LDP + Calendar |
| 13 | US–Japan Alliance & Trade | Section 232 autos/steel, Section 122, trade-deal status, alliance dashboard (Article 5, defense spending, HNS, USFJ) |
| 14 | Diet Watch | House of Representatives / House of Councillors, key bills, budget |
| 15 | Business & Economy | Major corporates, semiconductors (Rapidus, JASM), macro indicators |
| 16 | Indo-Pacific | China-Japan, Korea-Japan, DPRK, US-Japan-ROK trilateral, Quad, Taiwan |
| 17 | Also Today / The Wire | Up to 6 third-tier items |
| 18 | On This Day | Verified historical event matching today's exact date |
| 19 | Footer | — |

---

## Setup

**Full setup & operations guide: [`SETUP.md`](SETUP.md)** (secrets, GitHub Actions, local runs, troubleshooting, go-live checklist).

### Prerequisites
- Python 3.12+
- Anthropic API key (Claude Sonnet)
- Gmail account with app password
- GitHub PAT (for Pages deployment)

### Install
```bash
git clone https://github.com/andysaulim/Daily-Japan-Digest.git
cd Daily-Japan-Digest
pip install -r requirements.txt
```

### Environment Variables
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GMAIL_USER="you@gmail.com"
export GMAIL_APP_PASS="xxxx xxxx xxxx xxxx"
export DIGEST_TO="recipient1@example.com,recipient2@example.com"
export GITHUB_TOKEN="ghp_..."
export WEB_URL="https://andysaulim.github.io/Daily-Japan-Digest"
```

### Run
```bash
python run.py                # Full pipeline: collect -> digest -> render -> send
python run.py --dry-run      # Collection only (outputs collected.json)
python run.py --from-cache   # Skip collection, reuse collected.json
python run.py --no-send      # Generate HTML but don't email
python run.py --no-archive   # Skip writing to public/ archive
python run.py --force-send   # Send even if validation gates fail
```

---

## Schedule

GitHub Actions workflow (`.github/workflows/daily-digest.yml`) runs daily at **10:00 UTC (6:00 AM ET)** with manual `workflow_dispatch`. Cron handles both EST and EDT.

Required secrets: `ANTHROPIC_API_KEY`, `GMAIL_USER`, `GMAIL_APP_PASS`, `DIGEST_TO`, `GH_PAT`. Optional variable: `WEB_URL`.

---

## Validation Gates

- **Word count**: Hard minimum 1,000 (target 1,200–1,400)
- **Section minimums**: 2–4 top stories, ≥3 overnight, exactly 3 morning memo
- **Source diversity**: No single source >3 times in top + overnight
- **Prestige outlets**: WSJ/NYT/WaPo/Bloomberg/FT/Economist/CNN/Reuters/NHK/Kyodo/Japan Times/Nikkei never dropped
- **Same-poll-date rule**: Approval polling never mixes pollsters or survey dates
- **Content filters**: J-pop/idol/anime/celebrity hard-blocked unless policy/security angle
- **Data integrity**: No placeholder URLs, no "None" strings, date matches today

---

## Project Structure

```
├── run.py                   # Entry + validation
├── collect.py               # 60+ RSS feeds, market data, PM tracker, security watch
├── digest.py                # Claude system prompt and generation
├── render.py                # HTML email renderer
├── send_email.py            # Gmail SMTP
├── databases.py             # Verified Japan reference timelines
├── pm_tracker.py            # Japanese PM appearance persistence
├── pm_tracker.json          # Appearance history
├── region_tracker.py        # Adversary-signal baseline (China/DPRK/Russia)
├── region_tracker.json      # Signal history
├── tension_scorer.py        # Senkaku/ECS · DPRK · Russia tension
├── update_readme.py         # README auto-updater
├── requirements.txt
├── .github/workflows/
│   └── daily-digest.yml     # 10:00 UTC cron
└── public/                  # GitHub Pages archive (generated)
```

---

*CSIS Japan Chair*

*Prepared by Andy Lim*
