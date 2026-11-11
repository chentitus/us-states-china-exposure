"""Executive releases found through the Internet Archive CDX index (decided by the project owner 2026-11-11).
mode "archive": the archived copy is fetched from web.archive.org (site refuses the research crawler or is unreachable);
mode "auto"   : the release is fetched from the official site, falling back to the archived copy if that fails
                (site reachable but its listing pages are script-rendered).
For each office: CDX index (statuscode 200, captures from 2025 on) -> latest capture of each release URL ->
raw archived page (web/{timestamp}id_/{url}) -> same parsing as 01c; releases dated before 2025-01-01 are dropped.
Coverage depends on what the Archive captured and is incomplete.
Output: data/raw/{gov,lg,sos}_{STATE}.jsonl (source = "internet_archive"); data/raw/fetch_status_{STATE}.json updated
"""
import json, re, sys, time
from pathlib import Path
import requests
sys.path.insert(0, str(Path(__file__).parent))
import importlib
c = importlib.import_module("01c_fetch_listing")
RAW = c.RAW
ARCH = {
    "AZ": [("governor", [("azgovernor.gov/office-arizona-governor/news/2025/", "prefix", None),
                         ("azgovernor.gov/office-arizona-governor/news/2026/", "prefix", None)]),
           ("secretary_of_state", [("azsos.gov/news/", "prefix", None)])],
    "MI": [("governor", [("michigan.gov/whitmer/news/press-releases/2025/", "prefix", None),
                         ("michigan.gov/whitmer/news/press-releases/2026/", "prefix", None)]),
           ("secretary_of_state", [("michigan.gov/sos/resources/news/2025/", "prefix", None),
                                   ("michigan.gov/sos/resources/news/2026/", "prefix", None)])],
    "KY": [("governor", [("kentucky.gov/Pages/Activity-stream.aspx", "prefix", r"n=(GovernorBeshear|KentuckyGovernor)&")])],
    # batch 3/4 governors
    "VA": [("governor", [("governor.virginia.gov/newsroom/news-releases/2025/", "prefix", None),
                         ("governor.virginia.gov/newsroom/news-releases/2026/", "prefix", None)])],
    "IN": [("governor", [("in.gov/gov/newsroom/", "prefix", None),
                         # Indiana posts governor releases on the state events system; keep slugs naming the governor
                         ("events.in.gov/event/", "prefix", r"events\.in\.gov/event/[^?]*(braun|governor)")])],
    "MN": [("governor", [("mn.gov/governor/newsroom/press-releases/", "prefix", r"[?&]id=")])],
    "OR": [("governor", [("apps.oregon.gov/oregon-newsroom/OR/GOV/Posts/Post/", "prefix", None)])],
    "TN": [("governor", [("tn.gov/governor/news/2025/", "prefix", None), ("tn.gov/governor/news/2026/", "prefix", None)])],
    "LA": [("governor", [("gov.louisiana.gov/news/", "prefix", r"/news/\d+")])],
    "PA": [("governor", [("pa.gov/governor/newsroom/", "prefix", None)])],
    "IA": [("governor", [("governor.iowa.gov/press-release/", "prefix", None)])],
    # batch 5 governors
    "OH": [("governor", [("governor.ohio.gov/media/news-and-media/", "prefix", None)])],
    "SC": [("governor", [("governor.sc.gov/news/", "prefix", None)])],
    "MO": [("governor", [("governor.mo.gov/press-releases/", "prefix", None)])],
    "KS": [("governor", [("governor.kansas.gov/", "prefix", r"kansas\.gov/governor-")])],
    "CO": [("governor", [("governor.colorado.gov/press-release/", "prefix", None)])],
    "NV": [("governor", [("gov.nv.gov/Newsroom/PRs/", "prefix", None)])],
    "NJ": [("governor", [("nj.gov/governor/news/news/562025/", "prefix", None), ("nj.gov/governor/news/news/562026/", "prefix", None)])],
    "WI": [("governor", [("content.govdelivery.com/accounts/WIGOV/bulletins/", "prefix", None)])],
    "SD": [("governor", [("news.sd.gov/news", "prefix", r"sys_id=")])],   # all state agencies: keep governor items (FILTER)
    # batch 6 governors
    "AK": [("governor", [("gov.alaska.gov/", "prefix", r"gov\.alaska\.gov/[^?]*(dunleavy|governor|news|press)")])],
    "CT": [("governor", [("portal.ct.gov/governor/news/press-releases/2025/", "prefix", None), ("portal.ct.gov/governor/news/press-releases/2026/", "prefix", None)])],
    "ID": [("governor", [("gov.idaho.gov/pressrelease/", "prefix", None)])],
    "ME": [("governor", [("maine.gov/governor/mills/news/", "prefix", None)])],
    "MD": [("governor", [("governor.maryland.gov/news/press/", "prefix", None)])],
    "MA": [("governor", [("mass.gov/news/governor-healey", "prefix", None)])],
    "MT": [("governor", [("news.mt.gov/Governors-Office/", "prefix", None)])],
    "NE": [("governor", [("governor.nebraska.gov/", "prefix", r"governor\.nebraska\.gov/(press|news)/")])],
    "NH": [("governor", [("governor.nh.gov/news-and-media/", "prefix", None)])],
    "NM": [("governor", [("governor.state.nm.us/newsroom/", "prefix", None)])],
    "ND": [("governor", [("governor.nd.gov/news/", "prefix", None)])],
    "OK": [("governor", [("oklahoma.gov/governor/newsroom/newsroom/2025/", "prefix", None), ("oklahoma.gov/governor/newsroom/newsroom/2026/", "prefix", None)])],
    "RI": [("governor", [("governor.ri.gov/press-releases/", "prefix", None)])],
    "VT": [("governor", [("governor.vermont.gov/press-release/", "prefix", None)])],
    "WV": [("governor", [("governor.wv.gov/News/", "prefix", None)])],
    "WY": [("governor", [("governor.wyo.gov/", "prefix", r"governor\.wyo\.gov/[^?]*(news|press|release)")])],
}
# keep only releases issued by the governor's office where the source mixes agencies
FILTER = {"SD": r"\bGov\.|\bGovernor\b"}
MODE = {"AK": "archive", "MA": "archive", "NH": "archive", "RI": "archive", "ND": "archive",
        "CT": "auto", "ID": "auto", "ME": "auto", "MD": "auto", "MT": "auto", "NE": "auto", "NM": "auto", "OK": "auto",
        "VT": "auto", "WV": "auto", "WY": "auto",
        "OH": "archive", "SC": "archive", "MO": "archive", "KS": "archive", "CO": "archive",
        "NV": "auto", "NJ": "auto", "WI": "auto", "SD": "auto",
        "AZ": "archive", "MI": "archive", "KY": "archive", "IN": "archive", "MN": "archive",
        "VA": "auto", "OR": "auto", "TN": "auto", "LA": "auto", "PA": "auto", "IA": "auto"}

