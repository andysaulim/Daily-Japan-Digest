# Daily Japan Digest — Editorial Approval Package

**For:** CSIS Japan Chair (final approval)
**Prepared by:** Andy Lim
**Status:** Built, not yet live. **Nothing sends until the Japan Chair signs off.**
**Cadence:** Daily, 6:00 AM ET · HTML email + public web archive

This document is for editorial review. It lays out every **source**, the **newsletter structure**, the **topics covered**, the **polling inputs**, and the **editorial rules**. Mark up anything you want added, dropped, or reweighted. A short list of **items needing your decision** is at the bottom.

---

## 1. What it is

An automated morning intelligence brief on Japan and the US–Japan alliance, built on the same pipeline as the Korea and China daily briefs. Each morning it collects from the sources below, has Claude synthesize a structured, sourced digest (no editorializing, every claim traceable to a collected article), runs it through quality gates, and delivers a styled HTML email — with a permanent web archive.

It is a **Japan-as-subject, ally-framed** product: Japan's own government, politics, economy, alliance management, and public opinion — plus an adversary **Regional Pressure Watch** (China / North Korea / Russia).

---

## 2. Sources (for review)

> **Complete, exact feed inventory — including every search query — is in [`SOURCES.md`](SOURCES.md).** The summary below is by category; `SOURCES.md` lists all ~90 feeds, the market endpoints, and the reference databases the Claude API draws from.

Sources are organized in four tiers by type and recency window. News is pulled via wire/outlet RSS and Google News site-scoped queries.

### Tier 1 — News (24-hour window, ~44 sources)
**International press, Japan bureaus:** WSJ, NYT, Washington Post, FT, Reuters, AP, AFP, Bloomberg, BBC, CNN, CNBC, The Economist, The Guardian
**Japanese press (English editions):** NHK World, Kyodo News, Japan Times, Mainichi, Asahi (AJW), The Japan News (Yomiuri), Nikkei Asia, Jiji Press, Japan Forward
**US government:** White House, State Dept, Pentagon, Treasury, USTR, Commerce, INDOPACOM, US Forces Japan
**Japanese government:** Kantei / PMO, MOFA, MOD, METI, MOF, Bank of Japan
**Regional reaction:** Yonhap & Korea Herald (on Japan), Global Times & Xinhua (on Japan), TASS (on Japan)
**Specialist:** The Diplomat (Japan), Tokyo Review, Observing Japan

### Tier 2 — Analysis / think tanks (36-hour window, ~21 sources)
CSIS Japan Chair, Brookings (Mireya Solís), CFR (Sheila Smith), RAND (Jeffrey Hornung), Carnegie, Stimson, Hudson, Sasakawa USA, Sasakawa Peace Foundation, NBR, East-West Center, Lowy Institute, IISS, Atlantic Council, USIP, German Marshall Fund, Asia Society Policy Institute, university Japan programs (MIT/Harvard/Georgetown), Foreign Affairs, Foreign Policy, War on the Rocks.
*CSIS in-house products are flagged for mandatory inclusion when they publish.*

### Tier 3 — Academic journals (72-hour window, ~11 sources)
International Security, International Organization, Security Studies, The Washington Quarterly, Survival (IISS), Journal of Strategic Studies, Journal of East Asian Studies, Asian Survey, Pacific Affairs, Journal of Japanese Studies, Social Science Japan Journal.

### Tier 4 — Primary government / adversary signal (48-hour window, ~9 sources)
**Japanese primary:** Kantei (PM statements), Chief Cabinet Secretary daily presser, MOFA press conferences, MOD / Joint Staff (scramble & intrusion announcements), METI, Bank of Japan.
**Adversary signal:** China MOFA statements on Japan, North Korea (launches/statements affecting Japan), Russia (statements on Japan / Northern Territories).

### Market data (daily strip)
Nikkei 225, USD/JPY, EUR/JPY, Brent crude, 10-year JGB yield, Bank of Japan policy rate, Japan 5Y CDS, GDP. *(Scraped live with sane fallbacks if a feed is down.)*

### Prestige outlets — mandatory inclusion
A Japan story from **WSJ, NYT, WaPo, Bloomberg, FT, The Economist, CNN, Reuters, Nikkei Asia, or Japan Times** is never dropped.

---

## 3. Newsletter structure (sections in delivery order)

