"""Fetch lieutenant governor and secretary of state releases, 2020-01-01 onward, CA and TX.
CA LG : ltg.ca.gov sitemap (dated post URLs) -> post pages
CA SoS: sos.ca.gov yearly release index pages -> release pages
TX LG : ltgov.texas.gov WordPress REST API
TX SoS: sos.state.tx.us/about/newsreleases/{year}/index.shtml -> MMDDYY.shtml
Output: data/raw/{lg,sos}_{state}.jsonl
"""
import json, re, time, html
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
S = requests.Session(); S.headers.update({"User-Agent": "Mozilla/5.0 (academic research; state press release archive)"})
START, YEARS = "2020-01-01", range(2020, 2027)
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"

def get(url, tries=6):
    for i in range(tries):
        try:
            r = S.get(url, timeout=60)
            if r.status_code in (200, 400, 404):
                return r
        except requests.RequestException:
            pass
        time.sleep(2 * (i + 1))
    raise RuntimeError(url)

def strip(h):
    h = re.sub(r"<(script|style|nav|header|footer|form)[^>]*>.*?</\1>", " ", h, flags=re.S)
    h = re.sub(r"<br\s*/?>|</p>|</li>|</h\d>|</div>", "\n", h)
    h = html.unescape(re.sub(r"<[^>]+>", " ", h))
    return re.sub(r"[ \t\xa0]+", " ", re.sub(r"\n\s*\n+", "\n\n", h)).strip()

def body(h):
    for pat in [r'<div class="entry-content[^"]*"[^>]*>(.*?)<footer', r"<article[^>]*>(.*?)</article>",
                r"<main[^>]*>(.*?)</main>", r'id="content"[^>]*>(.*?)<div id="footer', r"<body[^>]*>(.*?)</body>"]:
        m = re.search(pat, h, re.S)
        if m and len(strip(m.group(1))) > 200:
            return strip(m.group(1))
    return strip(h)

def title(h):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S) or re.search(r"<title>(.*?)</title>", h, re.S)
    return strip(m.group(1)) if m else ""

def text_date(h):
    m = re.search(r"(%s) \d{1,2}, \d{4}" % MONTHS, h)
    return time.strftime("%Y-%m-%d", time.strptime(m.group(0), "%B %d, %Y")) if m else ""

def page(url, state, office, date=""):
    try:
        h = get(url, tries=3).text
    except RuntimeError:
        print("  skip", url, flush=True)
        return {"state": state, "office": office, "date": date, "title": "", "url": url, "text": "", "fetch_failed": True}
    return {"state": state, "office": office, "date": date or text_date(h), "title": title(h), "url": url, "text": body(h)}

def write(name, recs):
    recs = [r for r in recs if not r["date"] or r["date"] >= START]
    with (RAW / name).open("w") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(name, len(recs), "undated", sum(not r["date"] for r in recs), flush=True)

def ca_lg():
    sm = get("https://ltg.ca.gov/sitemap.xml").text
    urls = sorted(set(re.findall(r"<loc>(https://ltg.ca.gov/(20[2]\d)/(\d\d)/(\d\d)/[^<]+)</loc>", sm)))
    with ThreadPoolExecutor(4) as ex:
        write("lg_CA.jsonl", list(ex.map(lambda u: page(u[0], "CA", "lieutenant_governor", "%s-%s-%s" % u[1:]), urls)))

def ca_sos():
    urls = []
    for y in YEARS:
        idx = "https://www.sos.ca.gov/administration/news-releases-and-advisories/%d-news-releases-and-advisories/" % y
        h = get(idx).text
        urls += list(dict.fromkeys(re.findall(r'href="(https://www.sos.ca.gov/administration/news-releases-and-advisories/%d-news-releases-and-advisories/[^"#]+)"' % y, h)))
    with ThreadPoolExecutor(4) as ex:
        write("sos_CA.jsonl", list(ex.map(lambda u: page(u, "CA", "secretary_of_state"), urls)))

def tx_lg():
    recs, p = [], 1
    while True:
        r = get("https://www.ltgov.texas.gov/wp-json/wp/v2/posts?per_page=100&page=%d&after=%sT00:00:00&_fields=date,link,title,content" % (p, START))
        if r.status_code != 200 or not r.json():
            break
        recs += [{"state": "TX", "office": "lieutenant_governor", "date": it["date"][:10], "title": strip(it["title"]["rendered"]),
                  "url": it["link"], "text": strip(it["content"]["rendered"])} for it in r.json()]
        if p >= int(r.headers.get("X-WP-TotalPages", p)):
            break
        p += 1
    write("lg_TX.jsonl", recs)

def tx_sos():
    jobs = []
    for y in YEARS:
        base = "https://www.sos.state.tx.us/about/newsreleases/%d/" % y
        try:
            h = get(base + "index.shtml", tries=3).text
        except RuntimeError:
            print("  no index", y, flush=True); continue
        for f in dict.fromkeys(re.findall(r'href="(\d{6}[a-z]?\.shtml)"', h)):
            d = "20%s-%s-%s" % (f[4:6], f[0:2], f[2:4])
            jobs.append((base + f, d))
    with ThreadPoolExecutor(4) as ex:
        write("sos_TX.jsonl", list(ex.map(lambda j: page(j[0], "TX", "secretary_of_state", j[1]), jobs)))

if __name__ == "__main__":
    import sys
    todo = sys.argv[1:] or ["ca_lg", "ca_sos", "tx_lg", "tx_sos"]
    for fn in [globals()[n] for n in todo]:
        try:
            fn()
        except Exception as e:
            print(fn.__name__, "FAILED", e, flush=True)
