# Daily Japan Digest — Monthly Operating Cost

**Prepared for:** CSIS Japan Chair · **Prepared by:** Andy Lim

The only recurring cost of running the Daily Japan Digest is the **Anthropic (Claude) API** that writes the brief. Hosting, scheduling, email delivery, and data feeds are all free at this scale. Figures are benchmarked against the **Korea brief** (same Claude Sonnet → Opus setup, running daily for months); the Japan brief currently runs a touch leaner, so these are a safe upper estimate.

**Bottom line: ~$12–15/month — about $0.40 per daily issue.**

---

## Monthly estimate

One issue per day, ~30 issues/month.

| Scenario | Assumption | Monthly cost |
|---|---|---|
| Typical | Sonnet-generated, occasional Opus escalation (~15% of days) | ~$12–15 |
| + Weekly "Week in Review" | Adds a Friday synthesis, as the Korea brief runs | ~$16–18 |
| Worst case | Heavy news, frequent Opus escalation | ~$22–25 |

---

## Per issue

Korea-calibrated token usage: ~40,000 input + ~15,000 output tokens. Sonnet 4.6 is $3.00 / 1M input and $15.00 / 1M output; Opus 4.8 is $5.00 / $25.00.

| Component | Cost |
|---|---|
| Claude Sonnet generation | ~$0.37 |
| Optional Opus escalation (minority of days) | +$0.55–0.60 |
| Typical per issue | ~$0.40 |

---

## Everything else — $0

| Service | Cost | Why |
|---|---|---|
| GitHub Actions (compute) | $0 | Free minutes cover ~5 min/run × 30 |
| GitHub Pages (web archive) | $0 | Free static hosting |
| Gmail (delivery) | $0 | Under sending limits; recipients are free — adding readers doesn't change cost |
| Market data & news feeds | $0 | Public RSS + free endpoints |

---

## Notes

- **Recipients are free** — the digest is generated once and emailed to the whole list, so distribution can grow at no added cost.
- The main cost variable is **daily news volume** (input scales with feed richness); output is capped by the ~1,000–1,400-word target.
- The **Sonnet-first / Opus-on-retry** design keeps most days on the cheaper model, holding cost down.
- Adding a weekly "Week in Review" synthesis (as the Korea brief runs) adds roughly **$3–4/month**.

*In short: on the order of $12–15/month, or about a dollar a workweek.*
