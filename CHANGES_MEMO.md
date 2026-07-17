# Memo — Japan Chair Review: Proposed Changes to the Daily Japan Digest

**To:** CSIS Japan Chair
**From:** Andy Lim
**Re:** Implementation plan for reviewer comments on the Daily Japan Digest setup
**Reviewers:** Kristi Govella · Yuko Nakano · Nicholas Szechenyi
**Comments received:** 14

---

## Summary

Thank you for the review. All 14 comments have been collected and mapped to specific changes in the pipeline. **Thirteen of the fourteen are now implemented and pushed** — the ten drop-in source/factual changes (Batch 1) and the three coverage/accuracy changes (Batch 2: rare-earths, the $550B framework, and the trade/alliance figures rewrite). The **one** remaining item is how to display cabinet-approval polling, which involves a genuine design choice where two reviewers pointed in slightly different directions — that is the only item still needing a decision before we build it.

Sequencing and status:

| Batch | What | Comments | Status |
|---|---|---|---|
| **1 — Drop-ins** | New feeds, journals, regional press, analysts; remove USIP; add Onoda; fix BOJ rate | #1, 2, 3, 8, 9, 11, 13, 14 | **Done** |
| **2 — Coverage & accuracy** | Rare-earths + $550B targeting; US-Japan trade/alliance rewrite | #4, 7, 12 | **Done** |
| **3 — Polling display** | Multiple polls / aggregator | #5, 6, 10 | **Needs a decision (see §I)** |

---

## A. New think-tank feeds (Tier 2) — **Done**
*Govella #1 · Szechenyi #14 · Govella #8 — drop-in, low risk*

**Add (Govella):** Pacific Forum, Congressional Research Service, Asia Policy Point, Japan Economy Watch (Richard Katz), VUB/CSDS Japan Chair.

**Add (Szechenyi — survey/opinion-data institutions):** ASAN Institute, ISEAS–Yusof Ishak Institute, Genron NPO, Chicago Council on Global Affairs, Pew Research Center.

**Remove (Govella):** USIP.

Each is a one-line change to the feed list, mirrored in the public source inventory. *Caveat:* a few of these (CRS, the Katz Substack, Genron NPO, CSDS) are not always well-indexed by the news aggregator we query; where hit-rates are low in the first runs we will switch to the outlet's direct feed. No decision required.

---

## B. New academic journals (Tier 3) — **Done**
*Govella #2 — drop-in*

Add: Asia Policy (A), Asia-Pacific Journal: Japan Focus (B), Asian Security (B), International Relations of the Asia-Pacific (A), The Pacific Review (A), Contemporary Japan (B), Japan Review (B). One line each. No decision required.

---

## C. Regional press — **Done**
*Szechenyi #13 — drop-in*

Broaden allied/regional reaction with **The Australian** (Australia), **Indian Express** (India), and **Rappler** (Philippines), alongside the existing Korea/China/Russia reaction feeds. No decision required.

---

## D. Analyst bylines — **Done**
*Nakano #9 — drop-in*

Add **Demetri Sevastopulo (FT)** and **David Ignatius (WaPo)** to the flagged-byline list. As Nakano notes, these are columnists rather than Tokyo correspondents, so they are flagged for weight but not treated as on-the-ground reporting. No decision required.

---

## E. BOJ policy rate correction — **Done**
*Govella #3 — factual fix, must-do*

Dr. Govella is correct that the sample showed **0.50%** while the live BOJ short-term policy rate is now higher. **Implemented:** the fallback figure is corrected to **1.00%**, and the live rate scrape still overrides it whenever the day's sources report a rate — so we are never showing a stale hardcoded number. If the current rate differs from 1.00%, it's a one-line change to the fallback.

---

## F. Cabinet reference — **Done**
*Nakano #11 — drop-in*

Nakano confirms the cabinet names are current. Two adjustments: **Yoshimasa Hayashi** (Internal Affairs & Communications) is already in the reference; add **Kimi Onoda**, Minister for Economic Security — noting she also carries the "foreign nationals" portfolio. No decision required.

---

## G. Targeted coverage: rare earths and the $550B framework — **Done**
*Govella #4, #7 — prompt steering*

Neither needed a new source; both are instructions that make sure existing coverage surfaces. **Implemented:**

