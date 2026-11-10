"""For bills that survive the rule exclusions, fetch the latest bill text (LegiScan getBillText)
and keep keyword-in-context snippets for manual coding.
Output: data/raw/legiscan/texts/{bill_id}.txt, data/processed/bill_snippets.csv
"""
import base64, glob, html, io, json, re, time
from pathlib import Path
import pandas as pd, requests

ROOT = Path(__file__).resolve().parents[1]
P, LS = ROOT / "data" / "processed", ROOT / "data" / "raw" / "legiscan"
TX = LS / "texts"; TX.mkdir(exist_ok=True)
KEY = dict(l.strip().split("=", 1) for l in open(ROOT / ".env") if "=" in l)["LEGISCAN_API_KEY"]
KW = re.compile(r"China|Chinese|Beijing|Communist Party|Hong Kong|Taiwan|Taipei|foreign adversar|countr(y|ies) of concern|TikTok|Huawei|ByteDance", re.I)

def text_of(doc):
    raw = base64.b64decode(doc["doc"])
    if doc["mime"] == "application/pdf":
        from pypdf import PdfReader
        return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(raw)).pages)
    h = raw.decode("utf-8", "ignore")
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)))

B = pd.read_csv(P / "bills_rules.csv")
B = B[B.rule_excluded.isna()]
bill_files = {}
for f in glob.glob(str(LS / "*/*/*/bill/*.json")):
    b = json.load(open(f))["bill"]
    if b["bill_id"] in set(B.bill_id):
        bill_files[b["bill_id"]] = b
rows = []
for bid in B.bill_id:
    out = TX / f"{bid}.txt"
    if not out.exists():
        texts = bill_files[bid]["texts"]
        t = ""
        if texts:
            doc = requests.get("https://api.legiscan.com/", params={"key": KEY, "op": "getBillText", "id": texts[-1]["doc_id"]}, timeout=120).json()
            if doc.get("status") == "OK":
                t = text_of(doc["text"])
        out.write_text(t)
    t = out.read_text()
    snips = []
    for m in KW.finditer(t):
        s = t[max(0, m.start() - 160): m.end() + 160].replace("\n", " ")
        if not snips or m.start() > snips[-1][0] + 320:
            snips.append((m.start(), s))
        if len(snips) == 2:
            break
    rows.append({"bill_id": bid, "n_kw": len(KW.findall(t)), "text_len": len(t), "snippets": " || ".join(s for _, s in snips)})
pd.DataFrame(rows).to_csv(P / "bill_snippets.csv", index=False)
print(len(rows), "bills; empty texts:", sum(r["text_len"] == 0 for r in rows))
