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
| `collect.py` | Parallel RSS scraper, market data (Nikkei, USD/JPY, EUR/JPY, Brent, JGB, BOJ rate, CDS), PM-appearance feeds |
| `digest.py` | Claude API integration — system prompt, structured JSON output, Sonnet-first (`claude-sonnet-4-6`) with Opus retry (`claude-opus-4-8`) |
| `render.py` | HTML email renderer — table-based layout, inline CSS, dark mode, mobile responsive |
| `send_email.py` | Gmail SMTP sender (SSL, port 465) |
| `databases.py` | Verified Japan reference timelines (Senkaku/ECS incidents, US-Japan alliance milestones, DPRK missiles over/near Japan) |
| `pm_tracker.py` | Japanese Prime Minister appearance log — "days since last seen" (7-day anomaly threshold) |
| `region_tracker.py` | Adversary-signal baseline — rolling China / DPRK / Russia signal history toward Japan |
| `tension_scorer.py` | Japan regional tension index — Senkaku/ECS + DPRK + Russia axes |
| `update_readme.py` | Auto-updates README with latest run stats |

## Persistent State

Tracker files (`pm_tracker.json`, `region_tracker.json`) are cached across GitHub Actions runs. They prevent the AI from hallucinating baselines — real historical data is injected into the prompt instead.

## Feed Tiers

- **Tier 1 (News, 24h)**: WSJ/NYT/WaPo/FT/Reuters/AP/AFP/Bloomberg/BBC/CNN/Economist + Japanese press in English (NHK World, Kyodo, Japan Times, Mainichi, Asahi, Yomiuri/Japan News, Nikkei Asia, Jiji, Japan Forward) + US govt (White House, State, Pentagon, USTR, INDOPACOM, USFJ) + Japan govt (Kantei, MOFA, MOD, METI, MOF, BOJ) + regional reaction (Yonhap, Global Times, Xinhua, TASS) + specialists (The Diplomat, Tokyo Review, Observing Japan)
- **Tier 2 (Analysis, 36h)**: CSIS Japan Chair, Brookings (Solís), CFR (Sheila Smith), RAND (Hornung), Carnegie, Stimson, Hudson, Sasakawa USA/SPF, NBR, East-West Center, Lowy, IISS, Atlantic Council, USIP, GMF, Asia Society
- **Tier 3 (Academic, 72h)**: International Security, International Organization, Asian Survey, Pacific Affairs, Journal of Japanese Studies, Social Science Japan Journal, Journal of East Asian Studies, Security Studies, Washington Quarterly, Survival, Journal of Strategic Studies — all filtered with "Japan"
- **Tier 4 (Japanese Government Primary + Adversary Signal, 48h)**: Kantei/PM, Chief Cabinet Secretary, MOFA presser, MOD/Joint Staff, METI, BOJ; plus China MOFA on Japan/Senkaku, DPRK (KCNA / launches affecting Japan), Russia (Northern Territories)

## Critical Rules

- **SOURCE-OR-SKIP**: Every claim in the digest must trace to a collected article or a prompt baseline. No memory-based assertions.
- **PM identity**: The sitting Prime Minister may have changed since the model's training cutoff. ALWAYS use the name from today's articles. Current seed: Sanae Takaichi (LDP, first female PM; succeeded Ishiba) — verify.
- **Same-poll-date rule**: All `public_sentiment` polling numbers must come from the same pollster (NHK/Jiji/Yomiuri/Asahi/Kyodo) and the same survey date range — never mix.
- **Prestige enforcement**: Japan stories from WSJ, NYT, WaPo, Bloomberg, FT, Economist, CNN, Reuters, CNBC, NHK, Kyodo, Japan Times, Nikkei Asia must appear if they published.
- **Section-key coupling**: `digest.py`, `render.py`, and `run.py` share top-level dict keys. Several China-era keys are retained but relabeled in the UI: `xinhua_delta` = Regional Pressure Watch, `prc_government` = Japanese Government, `npc_politburo` = Diet Sessions / LDP (inside Japanese Government, and now carrying all Diet and party business). `us_china_trade` (US-Japan Alliance & Trade), `congressional_watch` (Diet Watch), `morning_memo` (Today at a Glance), `overnight_items` (Overnight) and `also_today` (The Wire) no longer exist.
- **Adding or removing a section key**: many places enumerate sections, and a key missing from one of them usually fails silently rather than loudly. This list said "nine" while naming fourteen, and omitted the two that fail *loudly* — which is the pair that matters most, because they stop the pipeline rather than degrade it. The real inventory:
  - **Hard gates — a stale entry here fails EVERY run, not just one section.** `digest.py` `_check_content_minimums` and `run.py` `_validate_digest` both assert per-section counts. A minimum naming a section that no longer exists means the model retries to Opus, fails again, and `run.py` refuses to send. Check these first.
  - **The model's contract**, `digest.py`: the per-section spec under DIGEST SYNTHESIS, the anti-fabrication list, the Tier 1 triage list, PLACEMENT PRIORITY, the prestige-outlet and CSIS-products fallback rules, the `indo_pacific` exclusion redirect, `_CONTENT_SECTIONS`, and the TARGET LENGTH band (which is calibrated on the sections that exist).
  - **Pipeline**, `run.py`: `_count_words`, `_URL_SECTIONS`, `_DEDUPE_ORDER`, the unrolled `_sweep`/`_already_swept` pair around the `key_stat` seeding, `_enforce_source_diversity`, `_TIER_SOURCED`, and the archive-entry stat dict.
  - **Render**, `render.py`: the section's own render block, `SECTION_ORDER`, `_NAV`, `_word_count`.
  - **Elsewhere**: `length_budget.py` `TRIM_ORDER`; `update_readme.py` `_ARTICLE_SECTIONS` / `_TEXT_SECTIONS` and the Latest Run table rows; the `smoke_test.py` and `preview.py` fixtures, which are meant to carry every content key.

  Omitting `_URL_SECTIONS` skips URL repair and the untraceable-source drop; omitting `_word_count` hides the section from both the masthead word count and the length ceiling. `shared/length_budget.py` is the Korea copy and is NOT imported by this pipeline — it will match a search but must not be edited.
- **Section order** lives in one place: `SECTION_ORDER` in `render.py`. Each section writes itself into `body_sections` under its own id; a key absent from `SECTION_ORDER` raises rather than vanishing.

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