- **Rare earths / critical minerals** — now an explicit watch item in the Regional Pressure Watch's China signal (rare earths, gallium, germanium, graphite, magnets, export-license/supply restrictions bearing on Japan), where China's mineral leverage properly belongs.
- **The $550 billion US-Japan strategic investment framework** — now flagged as a priority pickup for both the Business & Economy section and the trade block, and carried as a standing line in the tariff/trade dashboard.

*Honest limit:* our source-or-skip rule means we can guarantee we never *miss* one of these stories when the day's feeds carry it — we cannot manufacture one on a quiet day. That is the correct, non-fabricating behavior.

---

## H. US-Japan Alliance & Trade — figures rewrite — **Done**
*Nakano #12 — substantive, high value*

Nakano's detailed corrections have been **encoded verbatim** as the new trade/alliance baselines, and the email's tariff/alliance dashboard now renders them:

**Tariffs**
- Autos: **15%, inclusive of MFN**, under the 2025 US-Japan agreement (replaces the old 25% Section 232 auto rate for Japan).
- Section 122: **10% surcharge through July 24, 2026**, **not stacked** on Section 232, **autos excluded** — on the June 2026 proclamation basis.
- Steel & aluminum: **50%** remains the core Section 232 rate.
- **New "Section 301 Watch"** line (renders when relevant): proposed 12.5% forced-labor tariff; excess-capacity investigation pending — marked as *proposed/pending*.
- The outdated "negotiated framework reported; auto relief unconfirmed — verify" line is **removed**; the dashboard now shows "2025 agreement in force" plus a **$550B investment framework** line.

**Alliance dashboard**
- Defense spending: **2% of GDP brought forward to JFY2025** (ended March 31, 2026), with the **2026 Three Strategic Documents review** noted — replacing "by FY2027."
- Article 5 / Senkakus: affirmed — **kept** under the dashboard.
- Host-nation support: SMA **through March 31, 2027, ~¥211bn/year**.
- USFJ: Henoko/Futenma realignment **ongoing**.

These were reference-text + renderer changes, no new scraping. *Standing caution:* several are dated specifics (a surcharge "through July 2026," an SMA to March 2027) and will eventually go stale like the old figures — the guardrail is intact: live news overrides the baseline, and anything uncertain is marked "verify."

---

## I. Public Sentiment / polling — the one open decision
*Govella #5, #6 · Nakano #10*

This is the only item with a genuine trade-off, because the two reviewers emphasize different things:

- **Govella (#5):** Can it display **multiple polls**? "There are often differences."
- **Govella (#6):** Observing Japan runs a **poll aggregator** worth linking.
- **Nakano (#10):** Pull figures from dedicated poll sites (NHK, Nikkei) — but **"do not want to overcomplicate."**

Today the digest shows a single poll under a strict same-pollster/same-date rule. Honoring "show multiple polls" means changing the data model to hold two or three polls and rendering them side by side (e.g. *NHK 46% · Jiji 41% · Yomiuri 44%*). The options:

| Option | What it does | Effort | Trade-off |
|---|---|---|---|
| **1 — Multi-poll row** | 2–3 pollsters side by side; collapses to one on light days | Moderate | Fully honors "show differences" |
| **2 — One poll + aggregator link** | Keep single headline poll; add standing Observing Japan tracker link | Low | Simplest; doesn't literally show multiple numbers |
| **3 — Both** | Multi-poll row *and* aggregator link | Higher | Most complete |

On Nakano's dedicated-site suggestion: the NHK and Nikkei approval pages are data/JavaScript pages, not standard feeds, so scraping them reliably is real work and can fail silently. **Recommendation:** do *not* hard-scrape those; rely on the pollster stories we already collect (NHK/Jiji/Yomiuri/Asahi/Kyodo all publish poll coverage we catch), and add the Observing Japan aggregator as a **link**. That honors "don't overcomplicate."

**Our recommendation: Option 1 plus the aggregator link** — show multiple polls when the day's feeds carry them, plus a persistent Observing Japan tracker link, and no fragile dedicated-site scraping.

---

## What we need from you

**One decision remains:**

1. **Polling display (§I):** confirm **Option 1 + aggregator link** (our recommendation), or pick another. This is the only thing gating Batch 3.

*Resolved and shipped:* the BOJ fallback (§E, now 1.00%) and the trade/alliance figures (§H, encoded as-is per your green-light). If any Batch-2 figure should be re-verified against a specific source, point us to it and it's a one-line change.

*Prepared by Andy Lim · CSIS Japan Chair*
