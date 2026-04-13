import csv
import json
import logging
import re
import sys
import time
from dataclasses import asdict, dataclass, fields
from typing import List, Optional, Tuple
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup, NavigableString, Tag

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scraper.log", mode="w", encoding="utf-8"),
    ],
)
log = logging.getLogger("coventry_scraper")

ALLOWED_DOMAIN = "www.coventry.ac.uk"

COURSE_URLS: List[str] = [
    "https://www.coventry.ac.uk/course-structure/pg/ees/data-science-msc/",
    "https://www.coventry.ac.uk/course-structure/pg/ees/computer-science-msc/",
    "https://www.coventry.ac.uk/course-structure/pg/ees/data-science-and-computational-intelligence-msc/",
    "https://www.coventry.ac.uk/course-structure/pg/ees/engineering-management-msc/",
    "https://www.coventry.ac.uk/course-structure/pg/ees/artificial-intelligence-human-factors-msc/",
]

UNIVERSITY_NAME = "Coventry University"
CAMPUS = "Coventry University (Coventry)"
COUNTRY = "United Kingdom"
ADDRESS = "Priory Street, Coventry, CV1 5FB, United Kingdom"

OUTPUT_JSON = "coventry_courses.json"
OUTPUT_CSV = "coventry_courses.csv"

REQUEST_TIMEOUT = 25
REQUEST_DELAY = 2
MAX_RETRIES = 3
BACKOFF_FACTOR = 2

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

@dataclass
class CourseRecord:
    program_course_name: str = ""
    university_name: str = UNIVERSITY_NAME
    course_website_url: str = ""
    campus: str = CAMPUS
    country: str = COUNTRY
    address: str = ADDRESS
    study_level: str = "NA"
    course_duration: str = "NA"
    all_intakes_available: str = "NA"
    mandatory_documents_required: str = "NA"
    yearly_tuition_fee: str = "NA"
    scholarship_availability: str = "NA"
    gre_gmat_mandatory_min_score: str = "NA"
    min_ielts: str = "NA"
    kaplan_test_of_english: str = "NA"
    min_pte: str = "NA"
    min_toefl: str = "NA"
    min_duolingo: str = "NA"
    ug_academic_min_gpa: str = "NA"
    twelfth_pass_min_cgpa: str = "NA"
    class_12_boards_accepted: str = "NA"
    english_waiver_class12: str = "NA"
    english_waiver_moi: str = "NA"
    mandatory_work_exp: str = "NA"
    max_backlogs: str = "NA"
    gap_year_max_accepted: str = "NA"
    indian_regional_institution_restrictions: str = "NA"

def _assert_official_url(url: str) -> None:
    netloc = urlparse(url).netloc.lower().lstrip("www.")
    allowed = ALLOWED_DOMAIN.lower().lstrip("www.")
    if netloc != allowed:
        raise ValueError(f"URL '{url}' is not on '{ALLOWED_DOMAIN}'")

def fetch_page(url: str) -> Optional[Tuple[BeautifulSoup, str]]:
    _assert_official_url(url)
    session = requests.Session()
    session.headers.update(HTTP_HEADERS)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.info(f"GET {url}  [{attempt}/{MAX_RETRIES}]")
            resp = session.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            resp.raise_for_status()
            final_url = resp.url
            encoding = resp.apparent_encoding or "utf-8"
            resp.encoding = encoding
            soup = BeautifulSoup(resp.text, "lxml")
            return soup, final_url
        except Exception:
            if attempt < MAX_RETRIES:
                wait = REQUEST_DELAY * (BACKOFF_FACTOR ** (attempt - 1))
                time.sleep(wait)
    return None

def _clean(text: Optional[str]) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()

def _page_text(soup: BeautifulSoup) -> str:
    return _clean(soup.get_text(" "))

