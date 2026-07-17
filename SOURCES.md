# Sources — Daily Japan Digest

Full, exact inventory of every source the pipeline pulls before anything reaches the Claude API. This is the complete input surface: **~110 RSS/news feeds across 4 tiers + a PM-appearance tracker group**, plus live market endpoints and static reference databases. Nothing else is fed to the model — and per the **source-or-skip** rule, every claim in the digest must trace to one of these inputs or a reference baseline (no memory-based assertions).

> **How feeds are queried.** Most feeds are Google News RSS searches scoped to a specific outlet/domain (shown as the search string below); some are the outlet's direct RSS. Each tier has a recency window — articles older than the window are dropped. Tier 1 is keyword-filtered for Japan relevance; lifestyle/entertainment is hard-blocked.

---

## Tier 1 — News (24-hour window · 47 feeds)

### International press — Japan coverage
| Source | Query / feed |
|---|---|
| WSJ Japan | `Japan site:wsj.com` |
| NYT Japan | `Japan site:nytimes.com` |
| Washington Post Japan | `Japan site:washingtonpost.com` |
| FT Japan | `Japan site:ft.com` |
| Reuters Japan | `Japan site:reuters.com` |
| AP Japan | `Japan site:apnews.com` |
| AFP Japan | `Japan site:afp.com` |
| Bloomberg Japan | `Japan site:bloomberg.com` |
| BBC Japan | `Japan site:bbc.com` |
| CNN Japan | `Japan site:cnn.com` |
| CNBC Japan | `Japan site:cnbc.com` |
| The Economist Japan | `Japan site:economist.com` |
| The Guardian Japan | `Japan site:theguardian.com` |

### Japanese press (English editions)
| Source | Query / feed |
|---|---|
| NHK World | `site:www3.nhk.or.jp/nhkworld` |
| Kyodo News | `site:english.kyodonews.net` |
| The Japan Times | `site:japantimes.co.jp` |
| Mainichi | `site:mainichi.jp/english` |
| Asahi (AJW) | `site:asahi.com/ajw` |
| The Japan News (Yomiuri) | `site:the-japan-news.com` |
| Nikkei Asia | `Japan site:asia.nikkei.com` |
| Jiji Press | `Japan site:jiji.com OR "Jiji Press"` |
| Japan Forward | `site:japan-forward.com` |

### US government
| Source | Query / feed |
|---|---|
| White House | `Japan site:whitehouse.gov` |
| State Department | `Japan site:state.gov` |
| Pentagon | `Japan site:defense.gov` |
| Treasury | `Japan site:treasury.gov` |
| USTR | `Japan site:ustr.gov` |
| Commerce | `Japan site:commerce.gov` |
| INDOPACOM | `Japan OR "Self-Defense" site:pacom.mil` |
| US Forces Japan | `"U.S. Forces Japan" OR site:usfj.mil` |

### Japanese government
| Source | Query / feed |
|---|---|
| Kantei / PMO | `site:japan.kantei.go.jp` |
| MOFA | `site:mofa.go.jp` |
| MOD | `site:mod.go.jp` |
| METI | `site:meti.go.jp` |
| MOF | `site:mof.go.jp` |
| Bank of Japan | `site:boj.or.jp` |

### Regional reaction
| Source | Query / feed |
|---|---|
| Yonhap (on Japan) | `Japan site:en.yna.co.kr` |
| Korea Herald (on Japan) | `Japan site:koreaherald.com` |
| Global Times (on Japan) | `Japan site:globaltimes.cn` |
| Xinhua (on Japan) | `Japan site:xinhuanet.com` |
| TASS (on Japan) | `Japan site:tass.com` |
| The Australian (on Japan) | `Japan site:theaustralian.com.au` |
| Indian Express (on Japan) | `Japan site:indianexpress.com` |
| Rappler (on Japan) | `Japan site:rappler.com` |

### Specialist
| Source | Query / feed |
|---|---|
| The Diplomat (Japan) | `Japan site:thediplomat.com` |
| Tokyo Review | `site:tokyoreview.net` |
| Observing Japan | `site:observingjapan.com OR "Observing Japan"` |

---

## Tier 2 — Analysis / think tanks (36-hour window · 30 feeds)

