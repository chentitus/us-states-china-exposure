"""Fetch governor press releases, 2020-01-01 onward, for CA and TX.
CA: WordPress REST API (all posts, full content).
TX: paginated list (8 posts per page, /news/P{offset}) + each post page.
Output: data/raw/gov_{state}.jsonl  (one record per release: state, office, date, title, url, text)
"""
import json, re, sys, time, html
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
UA = {"User-Agent": "Mozilla/5.0 (academic research; state press release archive)"}
START = "2020-01-01"
S = requests.Session(); S.headers.update(UA)

def get(url, tries=6):
    for i in range(tries):
        try:
            r = S.get(url, timeout=60)
            if r.status_code == 200:
                return r
            if r.status_code in (400, 404):
                return r
        except requests.RequestException:
            pass
        time.sleep(2 * (i + 1))
    raise RuntimeError(url)

def strip(h):
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S)
    h = re.sub(r"<br\s*/?>|</p>|</li>|</h\d>", "\n", h)
    h = re.sub(r"<[^>]+>", " ", h)
    h = html.unescape(h)
    return re.sub(r"[ \t\xa0]+", " ", re.sub(r"\n\s*\n+", "\n\n", h)).strip()

def fetch_ca():
    out = RAW / "gov_CA.jsonl"
    n = 0
    with out.open("w") as f:
        page = 1
        while True:
            r = get("https://www.gov.ca.gov/wp-json/wp/v2/posts?per_page=100&page=%d&after=%sT00:00:00"
                    "&_fields=id,date,link,title,content" % (page, START))
            if r.status_code != 200:
                break
            items = r.json()
            if not items:
                break
            for it in items:
                f.write(json.dumps({"state": "CA", "office": "governor", "date": it["date"][:10],
                                    "title": strip(it["title"]["rendered"]), "url": it["link"],
                                    "text": strip(it["content"]["rendered"])}, ensure_ascii=False) + "\n")
                n += 1
            tp = int(r.headers.get("X-WP-TotalPages", page))
            print("CA page", page, "/", tp, flush=True)
            if page >= tp:
                break
            page += 1
    print("CA done", n, flush=True)

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"

def tx_post(url):
    try:
        h = get(url).text
    except RuntimeError:
        print("  skip", url, flush=True)
        return {"state": "TX", "office": "governor", "date": "", "title": "", "url": url, "text": "", "fetch_failed": True}
    m = re.search(r'<p class="meta">\s*((?:%s) \d{1,2}, \d{4})' % MONTHS, h)
    date = time.strftime("%Y-%m-%d", time.strptime(m.group(1), "%B %d, %Y")) if m else ""
    t = re.search(r"<h1>(.*?)</h1>", h, re.S)
    body = re.search(r'<section aria-label="Content"[^>]*>(.*?)</section>', h, re.S)
    text = strip(body.group(1)) if body else ""
    text = re.sub(r"^.*?\|.*?\|[^\n]*\n", "", text, count=1)  # drop meta line
    return {"state": "TX", "office": "governor", "date": date,
            "title": strip(t.group(1)) if t else "", "url": url, "text": text}

def fetch_tx(start=0):
    """start > 0 resumes an interrupted crawl: keeps the existing file, skips URLs already saved."""
    out = RAW / "gov_TX.jsonl"
    seen, n, old = set(), 0, 0
    if start:
        seen = {json.loads(l)["url"] for l in out.open()}
    with out.open("a" if start else "w") as f, ThreadPoolExecutor(4) as ex:
        off = start
        while old < 24:
            h = get("https://gov.texas.gov/news/P%d" % off).text
            urls = [u for u in dict.fromkeys(re.findall(r'href="(https://gov.texas.gov/news/post/[^"]+)"', h)) if u not in seen]
            if not urls and off > 0:
                break
            seen.update(urls)
            for rec in ex.map(tx_post, urls):
                if rec["date"] and rec["date"] < START:
                    old += 1
                    continue
                f.write(json.dumps(rec, ensure_ascii=False) + "\n"); n += 1
            if off % 400 == 0:
                print("TX offset", off, "kept", n, "last", rec["date"], flush=True)
            off += 8
    print("TX done", n, flush=True)

if __name__ == "__main__":
    which = sys.argv[1:] or ["CA", "TX"]
    if "CA" in which: fetch_ca()
    if "TX" in which: fetch_tx()
    if "TX-resume" in which: fetch_tx(int(sys.argv[-1]))
