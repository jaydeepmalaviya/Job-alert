"""
Daily Job Alert Agent
Scrapes career pages of Toronto & Halifax asset management / fund admin companies,
detects NEW postings since yesterday, and emails a formatted digest via Gmail.
"""

import os, json, re, hashlib, smtplib, time, logging
from datetime import datetime, date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# COMPANY LIST  (name, city, careers_url, ats_type)
# ats_type: "greenhouse" | "lever" | "workday" | "html"
# ──────────────────────────────────────────────────────────────────────────────
COMPANIES = [
    # ── TORONTO ───────────────────────────────────────────────────────────────
    # Bank-owned / Large
    ("RBC Global Asset Management",          "Toronto", "https://jobs.rbc.com/ca/en/search-results?keywords=asset+management",                    "html"),
    ("TD Asset Management",                  "Toronto", "https://jobs.td.com/en/search/#q=asset+management&orgIds=1466",                          "html"),
    ("BMO Global Asset Management",          "Toronto", "https://jobs.bmo.com/ca/en/search-results?keywords=asset+management",                    "html"),
    ("CIBC Asset Management",                "Toronto", "https://cibc.wd3.myworkdayjobs.com/CIBC/jobs",                                           "workday"),
    ("1832 Asset Management / Dynamic",      "Toronto", "https://jobs.scotiabank.com/search/?q=asset+management",                                  "html"),
    ("Manulife Investment Management",       "Toronto", "https://manulife.wd3.myworkdayjobs.com/MFCJOBS",                                          "workday"),
    ("Sun Life / SLC Management",            "Toronto", "https://sunlife.wd3.myworkdayjobs.com/Experienced-EN/jobs",                               "workday"),
    ("Canada Life Investment Management",    "Toronto", "https://www.canadalife.com/about-us/careers.html",                                        "html"),
    # Pension / Institutional
    ("CPP Investments",                      "Toronto", "https://boards.greenhouse.io/cppinvestments",                                             "greenhouse"),
    ("Ontario Teachers' Pension Plan",       "Toronto", "https://otpp.wd3.myworkdayjobs.com/OTPP_External/jobs",                                   "workday"),
    ("OMERS",                                "Toronto", "https://omers.wd3.myworkdayjobs.com/OMERS_External",                                      "workday"),
    ("HOOPP",                                "Toronto", "https://hoopp.wd3.myworkdayjobs.com/HOOPP_Careers",                                       "workday"),
    ("OPTrust",                              "Toronto", "https://optrust.wd3.myworkdayjobs.com/OPTrust",                                           "workday"),
    # Independent boutiques
    ("Brookfield Asset Management",          "Toronto", "https://brookfieldoam.wd5.myworkdayjobs.com/brookfield-careers",                          "workday"),
    ("CI Global Asset Management",           "Toronto", "https://boards.greenhouse.io/cifinancialgrouptalentacquisition",                           "greenhouse"),
    ("AGF Investments",                      "Toronto", "https://agf.wd3.myworkdayjobs.com/AGFCareers",                                            "workday"),
    ("Fidelity Canada",                      "Toronto", "https://fidelity.wd3.myworkdayjobs.com/FidelityCanadaExternal",                           "workday"),
    ("EdgePoint Wealth Management",          "Toronto", "https://www.edgepointwealth.com/en/about/careers",                                        "html"),
    ("Beutel Goodman & Company",             "Toronto", "https://www.beutelgoodman.com/about/careers/",                                            "html"),
    ("Fiera Capital Corporation",            "Toronto", "https://boards.greenhouse.io/fieracapital",                                               "greenhouse"),
    ("Guardian Capital Group",               "Toronto", "https://guardiancapital.wd3.myworkdayjobs.com/Guardian_Careers",                          "workday"),
    ("Caldwell Investment Management",       "Toronto", "https://www.caldwellinvestment.com/about/careers/",                                       "html"),
    ("Burgundy Asset Management",            "Toronto", "https://www.burgundyasset.com/about-us/careers/",                                         "html"),
    ("Invesco Canada",                       "Toronto", "https://invesco.wd1.myworkdayjobs.com/External/jobs",                                     "workday"),
    ("BlackRock Canada",                     "Toronto", "https://blackrock.wd1.myworkdayjobs.com/BlackRock/jobs",                                  "workday"),
    ("Brandes Investment Partners",          "Toronto", "https://www.brandes.com/careers",                                                         "html"),
    ("Capital Group Canada",                 "Toronto", "https://capitalgroup.wd1.myworkdayjobs.com/Capital_Group/jobs",                           "workday"),
    # Alternatives
    ("Onex Corporation",                     "Toronto", "https://boards.greenhouse.io/onex",                                                       "greenhouse"),
    ("Northleaf Capital Partners",           "Toronto", "https://boards.greenhouse.io/northleafcapital",                                           "greenhouse"),
    ("Slate Asset Management",               "Toronto", "https://jobs.lever.co/slateasset",                                                        "lever"),
    ("Sprott Asset Management",              "Toronto", "https://jobs.lever.co/sprott",                                                            "lever"),
    ("Ninepoint Partners",                   "Toronto", "https://www.ninepoint.ca/en/about-ninepoint/careers/",                                    "html"),
    ("Arrow Capital Management",             "Toronto", "https://www.arrow-capital.com/careers/",                                                  "html"),
    ("Purpose Investments",                  "Toronto", "https://jobs.lever.co/purposeinvestments",                                                "lever"),
    ("Fengate Asset Management",             "Toronto", "https://jobs.lever.co/fengate",                                                           "lever"),
    ("3iQ Corp",                             "Toronto", "https://jobs.lever.co/3iq",                                                               "lever"),
    ("RPIA (RP Investment Advisors)",        "Toronto", "https://rpia.ca/en/careers",                                                              "html"),
    ("Wealthsimple",                         "Toronto", "https://jobs.lever.co/wealthsimple",                                                      "lever"),
    ("Ewing Morris & Co.",                   "Toronto", "https://www.ewingmorris.com/careers",                                                     "html"),
    # Fund Admin
    ("SS&C Technologies",                    "Toronto", "https://www.ssctech.com/company/careers",                                                 "html"),
    ("State Street (Canada)",                "Toronto", "https://statestreet.wd1.myworkdayjobs.com/External/jobs",                                 "workday"),
    ("Northern Trust Canada",                "Toronto", "https://northerntrust.wd5.myworkdayjobs.com/Careers/jobs",                                "workday"),
    ("CIBC Mellon",                          "Toronto", "https://www.cibcmellon.com/en/careers.html",                                              "html"),
    ("Apex Fund Services",                   "Toronto", "https://boards.greenhouse.io/theapexgroup",                                               "greenhouse"),
    ("Alter Domus",                          "Toronto", "https://jobs.alterdomus.com",                                                              "html"),
    ("IQ-EQ",                               "Toronto", "https://boards.greenhouse.io/iqeq",                                                       "greenhouse"),
    ("MUFG Investor Services",               "Toronto", "https://mufginvestorservices.wd1.myworkdayjobs.com/MUFG_Investor_Services",               "workday"),
    ("Citco Fund Services",                  "Toronto", "https://citco.wd3.myworkdayjobs.com/CitcoCareers",                                        "workday"),
    ("Maples Group",                         "Toronto", "https://jobs.maples.com",                                                                 "html"),
    # ── HALIFAX ───────────────────────────────────────────────────────────────
    ("Citco Fund Services (Halifax)",        "Halifax", "https://citco.wd3.myworkdayjobs.com/CitcoCareers",                                        "workday"),
    ("SS&C Technologies (Halifax)",          "Halifax", "https://www.ssctech.com/company/careers",                                                 "html"),
    ("MUFG Investor Services (Halifax)",     "Halifax", "https://mufginvestorservices.wd1.myworkdayjobs.com/MUFG_Investor_Services",               "workday"),
    ("Butterfield Fund Services",            "Halifax", "https://www.butterfieldgroup.com/about-us/careers",                                       "html"),
    ("Maitland Group (Halifax)",             "Halifax", "https://maitlandgroup.com/careers/",                                                      "html"),
    ("NTT Data Canada",                      "Halifax", "https://www.nttdata.com/global/en/careers",                                               "html"),
    ("SEAMARK Asset Management",             "Halifax", "https://www.seamark.ca/about/careers/",                                                   "html"),
    ("EY Halifax",                           "Halifax", "https://eyglobal.yello.co/jobs?page=1",                                                   "html"),
    ("KPMG Halifax",                         "Halifax", "https://home.kpmg/ca/en/home/careers.html",                                               "html"),
    ("Deloitte Halifax",                     "Halifax", "https://apply.deloitte.com/careers/SearchJobs?3_116_3=4183",                              "html"),
    ("RBC Wealth Management (Halifax)",      "Halifax", "https://jobs.rbc.com/ca/en/search-results?keywords=halifax",                              "html"),
    ("TD Wealth (Halifax)",                  "Halifax", "https://jobs.td.com/en/search/#q=halifax&orgIds=1466",                                    "html"),
    ("Scotia Wealth (Halifax)",              "Halifax", "https://jobs.scotiabank.com/search/?q=halifax",                                           "html"),
    ("National Bank (Halifax)",              "Halifax", "https://jobs.nbc.ca/search/?q=halifax",                                                   "html"),
    ("Medavie Blue Cross",                   "Halifax", "https://www.medavie.ca/en/careers/",                                                      "html"),
    ("Marsh McLennan (Halifax)",             "Halifax", "https://marsh.wd1.myworkdayjobs.com/Marsh_Careers/jobs",                                  "workday"),
    ("Canaccord Genuity (Halifax)",          "Halifax", "https://boards.greenhouse.io/canaccordgenuity",                                           "greenhouse"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# ──────────────────────────────────────────────────────────────────────────────
# ATS SCRAPERS
# ──────────────────────────────────────────────────────────────────────────────

def job_id(title, url):
    raw = f"{title}|{url}".lower().strip()
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def scrape_greenhouse(url: str) -> list[dict]:
    """Public Greenhouse JSON API."""
    jobs = []
    try:
        # Extract board token from URL
        m = re.search(r'greenhouse\.io/([^/?\s]+)', url)
        if not m:
            return []
        token = m.group(1)
        api = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
        r = requests.get(api, headers=HEADERS, timeout=15)
        data = r.json()
        for j in data.get("jobs", []):
            jobs.append({
                "title": j.get("title", ""),
                "url":   j.get("absolute_url", url),
                "location": j.get("location", {}).get("name", ""),
            })
    except Exception as e:
        log.warning(f"Greenhouse error for {url}: {e}")
    return jobs


def scrape_lever(url: str) -> list[dict]:
    """Public Lever JSON API."""
    jobs = []
    try:
        m = re.search(r'lever\.co/([^/?\s]+)', url)
        if not m:
            return []
        token = m.group(1)
        api = f"https://api.lever.co/v0/postings/{token}?mode=json"
        r = requests.get(api, headers=HEADERS, timeout=15)
        data = r.json()
        for j in data:
            loc = j.get("categories", {}).get("location", "")
            jobs.append({
                "title":    j.get("text", ""),
                "url":      j.get("hostedUrl", url),
                "location": loc,
            })
    except Exception as e:
        log.warning(f"Lever error for {url}: {e}")
    return jobs


def scrape_workday(url: str) -> list[dict]:
    """Workday careers page – parse visible job titles via HTML."""
    jobs = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        # Workday renders jobs in <li> or <a> tags with data-automation-id
        for tag in soup.find_all(attrs={"data-automation-id": "jobTitle"}):
            title = tag.get_text(strip=True)
            parent = tag.find_parent("a") or tag.find_parent("li")
            href = ""
            if parent and parent.name == "a":
                href = parent.get("href", "")
            if href and not href.startswith("http"):
                base = re.match(r'(https?://[^/]+)', url)
                href = (base.group(1) if base else "") + href
            if title:
                jobs.append({"title": title, "url": href or url, "location": ""})
    except Exception as e:
        log.warning(f"Workday error for {url}: {e}")
    return jobs


def scrape_html(url: str) -> list[dict]:
    """Generic HTML scraper — finds likely job-title links."""
    jobs = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        # Look for anchors whose text looks like a job title
        job_keywords = re.compile(
            r'(analyst|manager|associate|director|officer|specialist|advisor|engineer|'
            r'developer|coordinator|consultant|accountant|portfolio|research|compliance|'
            r'operations|quantitative|risk|fixed.income|equity|fund|investment|admin)',
            re.I
        )
        seen = set()
        for a in soup.find_all("a", href=True):
            text = a.get_text(" ", strip=True)
            if len(text) < 5 or len(text) > 120:
                continue
            if not job_keywords.search(text):
                continue
            href = a["href"]
            if not href.startswith("http"):
                base = re.match(r'(https?://[^/]+)', url)
                href = (base.group(1) if base else "") + href
            key = text.lower()[:60]
            if key in seen:
                continue
            seen.add(key)
            jobs.append({"title": text, "url": href, "location": ""})
        # If nothing found via links, try common job-list containers
        if not jobs:
            for tag in soup.select("h3, h4, .job-title, .position-title, [class*='job'], [class*='position']"):
                text = tag.get_text(" ", strip=True)
                if job_keywords.search(text) and 5 < len(text) < 120:
                    jobs.append({"title": text, "url": url, "location": ""})
    except Exception as e:
        log.warning(f"HTML scrape error for {url}: {e}")
    return jobs


SCRAPERS = {
    "greenhouse": scrape_greenhouse,
    "lever":      scrape_lever,
    "workday":    scrape_workday,
    "html":       scrape_html,
}


# ──────────────────────────────────────────────────────────────────────────────
# SEEN-JOBS TRACKING
# ──────────────────────────────────────────────────────────────────────────────

SEEN_PATH = Path("data/seen_jobs.json")

def load_seen() -> dict:
    if SEEN_PATH.exists():
        with open(SEEN_PATH) as f:
            return json.load(f)
    return {}

def save_seen(seen: dict):
    SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SEEN_PATH, "w") as f:
        json.dump(seen, f, indent=2)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN SCRAPE LOOP
# ──────────────────────────────────────────────────────────────────────────────

def collect_new_jobs() -> tuple[list[dict], dict]:
    seen = load_seen()
    new_jobs = []

    for company, city, url, ats in COMPANIES:
        log.info(f"Scraping {company} ({ats}) …")
        try:
            raw_jobs = SCRAPERS[ats](url)
        except Exception as e:
            log.error(f"  Error: {e}")
            raw_jobs = []

        for j in raw_jobs:
            jid = job_id(j["title"], j["url"])
            if jid not in seen:
                seen[jid] = str(date.today())
                new_jobs.append({
                    "company":  company,
                    "city":     city,
                    "title":    j["title"],
                    "url":      j["url"],
                    "location": j.get("location", ""),
                    "found":    str(date.today()),
                })

        time.sleep(0.8)   # polite delay between requests

    save_seen(seen)
    return new_jobs, seen


# ──────────────────────────────────────────────────────────────────────────────
# EMAIL BUILDER
# ──────────────────────────────────────────────────────────────────────────────

def build_email(new_jobs: list[dict]) -> tuple[str, str]:
    today = datetime.now().strftime("%A, %B %d %Y")
    count = len(new_jobs)

    # Group by city → company
    by_city: dict[str, dict[str, list]] = {"Toronto": {}, "Halifax": {}}
    for j in new_jobs:
        city = j["city"]
        comp = j["company"]
        by_city.setdefault(city, {}).setdefault(comp, []).append(j)

    # ── HTML ──────────────────────────────────────────────────────────────────
    city_blocks = ""
    for city, companies in by_city.items():
        if not companies:
            continue
        job_rows = ""
        for company, jobs in sorted(companies.items()):
            for j in jobs:
                loc_badge = (f'<span style="background:#e8f0fe;color:#1a73e8;'
                             f'padding:2px 8px;border-radius:12px;font-size:11px;'
                             f'margin-left:8px;">{j["location"]}</span>'
                             if j["location"] else "")
                job_rows += f"""
                <tr>
                  <td style="padding:10px 16px;border-bottom:1px solid #f0f4f8;">
                    <div style="font-size:13px;color:#888;margin-bottom:2px;">🏢 {company}</div>
                    <div>
                      <a href="{j['url']}" style="color:#1a73e8;font-weight:600;font-size:14px;
                                                   text-decoration:none;">{j['title']}</a>
                      {loc_badge}
                    </div>
                  </td>
                </tr>"""

        city_color = "#1F3864" if city == "Toronto" else "#2E75B6"
        city_blocks += f"""
        <div style="margin-bottom:28px;">
          <div style="background:{city_color};color:#fff;padding:10px 18px;
                      border-radius:8px 8px 0 0;font-size:15px;font-weight:700;
                      letter-spacing:0.5px;">📍 {city}</div>
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="border:1px solid #dde3ec;border-top:none;
                        border-radius:0 0 8px 8px;background:#fff;">
            {job_rows}
          </table>
        </div>"""

    if not city_blocks:
        city_blocks = """<p style="color:#666;text-align:center;padding:32px;">
          No new job postings detected since yesterday. Check back tomorrow!
        </p>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f7fb;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f7fb;padding:32px 0;">
    <tr><td align="center">
      <table width="620" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:12px;
                    box-shadow:0 2px 12px rgba(0,0,0,0.08);overflow:hidden;">

        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#1F3864,#2E75B6);
                     padding:28px 32px;text-align:center;">
            <div style="font-size:22px;font-weight:700;color:#fff;
                        letter-spacing:0.5px;">📊 Daily Job Alert</div>
            <div style="color:#cfe2ff;font-size:13px;margin-top:6px;">{today}</div>
          </td>
        </tr>

        <!-- Summary bar -->
        <tr>
          <td style="background:#e8f0fe;padding:14px 32px;text-align:center;
                     color:#1a73e8;font-weight:600;font-size:14px;">
            {'🎉 ' + str(count) + ' new job posting' + ('s' if count != 1 else '') + ' found across Toronto & Halifax companies'
             if count else '😴 No new postings today — all quiet on the hiring front'}
          </td>
        </tr>

        <!-- Job listings -->
        <tr>
          <td style="padding:28px 32px;">
            {city_blocks}
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#f8fafc;padding:20px 32px;text-align:center;
                     border-top:1px solid #e8edf3;">
            <div style="font-size:11px;color:#999;">
              This digest is generated automatically each morning by your Job Alert Agent.<br>
              Monitoring <strong>{len(COMPANIES)} career pages</strong> across Toronto & Halifax
              asset management and fund administration companies.
            </div>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    # ── Plain text fallback ───────────────────────────────────────────────────
    plain = f"Daily Job Alert — {today}\n{'='*50}\n"
    plain += f"{count} new posting(s) found.\n\n"
    for city, companies in by_city.items():
        if companies:
            plain += f"\n── {city} ──\n"
            for comp, jobs in sorted(companies.items()):
                for j in jobs:
                    plain += f"  [{comp}] {j['title']}\n  {j['url']}\n\n"

    return html, plain


# ──────────────────────────────────────────────────────────────────────────────
# EMAIL SENDER
# ──────────────────────────────────────────────────────────────────────────────

def send_email(html: str, plain: str, new_count: int):
    sender    = os.environ["GMAIL_SENDER"]      # your Gmail address
    password  = os.environ["GMAIL_APP_PASSWORD"] # Gmail App Password (16 chars)
    recipient = os.environ["RECIPIENT_EMAIL"]   # where to deliver the digest

    today = datetime.now().strftime("%b %d, %Y")
    subject = (f"🆕 Job Alert: {new_count} new posting(s) — {today}"
               if new_count else f"📭 Job Alert: No new postings — {today}")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Job Alert Agent <{sender}>"
    msg["To"]      = recipient

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html,  "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())

    log.info(f"Email sent to {recipient} — subject: {subject}")


# ──────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("🔍 Starting daily job scan …")
    new_jobs, seen = collect_new_jobs()
    log.info(f"✅ Found {len(new_jobs)} new job(s). Building email …")

    html, plain = build_email(new_jobs)
    send_email(html, plain, len(new_jobs))
    log.info("🎉 Done!")