def _section_after_heading(soup: BeautifulSoup, fragment: str, max_chars: int = 800) -> str:
    for heading in soup.find_all(re.compile(r"^h[1-6]$", re.I)):
        if fragment.lower() in heading.get_text().lower():
            parts = []
            for sib in heading.find_next_siblings():
                if isinstance(sib, Tag) and re.match(r"^h[1-6]$", sib.name or "", re.I):
                    break
                if isinstance(sib, (Tag, NavigableString)):
                    t = _clean(sib.get_text() if isinstance(sib, Tag) else str(sib))
                    if t:
                        parts.append(t)
            return _clean(" ".join(parts))[:max_chars]
    return ""

def _re(pattern: str, text: str, group: int = 1, flags: int = re.IGNORECASE) -> str:
    m = re.search(pattern, text, flags)
    return _clean(m.group(group)) if m else ""

def _re0(pattern: str, text: str, flags: int = re.IGNORECASE) -> str:
    return _re(pattern, text, group=0, flags=flags)

def _extract_course_name(soup: BeautifulSoup) -> str:
    h1 = soup.find("h1")
    if h1:
        name = _clean(h1.get_text())
        if name:
            return name
    title = soup.find("title")
    if title:
        return _clean(title.get_text()).split("|")[0].strip()
    return ""

def _extract_study_level(url: str, soup: BeautifulSoup) -> str:
    if "/pg/" in url:
        return "Postgraduate"
    if "/ug/" in url:
        return "Undergraduate"
    text = _page_text(soup)
    if re.search(r"\bpostgraduate\b", text, re.I):
        return "Postgraduate"
    if re.search(r"\bundergraduate\b", text, re.I):
        return "Undergraduate"
    return "NA"

def _extract_duration(soup: BeautifulSoup) -> str:
    for dt in soup.find_all("dt"):
        if "duration" in _clean(dt.get_text()).lower():
            dd = dt.find_next_sibling("dd")
            if dd:
                val = _clean(dd.get_text())
                if val:
                    return val
    text = _page_text(soup)
    v = _re(r"Duration\s*[:\-]\s*([^\n]{10,100})", text)
    if v:
        return v
    return "NA"

def _extract_intakes(soup: BeautifulSoup) -> str:
    text = _page_text(soup)
    m = re.search(r"Start\s+dates?\s*[:\-]?\s*((?:[A-Z][a-z]+\s+\d{4}[\s,/]*){1,10})", text, re.I)
    if m:
        dates = re.findall(r"[A-Z][a-z]+\s+\d{4}", m.group(1))
        if dates:
            return ", ".join(dates)
    return "NA"

def _extract_tuition_fee(soup: BeautifulSoup) -> str:
    text = _page_text(soup)
    v = _re(r"(£[\d,]{4,8})\s*per\s*year", text)
    if v:
        return f"{v} per year"
    return "NA"

def scrape_course(url: str) -> CourseRecord:
    rec = CourseRecord(course_website_url=url)
    result = fetch_page(url)
    if result is None:
        rec.program_course_name = "FETCH_ERROR"
        return rec
    soup, final_url = result
    rec.course_website_url = final_url
    rec.program_course_name = _extract_course_name(soup)
    rec.study_level = _extract_study_level(url, soup)
    rec.course_duration = _extract_duration(soup)
    rec.all_intakes_available = _extract_intakes(soup)
    rec.yearly_tuition_fee = _extract_tuition_fee(soup)
    return rec

def write_json(records: List[CourseRecord], path: str) -> None:
    data = [asdict(r) for r in records]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)

def write_csv(records: List[CourseRecord], path: str) -> None:
    if not records:
        return
    fieldnames = [f.name for f in fields(records[0])]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow(asdict(rec))

def run() -> List[CourseRecord]:
    results = []
    for url in COURSE_URLS:
        rec = scrape_course(url)
        results.append(rec)
        time.sleep(REQUEST_DELAY)
    write_json(results, OUTPUT_JSON)
    write_csv(results, OUTPUT_CSV)
    return results

if __name__ == "__main__":
    run()