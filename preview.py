"""Render a representative brief to preview.html for the visual check.

test_render_visual.py measures computed style in a real browser — contrast,
typeface count, horizontal overflow — and none of that is visible by reading
the HTML. It needs a page to measure, and nothing produced one, so the check
existed and never ran.

This builds a digest that exercises every section, so the measurement covers
the whole brief rather than whatever happened to be in the news.

    python3 preview.py && BRIEF_HTML=preview.html python3 test_render_visual.py
"""
import pathlib
import render

DIGEST = {'also_today': [{'body_text': 'METI names recipients.',
                 'category': 'trade',
                 'headline': 'Chip subsidy tranche released',
                 'source': 'Nikkei',
                 'url': 'https://example.org/6'},
                {'body_text': 'Budget testimony next week.',
                 'category': 'politics',
                 'headline': 'Diet committee sets hearing date',
                 'source': 'NHK World',
                 'url': 'https://example.org/7'}],
 'calendar_watch': [{'confirmed': True,
                     'date': '2026-09-12',
                     'day': 12,
                     'detail': 'First since the pact.',
                     'event': 'PIF leaders meet',
                     'headline': 'PIF leaders meet',
                     'month': 'Sep',
                     'why_it_matters': 'First since the pact.'}],
 'key_stat': {'context': 'Highest since 2008.',
              'label': 'BOJ policy rate after the expected hike',
              'number': '1.25%',
              'source': 'Bank of Japan'},
 'market_indicators': {'boj_rate': {'value': '1.25%'},
                       'brent': {'change_pct': 5.36, 'value': '100.64'},
                       'nikkei': {'change_pct': 1.45, 'value': '65,142.78'},
                       'usd_jpy': {'change_pct': -3.52, 'value': '153.32'}},
 'morning_memo': ['The yen reached a seven-month high against the dollar.',
                  '**Ueda Kazuo** signalled a rate decision is close.',
                  'Nagoya flooding displaced 4,000 households.'],
 'overnight_items': [{'body_text': 'Second passage this week.',
                      'category': 'Security',
                      'headline': 'Destroyer transits the Miyako Strait',
                      'source': 'Kyodo',
                      'url': 'https://example.org/3'},
                     {'body_text': 'Officials meet Thursday.',
                      'category': 'Trade',
                      'headline': 'Tariff talks resume in Washington',
                      'source': 'Asahi',
                      'url': 'https://example.org/4'},
                     {'body_text': 'Members join the CDP.',
                      'category': 'Politics',
                      'headline': 'Opposition CRA disbands',
                      'source': 'Mainichi',
                      'url': 'https://example.org/5'}],
 'pdf_url': 'https://example.org/digest_2026-09-09.pdf',
 're_line': 'Yen surges to 7-month high · BOJ rate hike imminent · Nagoya floods',
 'top_stories': [{'body': 'The currency strengthened *3.5 percent* on the week as '
                          '**Ueda Kazuo** signalled a hike.',
                  'category_tag': 'Economy',
                  'headline': 'Yen surges to seven-month high',
                  'source': 'Nikkei',
                  'src_line': 'per Nikkei',
                  'url': 'https://example.org/1'},
                 {'body': 'Disaster relief for Nagoya leads the package.',
                  'category_tag': 'Politics',
                  'headline': 'Cabinet approves supplementary budget',
                  'source': 'Yomiuri',
                  'src_line': 'per Yomiuri',
                  'url': 'https://example.org/2'}],
 'web_url': 'https://andysaulim.github.io/Daily-Japan-Digest/index.html'}

if __name__ == "__main__":
    html = render.render_html(dict(DIGEST))
    pathlib.Path("preview.html").write_text(html, encoding="utf-8")
    print(f"preview.html written ({len(html):,} chars)")