# States where only URLs first captured on/after 2025-01-01 are fetched (decided 2026-11-11: "只抓有明確2025年的文件").
# The earliest Archive capture of a URL is an upper bound on its publication date, so a first capture before 2025
# means the document is older; URLs without a 2025+ first capture are skipped without being fetched.
EARLIEST_2025 = {"WI", "SD", "SC", "MO", "KS", "CO", "AK", "ID", "ME", "MD", "MA", "MT", "NE", "NH", "NM", "ND", "RI", "VT", "WV", "WY"}

def cdx_first(url, match):
    """Earliest capture per URL (no date filter; collapse keeps the first capture of each urlkey)."""
    for i in range(6):
        try:
            time.sleep(5)
            r = requests.get("https://web.archive.org/cdx/search/cdx", params={"url": url, "matchType": match,
                             "output": "json", "fl": "timestamp,original", "filter": "statuscode:200",
                             "collapse": "urlkey", "limit": "100000"}, timeout=300)
            rows = r.json()
            return rows[1:] if rows else []
        except Exception:
            time.sleep(30 * (i + 1))
    return []

def cdx(url, match):
    for i in range(6):
        try:
            time.sleep(5)
            r = requests.get("https://web.archive.org/cdx/search/cdx", params={"url": url, "matchType": match, "from": "2025",
                             "output": "json", "fl": "timestamp,original", "filter": "statuscode:200", "limit": "50000"}, timeout=180)
            rows = r.json()
            return rows[1:] if rows else []
        except Exception:      # rate-limited: the Archive returns an HTML error page instead of JSON
            time.sleep(30 * (i + 1))
    return []

for st in sys.argv[1:]:
    stat_p = RAW / f"fetch_status_{st}.json"
    status = json.load(open(stat_p)) if stat_p.exists() else {}
    for office, specs in ARCH[st]:
        latest = {}
        for url, match, keep in specs:
            rows = cdx(url, match)
            if st in EARLIEST_2025:
                first = {re.sub(r"^https?://(www\.)?", "", o).replace(":80/", "/"): t for t, o in cdx_first(url, match)}
                rows = [(t, o) for t, o in rows if first.get(re.sub(r"^https?://(www\.)?", "", o).replace(":80/", "/"), "0") >= "20250101"]
            for ts, orig in rows:
                key = re.sub(r"^https?://(www\.)?", "", orig).replace(":80/", "/")
                if keep and not re.search(keep, key):
                    continue
                if key.endswith(".ics"):
                    continue
                key = re.sub(r"[#].*$", "", key) if keep else re.sub(r"[?#].*$", "", key)
                if key not in latest or ts > latest[key][0]:
                    latest[key] = (ts, orig)
        recs = []
        for key, (ts, orig) in sorted(latest.items()):
            r, src = None, "internet_archive"
            if MODE.get(st) == "auto":
                r = c.get("https://" + key if not orig.startswith("http") else orig.replace("http://", "https://"))
                src = "official"
            if r is None or r.status_code != 200:
                r, src = c.get(f"https://web.archive.org/web/{ts}id_/{orig}"), "internet_archive"
            if r is None or r.status_code != 200:
                continue
            h = r.text
            rec = {"state": st, "office": office, "date": c.page_date(h), "title": c.title(h), "url": "https://" + key,
                   "text": c.body(h), "source": src, "archived": ts}
            if not rec["date"] or rec["date"] > time.strftime("%Y-%m-%d"):
                m = re.search(rf"({c.MONTHS})\s+(\d{{1,2}}),?\s+(\d{{4}})", rec["title"] + " " + rec["text"][:800])
                rec["date"] = time.strftime("%Y-%m-%d", time.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%B %d %Y")) if m else ""
            if rec["date"] and rec["date"] < c.START:
                continue
            if st in FILTER and not re.search(FILTER[st], rec["title"] + " " + rec["text"][:600]):
                continue
            recs.append(rec)
        with (RAW / f"{c.OFFICE_FILE[office]}_{st}.jsonl").open("w") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        status[office] = {"status": "cdx_" + MODE.get(st, "archive"), "candidates": len(latest), "n": len(recs), "undated": sum(not r["date"] for r in recs)}
        print(st, office, status[office], flush=True)
    json.dump(status, open(stat_p, "w"), indent=1)