Bracketed letter = prestige weight (`A` = top-tier, mandatory-include when same-day; `B` = standard).

| Source | Weight | Query / feed |
|---|---|---|
| CSIS Japan Chair | A | `Japan site:csis.org` |
| Brookings (Mireya Solís) | A | `Japan site:brookings.edu` |
| CFR (Sheila Smith) | A | `Japan site:cfr.org` |
| RAND (Jeffrey Hornung) | A | Direct RSS: `rand.org/topics/japan.xml` |
| Carnegie | A | `Japan site:carnegieendowment.org` |
| Stimson | A | `Japan site:stimson.org` |
| Hudson | B | `Japan site:hudson.org` |
| Sasakawa USA | A | `site:spfusa.org OR "Sasakawa USA"` |
| Sasakawa Peace Foundation | B | `site:spf.org Japan` |
| NBR | A | `Japan site:nbr.org` |
| East-West Center | B | `Japan site:eastwestcenter.org` |
| Lowy Institute | B | `Japan site:lowyinstitute.org` |
| IISS | A | `Japan site:iiss.org` |
| Atlantic Council | B | `Japan site:atlanticcouncil.org` |
| German Marshall Fund | B | `Japan site:gmfus.org` |
| Asia Society Policy Institute | B | `Japan site:asiasociety.org/policy-institute` |
| Pacific Forum | A | `site:pacforum.org Japan` |
| Congressional Research Service | A | `Japan site:crsreports.congress.gov OR "Congressional Research Service"` |
| Asia Policy Point | B | `site:jiaponline.org OR "Asia Policy Point"` |
| Japan Economy Watch (Richard Katz) | B | `site:richardkatz.substack.com OR "Japan Economy Watch"` |
| VUB/CSDS Japan Chair | B | `site:csds.vub.be Japan` |
| ASAN Institute | B | `Japan site:en.asaninst.org OR "Asan Institute"` |
| ISEAS–Yusof Ishak Institute | B | `Japan site:iseas.edu.sg` |
| Genron NPO | B | `site:genron-npo.net OR "Genron NPO"` |
| Chicago Council on Global Affairs | B | `Japan site:globalaffairs.org OR "Chicago Council"` |
| Pew Research Center | B | `Japan site:pewresearch.org` |
| University Japan programs | B | `Japan ("Reischauer" OR "MIT Japan" OR "Georgetown") policy` |
| Foreign Affairs | A | `Japan site:foreignaffairs.com` |
| Foreign Policy | B | `Japan site:foreignpolicy.com` |
| War on the Rocks | B | `Japan site:warontherocks.com` |

---

## Tier 3 — Academic journals (72-hour window · 18 feeds)

Bracketed letter = journal tier (inclusion threshold rises from `A+` → `A` → `B`).

| Journal | Tier | Query |
|---|---|---|
| International Security | A+ | `"International Security" "Japan"` |
| International Organization | A+ | `"International Organization" "Japan"` |
| Security Studies | A | `"Security Studies" "Japan"` |
| The Washington Quarterly | A | `"Washington Quarterly" "Japan"` |
| Survival (IISS) | A | `"Survival" IISS "Japan"` |
| Journal of Strategic Studies | A | `"Journal of Strategic Studies" "Japan"` |
| Journal of East Asian Studies | A | `"Journal of East Asian Studies" "Japan"` |
| Asia Policy (NBR) | A | `"Asia Policy" NBR "Japan"` |
| International Relations of the Asia-Pacific | A | `"International Relations of the Asia-Pacific" "Japan"` |
| The Pacific Review | A | `"The Pacific Review" "Japan"` |
| Asian Survey | B | `"Asian Survey" "Japan"` |
| Asian Security | B | `"Asian Security" "Japan"` |
| Pacific Affairs | B | `"Pacific Affairs" "Japan"` |
| Asia-Pacific Journal: Japan Focus | B | `site:apjjf.org OR "Asia-Pacific Journal" Japan Focus` |
| Journal of Japanese Studies | B | `"Journal of Japanese Studies"` |
| Contemporary Japan | B | `"Contemporary Japan" journal` |
| Japan Review | B | `"Japan Review" Nichibunken` |
| Social Science Japan Journal | B | `"Social Science Japan Journal"` |

