# -*- coding: utf-8 -*-
"""
Asmary Field Services — SHANA Tender Scraper Module
"""
import re
import time
import urllib3
import requests
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://www.shana.ir/page/shana/module/tenderSearch.xhtml?a=0&alltp=true&allpl=true&allsr=true&pageSize=20&allty=true&pi={page}"

CAPABILITIES = {
    "PDC Bits & Milling": [
        r"pdc\s*bit", r"مته\s*(?:های\s*)?(?:حفاری|pdc|پی\s*دی\s*سی)",
        r"whipstock", r"ویپ\s*است[ا|ک]ک", r"ساید\s*ترک", r"window\s*milling",
        r"میلینگ", r"فرزکاری\s*پنجره", r"casing\s*scraper", r"اسکریپر", r"لوله\s*تراش"
    ],
    "Plugs & Packers": [
        r"bridge\s*plug", r"بریج\s*پلاگ", r"پلاگ\s*درون\s*چاهی",
        r"مسدود\s*کننده", r"thru[\s-]tubing", r"پکر\s*درون\s*چاهی",
        r"مجرابند", r"پلاگ\s*قابل\s*حفاری"
    ],
    "Pipe Recovery (FPIT & Back-Off)": [
        r"pipe\s*recovery", r"مانده\s*یابی", r"بازیابی\s*لوله",
        r"fpit", r"نقطه\s*گیر", r"نقطه\s*رهایی", r"free\s*point",
        r"back[\s-]*off", r"بک\s*آف", r"برش\s*شیمیایی\s*لوله", r"برش\s*مکانیکی"
    ],
    "Perforation": [
        r"perforat", r"مشبک\s*کاری", r"گان\s*مشبک", r"تفنگ\s*مشبک", r"چاشنی\s*انفجاری\s*چاه"
    ],
    "Well Integrity & Casing Inspection": [
        r"well\s*integrity", r"یکپارچگی\s*چاه", r"بازرسی\s*(?:لوله\s*)?جدار",
        r"emds", r"عیب\s*یابی\s*الکترومغناطیس", r"mfc", r"چند\s*انگشتی",
        r"multi[\s-]finger", r"mtt", r"ضخامت\s*سنجی\s*مغناطیس",
        r"spectral\s*noise", r"snl", r"نویز\s*طیفی", r"نشت\s*یابی\s*صوتی"
    ],
    "Well Logging (Open & Cased Hole)": [
        r"open[\s-]hole", r"حفره\s*باز", r"چاه\s*پیمایی", r"نمودار\s*گیری",
        r"نمودارگیری\s*کابل", r"log", r"لاگینگ", r"xmac", r"صوتی\s*دوقطبی",
        r"dipole\s*sonic", r"xrmi", r"cbil", r"تصویر\s*برداری\s*چاه",
        r"production\s*logging", r"plt", r"جریان\s*سنجی\s*درون\s*چاهی",
        r"4[\s-]arm\s*caliper", r"کالیپر\s*۴\s*بازو", r"انحراف\s*سنجی\s*چاه",
        r"cbl[\s/-]*vdl", r"کیفیت\s*سیمان", r"ارزیابی\s*سیمان"
    ],
    "Surface Testing & MPFM": [
        r"mpfm", r"جریان\s*سنج\s*چند\s*فازی", r"تفکیک\s*گر\s*سیار",
        r"multiphase\s*flow", r"آزمایش\s*سرچاهی", r"scale\s*prevention",
        r"کنترل\s*رسوب", r"رسوب\s*زدایی", r"توری\s*شنی", r"sand\s*screen"
    ],
    "Core & PVT Laboratory": [
        r"core\s*analysis", r"آنالیز\s*مغزه", r"مغزه\s*گیری",
        r"rcal", r"scal", r"خواص\s*سنگ\s*مخزن", r"تخلخل\s*و\s*نفوذ\s*پذیری",
        r"pvt", r"نمونه\s*گیری\s*سیال", r"سیال\s*مخزن", r"آسفالتین", r"فشار\s*اشباع"
    ]
}

COMPILED_CAPABILITIES = {
    cat: re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE)
    for cat, patterns in CAPABILITIES.items()
}

EXCLUDE_RE = re.compile(
    r"(?i)("
    r"خودرو(?:های)?\s*استیجاری|اجاره\s*خودرو|پیمان\s*حمل\s*و\s*نقل|"
    r"آشپزخانه|غذای\s*پرسنل|طبخ|پذیرایی|رستوران|"
    r"حراست|نگهبانی|انتظامات|"
    r"فضای\s*سبز|باغبانی|نظافت|آبدارخانه|"
    r"عایق\s*کاری\s*پشت\s*بام|ساختمان\s*اداری|بازسازی\s*مسجد|رنگ\s*آمیزی\s*جداول|"
    r"تاسیسات\s*حرارتی\s*ساختمان|مبلمان|خرید\s*کاغذ|لوازم\s*التحریر"
    r")",
    re.IGNORECASE
)

