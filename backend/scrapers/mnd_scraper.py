import re
import json
import httpx
from datetime import datetime, date
from bs4 import BeautifulSoup

def parse_mnd_report(html: str) -> dict:
    """Parse MND daily report HTML and extract military activity data."""
    result = {
        "aircraft_count": 0,
        "vessel_count": 0,
        "centerline_crossings": 0,
        "aircraft_types": {},
        "circumnavigation": False,
        "night_activity": False,
    }

    if not html.strip():
        return result

    aircraft_match = re.search(r"共機(\d+)架次", html)
    vessel_match = re.search(r"共艦(\d+)艘", html)
    centerline_match = re.search(r"逾越.*?中線.*?(\d+)架次", html)

    if aircraft_match:
        result["aircraft_count"] = int(aircraft_match.group(1))
    if vessel_match:
        result["vessel_count"] = int(vessel_match.group(1))
    if centerline_match:
        result["centerline_crossings"] = int(centerline_match.group(1))

    type_pattern = re.compile(r"([\u4e00-\u9fff\w\-]+(?:戰機|預警機|反潛機|電偵機|轟炸機|運輸機|直升機|無人機))(\d+)架次")
    for match in type_pattern.finditer(html):
        result["aircraft_types"][match.group(1).replace("戰機", "").replace("預警機", "").replace("反潛機", "").strip()] = int(match.group(2))

    if "環繞" in html or "繞台" in html:
        result["circumnavigation"] = True
    if "夜間" in html:
        result["night_activity"] = True

    return result


async def fetch_mnd_report(target_date: date = None) -> dict:
    """Fetch the latest MND daily report from mnd.gov.tw."""
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(
                "https://www.mnd.gov.tw/news/plaactlist",
                follow_redirects=True,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            links = soup.select("a[href*='plaact/']")
            if not links:
                return None
            href = links[0]["href"]
            if href.startswith("http"):
                detail_url = href
            else:
                detail_url = "https://www.mnd.gov.tw/" + href.lstrip("/")
            detail_resp = await client.get(detail_url, follow_redirects=True)
            detail_resp.raise_for_status()
            report = parse_mnd_report(detail_resp.text)
            report["raw_html"] = detail_resp.text
            report["date"] = target_date or date.today()
            return report
        except Exception as e:
            print(f"MND scraper error: {e}")
            return None


def save_mnd_report(conn, report: dict) -> None:
    """Save parsed MND report to database."""
    conn.execute(
        """INSERT OR REPLACE INTO mnd_reports
           (date, aircraft_count, vessel_count, centerline_crossings,
            aircraft_types, circumnavigation, night_activity, raw_html)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            str(report["date"]),
            report["aircraft_count"],
            report["vessel_count"],
            report["centerline_crossings"],
            json.dumps(report["aircraft_types"], ensure_ascii=False),
            report.get("circumnavigation", False),
            report.get("night_activity", False),
            report.get("raw_html", ""),
        ),
    )
    conn.commit()