---

## Tier 4 — Government primary + adversary signal (48-hour window · 9 feeds)

### Japanese government primary
| Source | Query |
|---|---|
| Kantei / PM | `"Prime Minister" Japan statement OR "press conference" site:japan.kantei.go.jp` |
| Chief Cabinet Secretary | `"Chief Cabinet Secretary" Japan press conference` |
| MOFA presser | `Japan "Foreign Ministry" OR "MOFA" press conference OR statement` |
| MOD / Joint Staff | `Japan "Joint Staff" OR "Defense Ministry" scramble OR incursion OR statement` |
| METI | `Japan "METI" OR "Ministry of Economy" statement OR policy` |
| BOJ | `"Bank of Japan" statement OR "policy meeting" OR Ueda` |

### Adversary signal (feeds the Regional Pressure Watch)
| Source | Query |
|---|---|
| China MOFA (on Japan) | `China "Foreign Ministry" Japan OR Senkaku statement OR spokesperson` |
| North Korea (affecting Japan) | `"North Korea" missile OR launch Japan OR "Sea of Japan" OR KCNA` |
| Russia (on Japan) | `Russia Japan "Northern Territories" OR Kuril statement OR TASS` |

---

## PM appearance tracker (72-hour window · 5 feeds)

Feeds the persistent PM-appearance log ("days since last seen"). Queries are leader-agnostic plus a last-known-name fallback so they remain correct if the sitting PM changes.

| Source | Query |
|---|---|
| PM appearance | `"Japanese Prime Minister" OR "Japan's Prime Minister" attended OR visited OR met OR spoke` |
| PM Diet | `Japan "Prime Minister" Diet OR "Lower House" OR "Upper House" session` |
| PM press conference | `Japan "Prime Minister" "press conference" OR statement OR remarks` |
| PM diplomacy | `Japan "Prime Minister" summit OR bilateral OR "telephone talks"` |
| PM (by name) | `"Takaichi" OR "Ishiba" Japan Prime Minister` |

---

## Market data (live, fetched each run)

| Indicator | Primary source | Fallback |
|---|---|---|
| Nikkei 225 (`^N225`) | Yahoo Finance | Stooq |
| USD/JPY (`JPY=X`) | Yahoo Finance | Stooq |
| EUR/JPY (`EURJPY=X`) | Yahoo Finance | Stooq |
| Brent crude (`BZ=F`) | Yahoo Finance | Stooq |
| 10Y JGB yield | worldgovernmentbonds.com | fixed fallback 1.50% |
| BOJ policy rate | Google News scrape | fixed fallback 1.00% |
| Japan 5Y CDS | worldgovernmentbonds.com | fixed fallback ~20 bps |
| GDP / macro (CPI, core CPI, Tankan, unemployment) | Google News scrape | estimate, marked as such |

Market values are passed through to the digest **verbatim** — the model does not compute or alter them.

---

## Static reference databases (injected into the prompt)

Provided as ground-truth context so the model never guesses historical baselines (`databases.py`):

- **Senkaku / East China Sea incident timeline** — key dated events (2010 trawler collision, 2012 nationalization, 2013 ADIZ, recurring CCG intrusions).
- **US–Japan alliance milestone timeline** — treaty and basing milestones.
- **DPRK launches over/near Japan** — 1998 Taepodong, 2017 overflights, 2022 overflight.

Plus persistent JSON trackers carried across runs (`pm_tracker.json`, `region_tracker.json`) so PM-appearance streaks and adversary-signal baselines are real history rather than model recall.

---

## Editorial guardrails on these sources

- **Source-or-skip** — every claim traces to a collected article or a reference baseline above.
- **Prestige enforcement** — a same-day Japan story from WSJ, NYT, WaPo, Bloomberg, FT, The Economist, CNN, Reuters, Nikkei Asia, or Japan Times is never dropped.
- **URL integrity** — links are copied verbatim from the feed; unknown-domain/hallucinated links are stripped before send.
- **Anti-fabrication** — think-tank and academic items must exist in the feed with a real URL or they are excluded.
- **Lifestyle/entertainment** — hard-blocked unless it carries a clear policy or security angle.

*Adding or removing a source is a one-line change in `collect.py`; this file should be updated to match.*