CLIENT_PATTERNS = [
    (r"(شرکت\s*ملی\s*حفاری\s*(?:ایران)?|nidc)", "شرکت ملی حفاری ایران (NIDC)"),
    (r"(مناطق\s*نفت[\s-]*خیز\s*جنوب|nisoc)", "شرکت ملی مناطق نفت‌خیز جنوب (NISOC)"),
    (r"(نفت\s*فلات\s*قاره\s*(?:ایران)?|iooc)", "شرکت نفت فلات قاره ایران (IOOC)"),
    (r"(مهندسی\s*و\s*توسعه\s*نفت|متن|pedec)", "شرکت متن (PEDEC)"),
    (r"(نفت\s*مناطق\s*مرکزی\s*(?:ایران)?|icofc)", "شرکت نفت مناطق مرکزی ایران (ICOFC)"),
    (r"(نفت\s*و\s*گاز\s*اروندان|aogc)", "شرکت نفت و گاز اروندان (AOGC)"),
    (r"(نفت\s*و\s*گاز\s*پارس|pogc)", "شرکت نفت و گاز پارس (POGC)"),
    (r"(شرکت\s*ملی\s*نفت\s*ایران|nioc)", "شرکت ملی نفت ایران (NIOC)"),
    (r"(پالایش\s*نفت\s*آبادان)", "شرکت پالایش نفت آبادان"),
    (r"(پالایش\s*نفت\s*اصفهان)", "شرکت پالایش نفت اصفهان"),
    (r"(پالایش\s*نفت\s*تهران)", "شرکت پالایش نفت تهران"),
]

def normalize_persian_text(text: str) -> str:
    if not text:
        return ""
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    for i in range(10):
        text = text.replace(persian_digits[i], str(i))
        text = text.replace(arabic_digits[i], str(i))
    text = text.replace("ي", "ی").replace("ك", "ک").replace("‌", " ")
    return " ".join(text.split())

def detect_client(full_text: str) -> str:
    for pattern, client_name in CLIENT_PATTERNS:
        if re.search(pattern, full_text, re.IGNORECASE):
            return client_name
    return "وزارت نفت / شرکت‌های تابعه"

def fetch_shana_page(session: requests.Session, page_num: int) -> str:
    url = BASE_URL.format(page=page_num)
    try:
        resp = session.get(url, timeout=25, verify=False)
        if resp.status_code == 200:
            return resp.text
        return ""
    except Exception:
        return ""

def parse_tenders_from_html(html_content: str) -> list:
    if not html_content:
        return []
    soup = BeautifulSoup(html_content, "html.parser")
    parsed_items = []

    blocks = soup.find_all(["li", "div", "tr"], class_=re.compile(r"tender|item|result|news-item|list-item", re.I))
    if len(blocks) < 3:
        blocks = soup.find_all("tr")

    for block in blocks:
        text = normalize_persian_text(block.get_text(separator=" ", strip=True))
        if len(text) < 30:
            continue

        link_tag = block.find("a", href=True)
        link = ""
        title = ""
        if link_tag:
            link = link_tag["href"]
            if not link.startswith("http"):
                link = f"https://www.shana.ir{link}"
            title = normalize_persian_text(link_tag.get_text(strip=True))

        if not title or len(title) < 15:
            title = text[:140] + "..."

        date_match = re.search(
            r"(\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}\s+(?:فروردین|اردیبهشت|خرداد|تیر|مرداد|شهریور|مهر|آبان|آذر|دی|بهمن|اسفند)\s+\d{4})",
            text
        )
        published_date = date_match.group(0) if date_match else "درج نشده"

        tender_id_match = re.search(r"(?:شماره\s*)?([م|الف][\s/]*[م|الف][\s/]*\d+[\s/]*\d+|\d{6,12})", text)
        tender_id = tender_id_match.group(0) if tender_id_match else "درج نشده"

        parsed_items.append({
            "title": title,
            "full_text": text,
            "date": published_date,
            "tender_id": tender_id,
            "link": link or "https://www.shana.ir/page/shana/module/tenderSearch.xhtml",
            "client": detect_client(text)
        })

    unique_items = []
    seen = set()
    for item in parsed_items:
        identifier = (item["title"], item["date"])
        if identifier not in seen:
            seen.add(identifier)
            unique_items.append(item)
    return unique_items

def run_scraper(pages_to_scan=50, progress_callback=None):
    """
    Scrapes the specified number of pages from SHANA,
    filtering for Asmary Field Services capabilities.
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'fa-IR,fa;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
    })

    all_tenders = []
    for page in range(1, pages_to_scan + 1):
        if progress_callback:
            progress_callback(page, pages_to_scan, len(all_tenders))
        
        html = fetch_shana_page(session, page)
        if not html:
            break
        items = parse_tenders_from_html(html)
        if not items:
            break
        all_tenders.extend(items)
        time.sleep(0.4)

    # Filtering
    matching_tenders = []
    seen_titles = set()

    for t in all_tenders:
        title = t["title"]
        full_text = t["full_text"]

        if title in seen_titles:
            continue
        seen_titles.add(title)

        if EXCLUDE_RE.search(full_text):
            continue

        matched_cats = []
        for cat, regex in COMPILED_CAPABILITIES.items():
            if regex.search(full_text):
                matched_cats.append(cat)

        if matched_cats:
            t["matched_services"] = matched_cats
            matching_tenders.append(t)

    return {
        "total_scanned_notices": len(all_tenders),
        "pages_scanned": pages_to_scan,
        "matched_count": len(matching_tenders),
        "tenders": matching_tenders
    }
