# Setup & Operations Guide — Daily Japan Digest

How to configure, run, and operate the Daily Japan Digest pipeline. For *what* the digest contains and the source list, see `APPROVAL.md` / `SOURCES.md`. For architecture, see `CLAUDE.md`.

The pipeline runs unattended on **GitHub Actions** (daily cron + manual trigger). You can also run it locally for development. **Nothing emails until you add the Gmail secrets** — until then it just renders and archives.

---

## 1. What you need

| Thing | Why | Where to get it |
|---|---|---|
| **Anthropic API key** | Generates the digest (Claude) | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| **Gmail account + App Password** | Sends the email (SMTP) | A Gmail account with 2-Step Verification on → [App Passwords](https://myaccount.google.com/apppasswords) (16-char password, *not* your login password) |
| **Recipient list** | Who receives the brief | Any email address(es), comma-separated |
| **GitHub repo** | Hosts code + runs Actions + archives to Pages | `andysaulim/Daily-Japan-Digest` (already set up) |
| **(Optional) GitHub PAT** | Lets Actions push the archive on protected branches | [Fine-grained PAT](https://github.com/settings/tokens) with `Contents: write` on the repo |

> The Anthropic key alone is enough to **generate** a digest. The Gmail secrets are only needed to **send** it.

---

## 2. Configure GitHub (the production path)

### 2a. Add repository secrets
**Repo → Settings → Secrets and variables → Actions → "Secrets" tab → New repository secret.** Add:

| Secret name | Required? | Value |
|---|---|---|
| `ANTHROPIC_API_KEY` | **Yes** | `sk-ant-...` |
| `GMAIL_USER` | For sending | The sending Gmail address, e.g. `you@gmail.com` |
| `GMAIL_APP_PASS` | For sending | The 16-char Gmail App Password (spaces OK) |
| `DIGEST_TO` | For sending | Recipients, comma-separated: `a@x.com,b@y.com` |
| `GH_PAT` | Optional | PAT for archive push; falls back to the built-in `GITHUB_TOKEN` if unset |

### 2b. Add the variable (optional)
**Same page → "Variables" tab → New repository variable:**

| Variable | Value |
|---|---|
| `WEB_URL` | `https://andysaulim.github.io/Daily-Japan-Digest` (used for the email's "Read online" link) |

### 2c. Enable GitHub Pages (for the public archive)
**Repo → Settings → Pages → Build and deployment → Source: "Deploy from a branch" → Branch: `main` (or the active branch), folder: `/public` → Save.** Each run writes `public/index.html` (latest) + `public/YYYY-MM-DD.html` (archive).

---

## 3. Run it on GitHub Actions

### Manual trigger (recommended for testing)
**Repo → Actions tab → "Daily Japan Digest" (left sidebar) → "Run workflow" (top right).** Pick the branch, set the inputs, Run:

| Input | Default | Effect |
|---|---|---|
| `dry_run` | `false` | `true` = **collection only** (scrape feeds + market data, upload `collected.json`). No API key needed, no digest, no send. Good for testing sources. |
| `live_send` | `false` | `false` = **render only** (collect → digest → render → upload `digest.html` artifact, **no email, no archive commit**). `true` = full pipeline **including the email send**. |

**Recommended first runs:**
1. `dry_run = true` → confirm feeds work (no secrets needed).
2. `live_send = false` (both false) → confirm the digest generates and renders. Download the **`digest-output`** artifact from the run page to see `digest.html`.
3. `live_send = true` (with Gmail secrets set) → real send to `DIGEST_TO`. *Use a test recipient first.*

### Daily schedule
The workflow runs automatically at **10:00 UTC (6:00 AM ET)** every day via cron (`.github/workflows/daily-digest.yml`). Scheduled runs always run the full pipeline (collect → digest → render → **send** → archive). It will simply skip the send if the Gmail secrets aren't present.

> **To pause automated runs before go-live:** comment out the `schedule:` / `cron:` lines in `.github/workflows/daily-digest.yml`. Manual `workflow_dispatch` still works. Re-enable at launch.

---

## 4. Run it locally (development)

```bash
git clone https://github.com/andysaulim/Daily-Japan-Digest.git
cd Daily-Japan-Digest
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export ANTHROPIC_API_KEY="sk-ant-..."
# Only needed if you want to actually send:
export GMAIL_USER="you@gmail.com"
export GMAIL_APP_PASS="xxxx xxxx xxxx xxxx"
export DIGEST_TO="recipient@example.com"
export WEB_URL="https://andysaulim.github.io/Daily-Japan-Digest"   # optional
```

### Run modes (`run.py` flags)
```bash
python run.py                # Full pipeline: collect → digest → render → send → archive
python run.py --dry-run      # Collection only; writes collected.json
python run.py --from-cache   # Reuse collected.json (skip scraping)
python run.py --no-send      # Generate + render + archive, but don't email
python run.py --no-archive   # Don't write to public/
python run.py --force-send   # Send even if a validation gate fails
```

**Typical dev loop:** `python run.py --no-send` → open the generated `digest.html` in a browser. Add `--from-cache` after the first run to iterate on rendering/prompt without re-scraping.

> Requires Python 3.12+. The collector needs outbound internet (RSS, Yahoo Finance, Google News). The digest needs `ANTHROPIC_API_KEY`.

---

## 5. Verify a run

- **Actions run page** → the **`digest-output`** artifact contains `digest.html` (open in a browser), `digest.json`, and (on dry runs) `collected.json`.
- **Pipeline log** (Run pipeline step) shows: article counts per tier, word count, Google News decode rate, validation result, and send status.
- **Archive**: `public/index.html` and `public/YYYY-MM-DD.html` are committed after a scheduled or `live_send=true` run; viewable on GitHub Pages once enabled.
- **README "Latest Run"** table is auto-updated each run.

A healthy run logs something like:
```
✔ ~80 articles from ~20 sources
✓ ~1,100 words, 3 top stories, 4 overnight
✓ 14/17 decoded to real article URLs
✓ All validation checks passed
• Wrote ~48,000 bytes to digest.html
```

---

## 6. Routine maintenance

| Task | Where |
|---|---|
| **Update the PM / cabinet seed** | `digest.py` → `_POLITICAL_LEADERS` (the live pipeline always prefers names from the day's articles; this is just the fallback baseline) |
| **Add / remove a news source** | `collect.py` → the relevant `TIER1_FEEDS` … `TIER4_FEEDS` dict. Mirror the change in `SOURCES.md`. |
| **Adjust digest length / section counts** | `digest.py` → "DIGEST SYNTHESIS" section (target word count + per-section item caps) |
| **Add a flagged correspondent** | `collect.py` → `PRESTIGE_JOURNALISTS` and the `JOURNALIST FLAGGING` block in `digest.py` |
| **Reference timelines (Senkaku / alliance / DPRK)** | `databases.py` |
| **Trackers** (PM appearances, adversary signal) | `pm_tracker.json`, `region_tracker.json` (auto-maintained across runs) |

---

## 7. Troubleshooting

| Symptom in the log | Cause / fix |
|---|---|
| `Missing ANTHROPIC_API_KEY` | Add the secret (§2a) / export it locally |
| `Missing GMAIL_USER or GMAIL_APP_PASS — skipping send` | Expected when Gmail secrets aren't set — render/archive still succeed. Add them to enable email. |
| `does not support assistant message prefill` | Already fixed (we removed prefill). If it recurs, the model was changed to one rejecting prefill — keep the no-prefill path. |
| `All JSON extraction strategies failed` / truncation | Output hit the token cap. Already mitigated (tighter prompt + 32K cap + retry). If it returns, lower per-section item counts in `digest.py`. |
| `0/N decoded` Google News URLs | The decoder hit Google rate limits or a format change. Links still work (the pipeline keeps the browser-resolvable Google News link as fallback). |
| A market indicator shows `—` | That source failed its sanity check / was unreachable; the strip renders the others. (TOPIX was removed for this reason.) |
| Pages 404 | Enable GitHub Pages (§2c); first deploy can take a couple of minutes. |

---

## 8. Go-live checklist

- [ ] `ANTHROPIC_API_KEY` secret set
- [ ] `dry_run=true` test run is green (sources work)
- [ ] `live_send=false` test run produces a good `digest.html` artifact
- [ ] Japan Chair has reviewed `APPROVAL.md` / `JAPAN_DIGEST_OVERVIEW.docx`
- [ ] PM / cabinet seed confirmed current (`digest.py`)
- [ ] `GMAIL_USER` / `GMAIL_APP_PASS` / `DIGEST_TO` secrets set
- [ ] One `live_send=true` test to a **test** recipient looks right
- [ ] `DIGEST_TO` updated to the real distribution list
- [ ] GitHub Pages enabled; `WEB_URL` variable set
- [ ] Daily `cron` enabled in the workflow

---

*Prepared by Andy Lim · CSIS Japan Chair*
