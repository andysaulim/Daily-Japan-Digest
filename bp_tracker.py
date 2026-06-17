"""
Japan Security-Watch Locations Tracker
Persists last-known status for ~9 monitored sites relevant to Japan's security.
Exposes build_context_block() for the digest LLM prompt.

All sites belong to a single "security_watch" block covering China gray-zone,
DPRK launch geography, Russia (Northern Territories), and USFJ basing.
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

TRACKER_FILE = Path(__file__).parent / "bp_tracker.json"

# ─────────────────────────────────────────────────────────────────────────────
# LOCATION DEFINITIONS (canonical name / CSIS or reference product / what to watch)
# ─────────────────────────────────────────────────────────────────────────────

SECURITY_LOCATIONS = [
    {
        "name": "Senkaku Islands / East China Sea ADIZ",
        "csis_product": "AMTI East China Sea",
        "watching": "China Coast Guard patrol-days in the contiguous zone, territorial-water intrusions, PLA aircraft/vessel activity, JASDF scrambles",
    },
    {
        "name": "Sea of Japan (DPRK missile splashdown zone)",
        "csis_product": "Missile Defense Project (CSIS)",
        "watching": "North Korean ballistic-missile launches and EEZ splashdowns, J-Alert activations",
    },
    {
        "name": "Tsushima / Korea Strait",
        "csis_product": "—",
        "watching": "ROK/Japan maritime activity, transiting PLAN/Russian vessels",
    },
    {
        "name": "Okinawa / USFJ (Kadena, Futenma, Henoko)",
        "csis_product": "—",
        "watching": "Futenma-Henoko relocation, base incidents, USFJ posture and command changes",
    },
    {
        "name": "Yonaguni / Ishigaki (Nansei buildup)",
        "csis_product": "—",
        "watching": "JSDF missile-unit deployments, radar sites, Sakishima island defenses near Taiwan",
    },
    {
        "name": "Northern Territories / Sea of Okhotsk",
        "csis_product": "—",
        "watching": "Russian military exercises and deployments on the disputed islands; air-sea activity",
    },
    {
        "name": "Nemuro Strait",
        "csis_product": "—",
        "watching": "Russian vessel transits and incidents off Hokkaido",
    },
    {
        "name": "DPRK launch sites (Sohae/Tongchang-ri, Punggye-ri)",
        "csis_product": "Beyond Parallel / Missile Defense Project (CSIS)",
        "watching": "Satellite-imaged launch-pad activity, nuclear test-site readiness affecting Japan",
    },
    {
        "name": "Okinotorishima EEZ",
        "csis_product": "—",
        "watching": "Chinese survey/research-vessel activity inside Japan's EEZ around the atoll",
    },
]

ALL_LOCATIONS = [{**loc, "block": "security_watch"} for loc in SECURITY_LOCATIONS]


# ─────────────────────────────────────────────────────────────────────────────
# STORAGE
# ─────────────────────────────────────────────────────────────────────────────

def _empty_status() -> dict:
    return {
        "status": "normal",       # normal | activity | elevated | alert
        "note": "No reporting yet",
        "last_source_date": None,
        "direction": "",          # up | down | ""
        "updated_at": None,
    }


def _load() -> dict:
    if not TRACKER_FILE.exists():
        return {
            "locations": {loc["name"]: _empty_status() for loc in ALL_LOCATIONS},
            "last_updated": None,
        }
    try:
        with open(TRACKER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for loc in ALL_LOCATIONS:
            if loc["name"] not in data.get("locations", {}):
                data.setdefault("locations", {})[loc["name"]] = _empty_status()
        return data
    except (json.JSONDecodeError, OSError):
        return {
            "locations": {loc["name"]: _empty_status() for loc in ALL_LOCATIONS},
            "last_updated": None,
        }


def _save(data: dict) -> None:
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_location(name: str, status: str, note: str, source_date: str,
                    direction: str = "") -> None:
    """Update a single location's last-known status."""
    data = _load()
    if name not in data["locations"]:
        data["locations"][name] = _empty_status()
    data["locations"][name].update({
        "status": status,
        "note": note,
        "last_source_date": source_date,
        "direction": direction,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    _save(data)


def get_status(name: str) -> dict:
    return _load()["locations"].get(name, _empty_status())


def build_context_block() -> str:
    """Build the prompt context block for digest.py with last-known status for each location."""
    data = _load()
    lines = [
        "JAPAN SECURITY-WATCH LOCATIONS HISTORY (persistent tracker — last known status for each site):",
        "",
        "Use these as GROUND TRUTH. If today's articles update a location, override.",
        "Otherwise CARRY FORWARD the note verbatim — do NOT replace with 'no new reporting'.",
        "",
    ]
    for loc in SECURITY_LOCATIONS:
        s = data["locations"].get(loc["name"], _empty_status())
        date_str = s.get("last_source_date") or "—"
        lines.append(
            f"  • {loc['name']} [{s['status']}] (last: {date_str}, "
            f"dir: {s.get('direction') or '—'}): {s['note']}"
        )
    return "\n".join(lines)


def location_names_for_prompt() -> dict:
    """Return location names for digest.py prompt."""
    return {"security_watch": [loc["name"] for loc in SECURITY_LOCATIONS]}


def update_from_digest(digest: dict) -> None:
    """Extract monitored location updates from digest output and persist them."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    valid_names = {loc["name"] for loc in ALL_LOCATIONS}

    for loc in (digest.get("monitored_locations") or []):
        name = (loc.get("name") or "").strip()
        if name not in valid_names:
            continue
        note = (loc.get("note") or "").strip()
        if not note or note.lower() == "no new reporting":
            continue
        status = loc.get("status", "normal")
        direction = loc.get("direction", "")
        source_date = loc.get("last_source_date") or today
        update_location(name, status, note, source_date, direction)


if __name__ == "__main__":
    print(build_context_block())
