# Japan Daily Brief

Automated intelligence briefing on Japan and the US-Japan alliance, delivered daily at 6 AM ET to senior policymakers and analysts.

## Architecture

```
COLLECT (60+ RSS feeds, 25 threads) → DIGEST (Claude Sonnet/Opus) → VALIDATE (dedup, URL repair, source caps) → RENDER (HTML email) → SEND (Gmail SMTP)
```

Orchestrated by `run.py`. Triggered via GitHub Actions `workflow_dispatch` + a 10:00 UTC daily cron.

## Key Files

| File | Role |
|------|------|
| `run.py` | Pipeline orchestrator — runs collect → digest → validate → render → send |
| `collect.py` | Parallel RSS scraper, market data (Nikkei, TOPIX, USD/JPY, EUR/JPY, Brent, JGB, BOJ rate, CDS), PM-appearance feeds, security-watch feeds |
| `digest.py` | Claude API integration — system prompt, structured JSON output, Sonnet-first (`claude-sonnet-4-6`) with Opus retry (`claude-opus-4-8`) |
| `render.py` | HTML email renderer — table-based layout, inline CSS, dark mode, mobile responsive |
| `send_email.py` | Gmail SMTP sender (SSL, port 465) |
| `databases.py` | Verified Japan reference timelines (Senkaku/ECS incidents, US-Japan alliance milestones, DPRK missiles over/near Japan) |
| `pm_tracker.py` | Japanese Prime Minister appearance log — "days since last seen" (7-day anomaly threshold) |
| `region_tracker.py` | Adversary-signal baseline — rolling China / DPRK / Russia signal history toward Japan |
| `bp_tracker.py` | 9 Japan security-watch location statuses (Senkaku, Sea of Japan, Okinawa/USFJ, Northern Territories, DPRK launch sites, etc.) |
| `tension_scorer.py` | Japan regional tension index — Senkaku/ECS + DPRK + Russia axes |
| `update_readme.py` | Auto-updates README with latest run stats |

## Persistent State

Tracker files (`pm_tracker.json`, `region_tracker.json`, `bp_tracker.json`) are cached across GitHub Actions runs. They prevent the AI from hallucinating baselines — real historical data is injected into the prompt instead.

## Feed Tiers

- **Tier 1 (News, 24h)**: WSJ/NYT/WaPo/FT/Reuters/AP/AFP/Bloomberg/BBC/CNN/Economist + Japanese press in English (NHK World, Kyodo, Japan Times, Mainichi, Asahi, Yomiuri/Japan News, Nikkei Asia, Jiji, Japan Forward) + US govt (White House, State, Pentagon, USTR, INDOPACOM, USFJ) + Japan govt (Kantei, MOFA, MOD, METI, MOF, BOJ) + regional reaction (Yonhap, Global Times, Xinhua, TASS) + specialists (The Diplomat, Tokyo Review, Observing Japan)
- **Tier 2 (Analysis, 36h)**: CSIS Japan Chair, Brookings (Solís), CFR (Sheila Smith), RAND (Hornung), Carnegie, Stimson, Hudson, Sasakawa USA/SPF, NBR, East-West Center, Lowy, IISS, Atlantic Council, USIP, GMF, Asia Society
- **Tier 3 (Academic, 72h)**: International Security, International Organization, Asian Survey, Pacific Affairs, Journal of Japanese Studies, Social Science Japan Journal, Journal of East Asian Studies, Security Studies, Washington Quarterly, Survival, Journal of Strategic Studies — all filtered with "Japan"
- **Tier 4 (Japanese Government Primary + Adversary Signal, 48h)**: Kantei/PM, Chief Cabinet Secretary, MOFA presser, MOD/Joint Staff, METI, BOJ; plus China MOFA on Japan/Senkaku, DPRK (KCNA / launches affecting Japan), Russia (Northern Territories)

## Critical Rules

- **SOURCE-OR-SKIP**: Every claim in the digest must trace to a collected article or a prompt baseline. No memory-based assertions.
- **PM identity**: The sitting Prime Minister may have changed since the model's training cutoff. ALWAYS use the name from today's articles. Last-known seed: Shigeru Ishiba (LDP, since Oct 2024) — verify.
- **Same-poll-date rule**: All `public_sentiment` polling numbers must come from the same pollster (NHK/Jiji/Yomiuri/Asahi/Kyodo) and the same survey date range — never mix.
- **Prestige enforcement**: Japan stories from WSJ, NYT, WaPo, Bloomberg, FT, Economist, CNN, Reuters, CNBC, NHK, Kyodo, Japan Times, Nikkei Asia must appear if they published.
- **Section-key coupling**: `digest.py`, `render.py`, and `run.py` share top-level dict keys. Several China-era keys are retained but relabeled in the UI: `xinhua_delta` = Regional Pressure Watch, `prc_government` = Japanese Government, `us_china_trade` = US-Japan Alliance & Trade, `congressional_watch` = Diet Watch, `npc_politburo` = Diet Sessions / LDP. Rename in all three files if you change one.

## Stack

Python 3.12, Anthropic API (Claude Sonnet primary / Opus retry), Gmail SMTP, GitHub Actions + GitHub Pages.

## Running Locally

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
export GMAIL_USER=...
export GMAIL_APP_PASS=...
export DIGEST_TO=...
python run.py                # full pipeline
python run.py --dry-run      # collection only
python run.py --from-cache   # reuse collected.json
python run.py --no-send      # render but don't email
```
