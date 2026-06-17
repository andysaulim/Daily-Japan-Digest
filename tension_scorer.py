"""
Daily Tension Scorer — Japan
Outputs 0–10 scores for three axes based on keyword signals in today's articles:
- Senkaku / East China Sea tension (China gray-zone activity vs Japan)
- DPRK tension affecting Japan (missile launches, EEZ splashdowns, overflights)
- Russia / Northern Territories tension

Used by render.py as an optional Δ Since Yesterday badge.
"""
import re

SENKAKU_ECS_SIGNALS = {
    "escalation": re.compile(
        r"senkaku|diaoyu|east\s+china\s+sea|"
        r"\bccg\b|china\s+coast\s+guard|coast\s+guard\s+vessel|"
        r"contiguous\s+zone|territorial\s+waters\s+(intrusion|incursion)|"
        r"adiz|scramble[ds]?|airspace\s+(intrusion|violation)|"
        r"survey\s+(ship|vessel)|okinotorishima|yonaguni|ishigaki",
        re.IGNORECASE,
    ),
    "deescalation": re.compile(
        r"japan-?china\s+(dialogue|talks|summit|meeting|hotline)|"
        r"east\s+china\s+sea\s+(stable|calm|reduced)",
        re.IGNORECASE,
    ),
}

DPRK_SIGNALS = {
    "escalation": re.compile(
        r"north\s+korea.*(missile|launch|test)|dprk.*(missile|launch)|"
        r"ballistic\s+missile|icbm|\beez\b|splashdown|"
        r"overfl(y|ew|ight)\s+japan|j-?alert|nuclear\s+test|"
        r"pyongyang.*(missile|provocation)",
        re.IGNORECASE,
    ),
    "deescalation": re.compile(
        r"north\s+korea.*(talks|dialogue|diplomacy|abduct(ee|ion)\s+resolution)|"
        r"denuclear",
        re.IGNORECASE,
    ),
}

RUSSIA_SIGNALS = {
    "escalation": re.compile(
        r"northern\s+territories|kuril|sea\s+of\s+okhotsk|nemuro|"
        r"russia.*(aircraft|bomber|warship|vessel).*(japan|hokkaido)|"
        r"tu-?95|russian\s+(incursion|patrol).*japan",
        re.IGNORECASE,
    ),
    "deescalation": re.compile(
        r"japan-?russia\s+(talks|dialogue|peace\s+treaty)|"
        r"northern\s+territories\s+(return|negotiation)",
        re.IGNORECASE,
    ),
}


def _score_axis(articles: list, signals: dict, baseline: int = 5) -> int:
    """Score one axis 0–10 based on signal counts in article titles + summaries."""
    esc = 0
    deesc = 0
    for art in articles:
        text = f"{art.get('title', '')} {art.get('summary', '')}"
        if signals["escalation"].search(text):
            esc += 1
        if signals["deescalation"].search(text):
            deesc += 1
    # Cap each side to prevent runaway scores
    esc = min(esc, 8)
    deesc = min(deesc, 8)
    score = baseline + (esc // 2) - (deesc // 2)
    return max(0, min(10, score))


def score_all(payload: dict) -> dict:
    """Score all three axes from a collected payload."""
    all_articles = (
        (payload.get("tier1") or [])
        + (payload.get("tier2") or [])
        + (payload.get("tier4") or [])
    )
    return {
        "senkaku_ecs": _score_axis(all_articles, SENKAKU_ECS_SIGNALS),
        "dprk": _score_axis(all_articles, DPRK_SIGNALS),
        "russia": _score_axis(all_articles, RUSSIA_SIGNALS),
    }


if __name__ == "__main__":
    import json, sys
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            payload = json.load(f)
        print(json.dumps(score_all(payload), indent=2))
    else:
        print("Usage: python tension_scorer.py <collected.json>")
