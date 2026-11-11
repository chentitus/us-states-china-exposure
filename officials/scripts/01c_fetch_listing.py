"""Executive-branch releases for further observed states, 2025-01-01 onward (window decided 2026-11-10).
Polite single-thread crawl (1 request/second, research User-Agent). Sites that refuse the crawler (HTTP 403) are
recorded as unavailable and not retried in other ways.
Sources per office:
  wp      : WordPress REST API (posts after START)
  sqsp    : Squarespace collection JSON (?format=json, paginated by offset)
  listing : paginated HTML listing -> post pages; year in the URL (if any) skips older posts without fetching them
Output: data/raw/{gov,lg,sos}_{STATE}.jsonl ; data/raw/fetch_status_{STATE}.json
Usage: python3.12 officials/scripts/01c_fetch_listing.py AL FL WA NY
"""
import html, json, re, sys, time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
START = "2025-01-01"
S = requests.Session(); S.headers.update({"User-Agent": "Mozilla/5.0 (academic research; state press release archive)"})
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
CONFIG = {
    "AL": [("governor", {"kind": "wp", "base": "https://governor.alabama.gov"}),
           ("lieutenant_governor", {"kind": "wp", "base": "https://ltgov.alabama.gov"}),
           ("secretary_of_state", {"kind": "listing", "list": "https://www.sos.alabama.gov/newsroom?page={p}",
                                   "link": r'href="((?:https://www\.sos\.alabama\.gov)?/newsroom/[^"?#]+)"', "base": "https://www.sos.alabama.gov"})],
    "FL": [("governor", {"kind": "listing", "list": "https://www.flgov.com/eog/news/press?page={p}",
                         "link": r'href="(/eog/news/press/(\d{4})/[^"?#]+)"', "base": "https://www.flgov.com"}),
           ("secretary_of_state", {"kind": "blocked", "note": "dos.fl.gov returns 403 to research crawler"})],
    "WA": [("governor", {"kind": "listing", "list": "https://governor.wa.gov/news/news-releases?page={p}",
                         "link": r'href="(/news/(\d{4})/[^"?#]+)"', "base": "https://governor.wa.gov"}),
           ("lieutenant_governor", {"kind": "sqsp", "base": "https://www.ltgov.wa.gov", "path": "/press-releases"}),
           ("secretary_of_state", {"kind": "blocked", "note": "sos.wa.gov returns 403 to research crawler"})],
    "NY": [("governor", {"kind": "listing", "list": "https://www.governor.ny.gov/news?page={p}",
                         "link": r'href="(/news/[^"?#]+)"', "base": "https://www.governor.ny.gov"}),
           ("lieutenant_governor", {"kind": "none", "note": "no separate site; LG statements are issued through the governor's newsroom"}),
           ("secretary_of_state", {"kind": "listing", "list": "https://dos.ny.gov/pressroom?page={p}",
                                   "link": r'href="(/news/[^"?#]+)"', "base": "https://dos.ny.gov"})],
    # batch 2 (2026-11-11)
    "NC": [("governor", {"kind": "listing", "list": "https://governor.nc.gov/news/press-releases?page={p}",
                         "link": r'href="(/news/press-releases/(\d{4})/[^"?#]+)"', "base": "https://governor.nc.gov"}),
           ("lieutenant_governor", {"kind": "listing", "list": "https://ltgov.nc.gov/news/press-releases?page={p}",
                                    "link": r'href="(/news/press-releases/(\d{4})/[^"?#]+)"', "base": "https://ltgov.nc.gov"}),
           ("secretary_of_state", {"kind": "none", "note": "releases are posted only as PDF files (not collected)"})],
    "KY": [("governor", {"kind": "blocked", "note": "governor.ky.gov / kentucky.gov return 403 to research crawler"}),
           ("lieutenant_governor", {"kind": "blocked", "note": "ltgovernor.ky.gov returns 403 to research crawler"}),
           ("secretary_of_state", {"kind": "none", "note": "no news listing found on sos.ky.gov"})],
    "AZ": [("governor", {"kind": "blocked", "note": "azgovernor.gov returns 403 to research crawler"}),
           ("lieutenant_governor", {"kind": "none", "note": "Arizona has no lieutenant governor"}),
           ("secretary_of_state", {"kind": "blocked", "note": "azsos.gov returns 403 to research crawler"})],
    "MI": [("governor", {"kind": "blocked", "note": "michigan.gov returns 403 to research crawler"}),
           ("lieutenant_governor", {"kind": "blocked", "note": "michigan.gov returns 403 to research crawler"}),
           ("secretary_of_state", {"kind": "blocked", "note": "michigan.gov returns 403 to research crawler"})],
    # batch 3/4 (2026-11-11): governors only
    "GA": [("governor", {"kind": "listing", "list": "https://gov.georgia.gov/press-releases?page={p}",
                         "link": r'href="(/press-releases/(\d{4})-[^"?#]+)"', "base": "https://gov.georgia.gov"})],
    "IL": [("governor", {"kind": "listing", "list": "https://gov-pritzker-newsroom.prezly.com/?page={p}",
                         "link": r'href="(/[a-z0-9-]{25,})"', "base": "https://gov-pritzker-newsroom.prezly.com", "start": 1})],
    # batch 5 (2026-11-11)
    "MS": [("governor", {"kind": "wp", "base": "https://governorreeves.ms.gov"})],
    # batch 6 (2026-11-11)
    "HI": [("governor", {"kind": "wp", "base": "https://governor.hawaii.gov"})],
    "UT": [("governor", {"kind": "wp", "base": "https://governor.utah.gov"})],
    "AR": [("governor", {"kind": "wp", "base": "https://governor.arkansas.gov", "ptype": "news_post"})],
    "DE": [("governor", {"kind": "wp", "base": "https://news.delaware.gov", "filter": r"\bGov(ernor|\.) (Matt )?Meyer\b"})],
}
OFFICE_FILE = {"governor": "gov", "lieutenant_governor": "lg", "secretary_of_state": "sos"}

