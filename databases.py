"""
Japan Reference Context Integration
Provides compact, verified reference timelines injected into the digest LLM prompt:
- Senkaku / East China Sea incident timeline
- US-Japan alliance milestone timeline
- North Korea missiles-over-Japan reference

These are STATIC, well-established historical references — they prevent the model
from hallucinating baselines. build_db_context() returns a string used in the prompt.
"""

# ── Senkaku / East China Sea incident timeline ────────────────────────────────
_SENKAKU_TIMELINE = [
    ("1895", "Japan incorporates the Senkaku Islands into Okinawa Prefecture."),
    ("1971", "China and Taiwan begin asserting claims after a UN survey suggests seabed hydrocarbons."),
    ("Sep 2010", "Trawler collision: Chinese fishing boat rams two Japan Coast Guard vessels near the Senkakus; captain's detention triggers a China rare-earth export halt."),
    ("Sep 2012", "Japan's government 'nationalizes' three of the Senkaku Islands (purchase from private owner), triggering anti-Japan protests across China and sustained CCG patrols."),
    ("Nov 2013", "China declares an East China Sea Air Defense Identification Zone (ADIZ) overlapping the Senkakus; US/Japan/ROK reject it."),
    ("2016 onward", "China Coast Guard establishes near-daily presence in the contiguous zone; record patrol-days and territorial-water intrusions recur annually."),
    ("2021", "China's Coast Guard Law authorizes use of force in claimed waters, raising Senkaku escalation risk."),
    ("2024-2025", "Record CCG and PLAN activity near the Senkakus; first confirmed PLA aircraft intrusion into Japanese airspace (Aug 2024) and PLA carrier transits near the Nansei (Ryukyu) chain."),
]

# ── US-Japan alliance milestone timeline ──────────────────────────────────────
_ALLIANCE_TIMELINE = [
    ("Sep 8 1951", "San Francisco Peace Treaty signed (in force Apr 28 1952), ending the Occupation; original US-Japan Security Treaty signed the same day."),
    ("Jan 19 1960", "Revised Treaty of Mutual Cooperation and Security signed in Washington — the foundation of today's alliance; Article 5 commits the US to Japan's defense."),
    ("1972", "Okinawa reverts to Japanese administration; the US retains major bases including Kadena and Futenma."),
    ("1996", "SACO agreement to relocate MCAS Futenma; the Henoko (Camp Schwab) replacement remains contested in Okinawa."),
    ("2015", "Revised US-Japan Defense Guidelines and Japan's security legislation permitting limited collective self-defense."),
    ("Dec 2022", "Japan's National Security Strategy commits to counterstrike capability and raising defense spending toward 2% of GDP by FY2027."),
    ("2024-2025", "Alliance 'modernization': upgraded US Forces Japan command, expanded co-production, and trade/tariff negotiations under the second Trump administration."),
]

# ── North Korea missiles-over / near Japan reference ──────────────────────────
_DPRK_OVER_JAPAN = [
    ("Aug 31 1998", "Taepodong-1 flies over Japan into the Pacific — first DPRK missile overflight; spurs Japan-US missile-defense cooperation."),
    ("Aug 29 2017", "Hwasong-12 IRBM overflies Hokkaido; J-Alert sirens sound across northern Japan."),
    ("Sep 15 2017", "Second 2017 IRBM overflight of Hokkaido."),
    ("Oct 4 2022", "Hwasong-12 again overflies Japan; first overflight in five years, triggering J-Alert."),
    ("Recurring", "Short- and medium-range ballistic missiles routinely splash down in or near Japan's EEZ in the Sea of Japan; Japan protests each via MOFA."),
]


# Most recent VERIFIED cabinet-approval polls. This is the authoritative FALLBACK
# for the Public Sentiment table — used only when the Wikipedia fetcher in
# collect.py can't reach the live aggregator (which returns every house with both
# numbers). SOURCE-OR-SKIP applies: seed ONLY pollsters where both the approval
# AND the disapproval figure are independently confirmed from a published report.
# Never ship an approve-only row or a stale number to fill the table out.
#
# July 2026 (both figures confirmed): Jiji (Jul 16, Jiji Press) and Mainichi
# (Jul 20, Mainichi Shimbun) — both fell below 50% for the first time under
# Takaichi; Mainichi's disapproval (44%) now overtakes approval (41%).
# The high houses' July approvals are on record (NHK 58%, Nikkei/TV Tokyo 66%,
# JNN 65.9%) but their disapproval breakdowns were not confirmable at seed time,
# so they are intentionally omitted here and left to the live fetcher.
# UPDATE ~monthly as new polls publish; only add a house once BOTH numbers verify.
RECENT_APPROVAL_POLLS = [
    {"pollster": "Jiji",     "poll_date": "Jul 16, 2026", "cabinet_approval": "49.0%", "cabinet_disapproval": "25.2%", "approval_change": "-5.3"},
    {"pollster": "Mainichi", "poll_date": "Jul 20, 2026", "cabinet_approval": "41%",   "cabinet_disapproval": "44%",   "approval_change": "-10"},
]


def build_db_context(max_chars: int = 4000) -> str:
    """Build a textual reference-context block for the digest LLM prompt."""
    blocks = []

    lines = ["SENKAKU / EAST CHINA SEA INCIDENT TIMELINE (verified reference — use for pattern_note / on_this_day only when relevant):"]
    for date, event in _SENKAKU_TIMELINE:
        lines.append(f"  • {date}: {event}")
    blocks.append("\n".join(lines))

    lines = ["US-JAPAN ALLIANCE MILESTONES (verified reference):"]
    for date, event in _ALLIANCE_TIMELINE:
        lines.append(f"  • {date}: {event}")
    blocks.append("\n".join(lines))

    lines = ["NORTH KOREA MISSILES OVER / NEAR JAPAN (verified reference):"]
    for date, event in _DPRK_OVER_JAPAN:
        lines.append(f"  • {date}: {event}")
    blocks.append("\n".join(lines))

    context = "\n\n".join(blocks)
    return context[:max_chars] if max_chars else context


if __name__ == "__main__":
    print(build_db_context())
