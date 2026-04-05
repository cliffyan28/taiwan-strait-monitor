import pytest
from scrapers.mnd_scraper import parse_mnd_report

SAMPLE_MND_HTML = """
<div class="military_news">
  <p>偵獲共機33架次、共艦7艘次，其中逾越海峽中線及其延伸線進入北部、西南及東南空域14架次。</p>
  <p>空中：殲-16戰機4架次、殲-10戰機6架次、蘇愷-30戰機2架次、運-8反潛機1架次、空警-500預警機2架次、其他機型18架次。</p>
</div>
"""

def test_parse_mnd_report_extracts_counts():
    result = parse_mnd_report(SAMPLE_MND_HTML)
    assert result["aircraft_count"] == 33
    assert result["vessel_count"] == 7
    assert result["centerline_crossings"] == 14

def test_parse_mnd_report_extracts_aircraft_types():
    result = parse_mnd_report(SAMPLE_MND_HTML)
    types = result["aircraft_types"]
    assert types["殲-16"] == 4
    assert types["蘇愷-30"] == 2

def test_parse_mnd_report_empty_html():
    result = parse_mnd_report("")
    assert result["aircraft_count"] == 0
    assert result["vessel_count"] == 0
    assert result["centerline_crossings"] == 0