def get(url):
    for i in range(3):
        try:
            time.sleep(1.0)
            r = S.get(url, timeout=60)
            return r
        except requests.RequestException:
            time.sleep(5 * (i + 1))
    return None

def strip(h):
    h = re.sub(r"<(script|style|nav|header|footer|form|noscript)[^>]*>.*?</\1>", " ", h, flags=re.S)
    h = re.sub(r"<br\s*/?>|</p>|</li>|</h\d>|</div>", "\n", h)
    h = html.unescape(re.sub(r"<[^>]+>", " ", h))
    return re.sub(r"[ \t\xa0]+", " ", re.sub(r"\n\s*\n+", "\n\n", h)).strip()

def page_date(h):
    for pat in [r'article:published_time"\s+content="(\d{4}-\d{2}-\d{2})', r'datetime="(\d{4}-\d{2}-\d{2})',
                r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})']:
        m = re.search(pat, h)
        if m:
            return m.group(1)
    m = re.search(r"(%s) (\d{1,2}), (\d{4})" % MONTHS, h)
    return time.strftime("%Y-%m-%d", time.strptime(m.group(0), "%B %d, %Y")) if m else ""

def body(h):
    for pat in [r"<article[^>]*>(.*?)</article>", r"<main[^>]*>(.*?)</main>", r"<body[^>]*>(.*?)</body>"]:
        m = re.search(pat, h, re.S)
        if m and len(strip(m.group(1))) > 200:
            return strip(m.group(1))
    return strip(h)

def title(h):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S) or re.search(r"<title>(.*?)</title>", h, re.S)
    return strip(m.group(1)) if m else ""

def wp(st, office, c):
    recs, p = [], 1
    while True:
        r = get(f"{c['base']}/wp-json/wp/v2/{c.get('ptype', 'posts')}?per_page=100&page={p}&after={START}T00:00:00&_fields=date,link,title,content")
        if r is None or r.status_code != 200 or not r.json():
            break
        recs += [{"state": st, "office": office, "date": x["date"][:10], "title": strip(x["title"]["rendered"]), "url": x["link"],
                  "text": strip(x["content"]["rendered"])} for x in r.json()]
        if p >= int(r.headers.get("X-WP-TotalPages", p)):
            break
        p += 1
    if c.get("filter"):   # multi-agency news sites: keep releases naming the governor
        recs = [x for x in recs if re.search(c["filter"], x["title"] + " " + x["text"][:600])]
    return recs, "ok"

def sqsp(st, office, c):
    recs, url = [], f"{c['base']}{c['path']}?format=json"
    while url:
        r = get(url)
        if r is None or r.status_code != 200:
            return recs, f"http {getattr(r, 'status_code', 'error')}"
        j = r.json()
        stop = False
        for it in j.get("items", []):
            d = time.strftime("%Y-%m-%d", time.gmtime(it.get("publishOn", 0) / 1000))
            if d < START:
                stop = True; break
            recs.append({"state": st, "office": office, "date": d, "title": strip(it.get("title", "")),
                         "url": c["base"] + it.get("fullUrl", ""), "text": strip(it.get("body", "") or "")})
        nxt = j.get("pagination", {}).get("nextPageUrl")
        url = None if stop or not nxt else c["base"] + nxt + "&format=json"
    return recs, "ok"

def listing(st, office, c):
    recs, seen, old_streak, p = [], set(), 0, c.get("start", 0)
    while old_streak < 15 and p < 400:
        r = get(c["list"].format(p=p))
        if r is None or r.status_code != 200:
            return recs, f"http {getattr(r, 'status_code', 'error')} at page {p}"
        links = [m if isinstance(m, tuple) else (m,) for m in re.findall(c["link"], r.text)]
        new = [(u, *rest) for u, *rest in links if u not in seen]
        if not new:
            break
        for u, *rest in new:
            seen.add(u)
            if rest and rest[0] and rest[0] < START[:4]:
                old_streak += 1; continue
            full = u if u.startswith("http") else c["base"] + u
            q = get(full)
            if q is None or q.status_code != 200:
                continue
            d = page_date(q.text)
            if d and d < START:
                old_streak += 1; continue
            old_streak = 0
            recs.append({"state": st, "office": office, "date": d, "title": title(q.text), "url": full, "text": body(q.text)})
        print(f"  {st} {office} page {p}: kept {len(recs)}", flush=True)
        p += 1
    return recs, "ok"

if __name__ == "__main__":
    for st in sys.argv[1:]:
        status = {}
        for office, c in CONFIG[st]:
            if c["kind"] in ("blocked", "none"):
                status[office] = {"status": c["kind"], "note": c["note"], "n": 0}; continue
            recs, s = {"wp": wp, "sqsp": sqsp, "listing": listing}[c["kind"]](st, office, c)
            recs = [r for r in recs if not r["date"] or r["date"] >= START]
            with (RAW / f"{OFFICE_FILE[office]}_{st}.jsonl").open("w") as f:
                for r in recs:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            status[office] = {"status": s, "n": len(recs), "undated": sum(not r["date"] for r in recs)}
            print(st, office, status[office], flush=True)
        json.dump(status, open(RAW / f"fetch_status_{st}.json", "w"), indent=1)
