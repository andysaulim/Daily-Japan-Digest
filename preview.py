"""Render a representative brief to preview.html for the visual check.

test_render_visual.py measures computed style in a real browser — contrast,
typeface count, horizontal overflow — and none of that is visible by reading
the HTML. It needs a page to measure, and nothing produced one, so the check
existed and never ran.

This builds a digest that exercises every section, so the measurement covers
the whole brief rather than whatever happened to be in the news.

That claim used to be false. The fixture carried eight content keys and the
browser check had therefore never measured the dark Regional Pressure Watch
panel, the poll table, the government cards, the analysis block, Business &
Economy or Indo-Pacific Partners — roughly two thirds of the brief, including
every section that sits on a coloured ground. It now carries all of them, so a
contrast or overflow regression in any section is caught rather than merely
assumed absent.

    python3 preview.py && BRIEF_HTML=preview.html python3 test_render_visual.py
"""
import pathlib
import render

DIGEST = {'academic_today': [{'authors': 'Nakamura, Ellis',
                              'journal_tier': 'A+',
                              'source': 'International Security',
                              'summary': 'The authors argue alliance credibility rests '
                                         'on basing access rather than on declaratory '
                                         'commitments, and test the claim against four '
                                         'East Asian cases.',
                              'title': 'Basing Access and the Credibility of Extended '
                                       'Deterrence in East Asia',
                              'url': 'https://example.org/21'}],
 'also_today': [{'body_text': 'METI names recipients.',
                 'category': 'trade',
                 'headline': 'Chip subsidy tranche released',
                 'source': 'Nikkei',
                 'url': 'https://example.org/6'},
                {'body_text': 'Budget testimony next week.',
                 'category': 'politics',
                 'headline': 'Diet committee sets hearing date',
                 'source': 'NHK World',
                 'url': 'https://example.org/7'}],
 'business_economy': [{'body_text': 'The trading house booked a *12 percent* rise in '
                                    'first-half operating profit on resource prices.',
                       'companies': ['Mitsui'],
                       'headline': 'Mitsui lifts full-year guidance',
                       'sector': 'macro',
                       'source': 'Nikkei Asia',
                       'url': 'https://example.org/12'},
                      {'body_text': 'Disbursement rules for the **$550bn** framework '
                                    'go to the Diet this session.',
                       'companies': [],
                       'headline': 'Investment framework governance bill drafted',
                       'sector': 'macro',
                       'source': 'Reuters',
                       'url': 'https://example.org/13'}],
 'calendar_watch': [{'confirmed': True,
                     'date': '2026-09-12',
                     'day': 12,
                     'detail': 'First since the pact.',
                     'event': 'PIF leaders meet',
                     'headline': 'PIF leaders meet',
                     'month': 'Sep',
                     'why_it_matters': 'First since the pact.'}],
 'events_today': [{'event_date': 'Sep 18, 2026',
                   'format': 'Hybrid',
                   'host': 'CSIS Japan Chair',
                   'summary': 'A panel on host-nation support negotiations ahead of '
                              'the 2027 agreement expiry.',
                   'title': 'The Next Host-Nation Support Agreement',
                   'url': 'https://example.org/22'}],
 'indo_pacific': [{'body_text': 'Seoul and Tokyo agreed to resume the shuttle summit '
                                'format in November.',
                   'category': 'korea-japan',
                   'headline': 'Shuttle diplomacy resumes with Seoul',
                   'source': 'Yonhap',
                   'track': 'Korea-Japan',
                   'url': 'https://example.org/14'},
                  {'body_text': 'Canberra and Tokyo signed a logistics-sharing annex.',
                   'category': 'australia',
                   'headline': 'Australia signs logistics annex',
                   'source': 'The Australian',
                   'track': 'Australia',
                   'url': 'https://example.org/15'},
                  {'body_text': 'Manila requested additional coast-guard vessels under '
                                'the existing yen-loan facility.',
                   'category': 'southeast-asia',
                   'headline': 'Philippines seeks more patrol vessels',
                   'source': 'Nikkei Asia',
                   'track': 'Southeast Asia',
                   'url': 'https://example.org/16'}],
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
 'npc_politburo': [{'action': 'Budget committee sets supplementary bill timetable',
                    'body': 'House of Representatives',
                    'detail': 'The committee will take the *supplementary budget* on '
                              'Thursday, with a floor vote expected the following week.',
                    'url': 'https://example.org/10'},
                   {'action': 'LDP names Diet Affairs Committee chair',
                    'body': 'LDP',
                    'detail': 'The appointment lands a week before the reshuffle.',
                    'url': 'https://example.org/11'}],
 'on_this_day': [{'date': 'September 8, 1951',
                  'event': 'Japan signed the San Francisco Peace Treaty.',
                  'relevance': 'The security treaty signed the same day remains the '
                               'basis of the alliance.'}],
 'opeds_today': [{'authors': 'Sheila A. Smith',
                  'central_argument': 'Alliance management now turns on industrial '
                                      'capacity rather than on declaratory policy.',
                  'policy_so_what': 'Washington should treat co-production as the '
                                    'principal deterrence lever.',
                  'source': 'CSIS Japan Chair',
                  'summary': 'The piece traces co-production talks since 2024 and '
                             'argues that *magazine depth*, not posture, is the '
                             'binding constraint on allied deterrence.',
                  'title': 'The Alliance Runs on Factories Now',
                  'url': 'https://example.org/20'}],
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
 'personnel_changes': [{'action': 'appointed',
                        'detail': 'The post had been vacant since July.',
                        'name': 'Hayashi Motoko',
                        'position': 'Ambassador to Australia',
                        'predecessor': 'Suzuki Takeshi'}],
 'prc_government': [{'action': 'MOFA lodges protest over survey vessel activity',
                     'detail': 'The ministry said the vessel operated inside the *EEZ* '
                               'without consent and summoned the deputy chief of '
                               'mission.',
                     'ministry': 'Ministry of Foreign Affairs',
                     'ministry_jp': '外務省',
                     'official': 'Kihara Seiji, Foreign Minister',
                     'source_label': 'Kyodo',
                     'url': 'https://example.org/8'},
                    {'action': 'BOJ holds policy rate, signals October review',
                     'detail': 'The board voted 7-2 to hold, with two members '
                               'dissenting in favour of an immediate increase.',
                     'ministry': 'Bank of Japan',
                     'ministry_jp': '日本銀行',
                     'official': '',
                     'source_label': 'Reuters',
                     'url': 'https://example.org/9'}],
 'public_sentiment': {'approval_polls': [{'cabinet_approval': '48%',
                                          'cabinet_disapproval': '34%',
                                          'days_old': 4,
                                          'poll_date': 'Sep 5-7',
                                          'pollster': 'NHK'},
                                         {'cabinet_approval': '44%',
                                          'cabinet_disapproval': '39%',
                                          'days_old': 26,
                                          'poll_date': 'Aug 15-17',
                                          'pollster': 'Asahi'}],
                      'discourse_flag': 'Coalition strain over the supplementary budget '
                                        'is the dominant domestic thread this week.',
                      'party_support': [{'party': 'LDP', 'support_pct': '34%'},
                                        {'party': 'CDP', 'support_pct': '11%'},
                                        {'party': 'Ishin', 'support_pct': '7%'}]},
 're_line': 'Yen surges to 7-month high · BOJ rate hike imminent · Nagoya floods',
 'social_statements': [{'analyst_note': 'The remark is the first time the figure has '
                                        'been given publicly.',
                        'avatar_initials': 'KS',
                        'badge_class': 'sb-p',
                        'handle_context': 'Chief Cabinet Secretary',
                        'platform_date': 'Kyodo · Sep 9',
                        'quote_text': 'We have conveyed our position through diplomatic '
                                      'channels and expect a response this week.',
                        'url': 'https://example.org/17',
                        'who': 'Kimura Shunsuke'}],
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
 'us_japan_relations': [{'body_text': 'Negotiators opened the host-nation support round '
                                      'covering the period from April 2027.',
                         'category': 'host-nation-support',
                         'headline': 'Host-nation support talks open in Washington',
                         'source': 'Kyodo',
                         'track': 'Alliance',
                         'url': 'https://example.org/18'},
                        {'body_text': 'Commerce confirmed the *Section 232* auto rate '
                                      'is unchanged pending the annual review.',
                         'category': 'trade',
                         'headline': 'Commerce leaves auto tariff rate unchanged',
                         'source': 'Reuters',
                         'track': 'Trade',
                         'url': 'https://example.org/19'}],
 'web_url': 'https://andysaulim.github.io/Daily-Japan-Digest/index.html',
 'xinhua_delta': {'bottom_line': 'Economic-pressure measures are accumulating faster '
                                 'than maritime activity; watch the licensing regime.',
                  'china_signal': 'Beijing confirmed a sevenfold visa-fee increase for '
                                  'Japanese nationals, citing reciprocity.',
                  'dprk_signal': 'KCNA carried a statement naming Japan over the '
                                 'trilateral exercise.',
                  'key_quotes': [{'quote': 'Japan should reflect on its own history '
                                           'before commenting on regional security.',
                                  'source_article': 'China MOFA press briefing',
                                  'speaker': 'MOFA spokesperson'}],
                  'output_volume': 'Heavy — 51 items',
                  'pm_activity': 'The Prime Minister chaired the disaster-response '
                                 'meeting and took questions afterwards.',
                  'pm_appearance_today': True,
                  'pm_days_since_last_appearance': 0,
                  'russia_signal': 'Moscow restated its position on the Northern '
                                   'Territories at a ministry briefing.',
                  'senkaku_status': 'Two China Coast Guard vessels remain inside the '
                                    'contiguous zone, a 31st consecutive patrol day.',
                  'silence_today': False,
                  'watch_flag': True}}

if __name__ == "__main__":
    html = render.render_html(dict(DIGEST))
    pathlib.Path("preview.html").write_text(html, encoding="utf-8")
    print(f"preview.html written ({len(html):,} chars)")
