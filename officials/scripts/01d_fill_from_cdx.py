"""Fill gaps where an official listing no longer pages back to 2025 (FL governor: listing reaches only Dec 2025).
URL list from the Internet Archive CDX index (data/raw/cdx_flgov_press_2025.txt, built with
  web.archive.org/cdx/search/cdx?url=flgov.com/eog/news/press/2025/*&collapse=urlkey&filter=statuscode:200);
each page is then fetched from the official site itself (1 request/second). CDX coverage may be incomplete.
Also repairs dates for all 01c outputs: the printed release date ("Month D YYYY" near the top) replaces a missing
or implausible (future) page date; duplicate URLs are dropped; trailing translation-download blocks are removed.
"""
import json, re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import importlib
c = importlib.import_module("01c_fetch_listing")
RAW = c.RAW
TODAY = time.strftime("%Y-%m-%d")
M = c.MONTHS

def text_date(r):
    m = re.search(rf"({M})\s+(\d{{1,2}}),?\s+(\d{{4}})", r["title"] + " " + r["text"][:800])
    return time.strftime("%Y-%m-%d", time.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%B %d %Y")) if m else ""

p = RAW / "gov_FL.jsonl"
have = {json.loads(l)["url"] for l in p.open()}
new = []
for u in [l.strip() for l in open(RAW / "cdx_flgov_press_2025.txt") if l.strip()]:
    if u in have:
        continue
    q = c.get(u)
    if q is None or q.status_code != 200:
        continue
    new.append({"state": "FL", "office": "governor", "date": "", "title": c.title(q.text), "url": u, "text": c.body(q.text)})
with p.open("a") as f:
    for r in new:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("FL governor added from CDX list:", len(new))

for f in sorted(RAW.glob("*_*.jsonl")):
    if f.stem.split("_")[1] in ("CA", "TX"):
        continue
    R, seen, out, fixed = [json.loads(l) for l in f.open()], set(), [], 0
    for r in R:
        if r["url"] in seen:
            continue
        seen.add(r["url"])
        if not r["date"] or r["date"] > TODAY:
            d = text_date(r)
            if d:
                r["date"], fixed = d, fixed + 1
        # NY governor pages end with a "Translations" download block (Arabic, Bengali, Chinese, ...): drop it
        r["text"] = re.sub(r"\n\s*Translations\s*\n.*$", "", r["text"], flags=re.S)
        if sum(ch == "\ufffd" for ch in r["text"][:2000]) >= 20:   # binary capture (PDF/image) decoded as text
            continue
        out.append(r)
    out = [r for r in out if not r["date"] or r["date"] >= c.START]
    # MN archived captures are mostly the script-rendered listing page, not the release itself: drop them
    out = [r for r in out if not (f.stem == "gov_MN" and "On this page you will find the latest press releases" in r["text"][:400])]
    f.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out))
    print(f.name, len(out), "dates repaired", fixed, "undated", sum(not r["date"] for r in out))