1. **Header** — date, RE: line (one-sentence theme summary), editor's note
2. **Market Strip** — Nikkei · USD/JPY · EUR/JPY · 10Y JGB · BOJ rate · Brent
3. **Morning Memo** — exactly 3 one-line items (the elevator brief)
4. **Key Stat** — one striking number from the day's news
5. **Top Stories** — 2–4 biggest hard-news items, each with a "so what" and (when sourced) a precedent note
6. **Overnight Flash** — up to 6 secondary items
7. **Regional Pressure Watch** *(dark section)* — adversary signals: China/Senkaku, North Korea, Russia (see §5)
8. **Japanese Government** — Kantei, Chief Cabinet Secretary, MOFA, MOD/Joint Staff, METI, MOF, BOJ
9. **US–Japan Alliance & Trade** — tariff/defense/alliance dashboard
10. **Business & Economy** — corporates, BOJ, macro
11. **Indo-Pacific** — China-Japan, Korea-Japan, DPRK, trilateral, Quad, Taiwan, SE Asia, Australia, India
12. **Diet Watch** — House of Representatives, House of Councillors, budget, key bills, LDP leadership
13. **Expert Analysts** — Tier 2 op-eds + Tier 3 academic
14. **Public Sentiment & Approval Polling** — cabinet approval & party support (see §6)
15. **Social Statements** — sourced quotes from senior officials
16. **Also Today / The Wire** — up to 6 brief items
17. **On This Day** — a verified historical Japan event matching today's date
18. **Footer**

---

## 4. Topic taxonomy (Top Stories categories)

`Alliance` · `China-Japan` · `Korea-Japan` · `DPRK` · `Economy/BOJ` · `Politics/Diet` · `Defense` · `Technology` · `Indo-Pacific` · `Energy`

**Hard-blocked:** celebrity / J-pop / idol / anime-manga / fashion / lifestyle content — unless it carries a clear policy or security angle.

---

## 5. Regional Pressure Watch (adversary file)

The dark section tracks, each day: a **China signal** (MOFA statements on Japan, Senkaku/ECS activity, Taiwan-contingency framing), a **DPRK signal** (missile/nuclear activity affecting Japan), a **Russia signal** (Northern Territories, near-Japan air/naval activity), a **Senkaku status** line, sourced **key quotes**, and a **bottom line**. A persistent tracker carries baselines forward so streaks/changes are real, not guessed.

---

## 6. Public Sentiment & Approval Polling

Cabinet approval and party support drawn from **NHK, Jiji, Yomiuri, Asahi, and Kyodo** monthly polls.
**Same-poll rule:** every figure in a set must come from the *same pollster and the same survey date* — pollsters are never mixed within one number set, and the pollster + date range is always cited.

---

## 7. Editorial & quality rules

- **Source-or-skip:** every factual claim traces to a collected article or a provided reference baseline — no memory-based assertions. An omission beats an invention.
- **No editorializing:** facts, numbers, attributions, and connective context only; the expert reader draws conclusions.
- **URL integrity:** every link is copied verbatim from the source feed; hallucinated/unknown-domain links are stripped.
- **Anti-fabrication:** think-tank and academic items must exist in the feed with a real URL or they are excluded.
- **Deduplication:** one topic = one entry across the whole digest.

### Automated validation gates (pre-send)
- Word count ≥ 1,000 (target 1,200–1,400)
- Top Stories 2–4 · Overnight ≥ 3 · Morning Memo exactly 3
- No single source more than 3× across Top + Overnight
- No placeholder/blocked URLs; digest date matches today

---

## 8. Schedule & delivery

- **Daily 6:00 AM ET** via GitHub Actions (with later fallback runs). Manual trigger available.
- HTML email via Gmail (recipient list configured separately) + permanent web archive on GitHub Pages.
- Models: Claude Sonnet (primary) with Opus escalation on retry.

---

## 9. Items needing your decision / verification

1. **Sitting Prime Minister & cabinet.** Seeded from the official Kantei roster — **PM Sanae Takaichi** (LDP, first female PM; inaugurated Oct 21 2025, reshuffled Feb 18 2026), Chief Cabinet Secretary **Minoru Kihara**, Foreign Minister **Toshimitsu Motegi**, Defense Minister **Shinjiro Koizumi**, Finance Minister **Satsuki Katayama**, METI Minister **Ryosei Akazawa**, BOJ Governor **Kazuo Ueda**. Please confirm this is current. *(The live pipeline always defers to the names in the day's articles regardless.)*
2. **Recipient list.** Who receives it at launch? (Configured as a secret, not in code.)
3. **US–Japan trade/tariff baseline.** The alliance-and-trade baseline (Section 232 autos/steel, any 2024–25 US-Japan tariff arrangement, host-nation support, the 2% GDP defense plan) is marked "verify" — please confirm the current state you want as the standing baseline.
4. **Source adds/drops.** Any outlets, think tanks, or journals to add or remove?
5. **Section weighting.** Any section you want promoted, demoted, or cut (e.g., emphasis on Diet Watch vs. Alliance vs. Regional Pressure Watch)?
6. **Go-live date.**

*On approval, configure the GitHub secrets and enable the daily workflow — no code changes required to go live.*
