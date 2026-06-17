"""
Regional Pressure Tracker (adversary-signal baseline)
Persists a rolling history of adversary signals toward Japan across runs in
region_tracker.json. Exposes build_context_block() for the digest LLM prompt.

Tracks daily watch flags and one-line signal summaries for the three adversary
vectors that bear on Japan: China (Senkaku / ECS / Taiwan), North Korea
(missile / nuclear activity affecting Japan), and Russia (Northern Territories /
Sea of Okhotsk activity).
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

TRACKER_FILE = Path(__file__).parent / "region_tracker.json"

# Adversary vectors tracked (key / English label)
TRACKED_VECTORS = [
    ("china_signal", "China — Senkaku / East China Sea / Taiwan"),
    ("dprk_signal", "North Korea — missile / nuclear activity affecting Japan"),
    ("russia_signal", "Russia — Northern Territories / Sea of Okhotsk / air-sea activity"),
]


def _load() -> dict:
    if not TRACKER_FILE.exists():
        return {"daily_signals": {}, "last_updated": None}
    try:
        with open(TRACKER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"daily_signals": {}, "last_updated": None}


def _save(data: dict) -> None:
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def record_day(date_iso: str, signals: dict, watch_flag: bool = False) -> None:
    """Record one day's adversary-signal summary.
    signals: {vector_key: one-line summary string}
    """
    data = _load()
    data["daily_signals"][date_iso] = {"signals": signals, "watch_flag": watch_flag}
    cutoff = (datetime.now(timezone.utc) - timedelta(days=60)).strftime("%Y-%m-%d")
    data["daily_signals"] = {k: v for k, v in data["daily_signals"].items() if k >= cutoff}
    _save(data)


def build_context_block() -> str:
    """Build the prompt context block for digest.py."""
    data = _load()
    if not data["daily_signals"]:
        return ""

    lines = [
        "REGIONAL PRESSURE HISTORY (persistent adversary-signal tracker, last 60 days):",
        "",
        "TRACKED ADVERSARY VECTORS:",
    ]
    for key, label in TRACKED_VECTORS:
        lines.append(f"  • {label}")
    lines.append("")

    recent_dates = sorted(data["daily_signals"].keys(), reverse=True)[:7]
    if recent_dates:
        lines.append("RECENT DAILY SIGNALS (last 7 days with data):")
        for d in recent_dates:
            day = data["daily_signals"][d]
            flag = " [WATCH]" if day.get("watch_flag") else ""
            lines.append(f"  • {d}{flag}:")
            for key, label in TRACKED_VECTORS:
                val = (day.get("signals") or {}).get(key)
                if val:
                    short = label.split(" — ")[0]
                    lines.append(f"      - {short}: {val}")
        lines.append("")

    lines.append("Use this history for context on whether today's adversary activity is")
    lines.append("a continuation or a change. Do NOT fabricate streak counts not supported here.")
    return "\n".join(lines)


def update_from_digest(digest: dict) -> None:
    """Extract adversary signals from the regional_watch (xinhua_delta) object and persist."""
    rw = digest.get("xinhua_delta") or {}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    signals = {}
    for key, _ in TRACKED_VECTORS:
        val = rw.get(key)
        if isinstance(val, str) and val.strip():
            signals[key] = val.strip()[:300]

    watch_flag = bool(rw.get("watch_flag"))

    if signals or watch_flag:
        record_day(today, signals, watch_flag)


if __name__ == "__main__":
    print(build_context_block())
