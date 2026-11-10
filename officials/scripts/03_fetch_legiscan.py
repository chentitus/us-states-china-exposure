"""LegiScan: (1) download session datasets (bills, sponsors, roll calls, people) for sessions
overlapping 2020-2026; (2) full-text search for China/Taiwan terms to find bills whose TEXT
(not only title) mentions them.
Output: data/raw/legiscan/{STATE}_{session_id}/...  and data/raw/legiscan/search_{STATE}.json
"""
import base64, io, json, os, sys, time, zipfile
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "legiscan"; OUT.mkdir(parents=True, exist_ok=True)
KEY = dict(l.strip().split("=", 1) for l in open(ROOT / ".env") if "=" in l)["LEGISCAN_API_KEY"]
API = "https://api.legiscan.com/"
TERMS = ['China', 'Chinese', 'Beijing', '"Communist Party"', '"Hong Kong"', 'Taiwan', 'Taipei',
         '"foreign adversary"', '"foreign adversaries"', '"country of concern"', 'TikTok', 'Huawei', 'ByteDance']

def call(**p):
    for i in range(5):
        try:
            r = requests.get(API, params={"key": KEY, **p}, timeout=120).json()
            if r.get("status") == "OK":
                return r
            print("ERR", p, r, flush=True)
        except Exception as e:
            print("retry", p.get("op"), e, flush=True)
        time.sleep(3 * (i + 1))
    raise RuntimeError(p)

def datasets(state):
    for d in call(op="getDatasetList", state=state)["datasetlist"]:
        if d["year_end"] < 2020:
            continue
        dest = OUT / f"{state}_{d['session_id']}"
        if dest.exists():
            continue
        z = call(op="getDataset", id=d["session_id"], access_key=d["access_key"])["dataset"]["zip"]
        zipfile.ZipFile(io.BytesIO(base64.b64decode(z))).extractall(dest)
        print(state, d["session_id"], d["session_name"], "saved", flush=True)

def search(state):
    hits = {}
    for y in range(2019, 2027):
        for t in TERMS:
            page = 1
            while True:
                r = call(op="getSearchRaw", state=state, query=t, year=y, page=page)["searchresult"]
                for x in r.get("results", []):
                    hits.setdefault(x["bill_id"], {"bill_id": x["bill_id"], "terms": set()})["terms"].add(t)
                s = r["summary"]
                if int(s["page_current"]) >= int(s["page_total"]):
                    break
                page += 1
    rec = [{"bill_id": k, "terms": sorted(v["terms"])} for k, v in hits.items()]
    json.dump(rec, open(OUT / f"search_{state}.json", "w"), indent=0)
    print(state, "search hits", len(rec), flush=True)

if __name__ == "__main__":
    for st in sys.argv[1:] or ["CA", "TX"]:
        datasets(st); search(st)
