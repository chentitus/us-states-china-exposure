"""Keyword filter: keep releases that mention China or Taiwan (title or text).
Input : data/raw/{gov,lg,sos}_*.jsonl
Output: data/processed/releases_all.csv            (all releases, with hit counts)
        data/processed/releases_china_taiwan.csv   (releases with >=1 hit)
        data/processed/keyword_counts_by_office_year.csv
"""
import json, re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CHINA = {
    "china": r"\bChina\b|\bPRC\b|People'?s Republic of China|\bBeijing\b",
    "chinese": r"\bChinese\b",
    "ccp": r"\bCCP\b|\bCPC\b|Chinese Communist Party|Communist Party of China|Communist China",
    "xi": r"\bXi Jinping\b|\bPresident Xi\b",
    "hong_kong": r"\bHong Kong\b",
    "provinces": r"\b(Guangdong|Jiangsu|Shanghai|Shenzhen|Zhejiang|Fujian|Sichuan|Hubei|Wuhan|Shandong|Hainan|Tianjin|Chongqing)\b",
    "firms_apps": r"\b(Huawei|ZTE|TikTok|ByteDance|WeChat|Tencent|Alibaba|DJI|CATL|BYD|Gotion|Hikvision|Temu|Shein|DeepSeek)\b",
    "adversary": r"foreign adversar(y|ies)|countr(y|ies) of concern",
}
TAIWAN = {
    "taiwan": r"\bTaiwan(ese)?\b|\bTaipei\b|\bROC\b|Republic of China \(Taiwan\)|\bTECO\b|\bTECRO\b",
    "taiwan_leaders": r"\bTsai Ing-?wen\b|\bLai Ching-?te\b|\bWilliam Lai\b|\bHsiao Bi-?khim\b",
}
PATS = {k: re.compile(v) for k, v in {**CHINA, **TAIWAN}.items()}

rows = []
for f in sorted((ROOT / "data" / "raw").glob("*_*.jsonl")):
    for line in open(f):
        r = json.loads(line)
        doc = (r.get("title") or "") + "\n" + (r.get("text") or "")
        for k, p in PATS.items():
            r["n_" + k] = len(p.findall(doc))
        rows.append(r)
df = pd.DataFrame(rows)
df["n_china_total"] = df[["n_" + k for k in CHINA]].sum(axis=1)
df["n_taiwan_total"] = df[["n_" + k for k in TAIWAN]].sum(axis=1)
df["year"] = df["date"].str[:4]
out = ROOT / "data" / "processed"
df.drop(columns=["text"]).to_csv(out / "releases_all.csv", index=False)
hit = df[(df.n_china_total > 0) | (df.n_taiwan_total > 0)].copy()
hit.to_csv(out / "releases_china_taiwan.csv", index=False)
g = df.groupby(["state", "office", "year"]).agg(
    releases=("url", "size"),
    china_any=("n_china_total", lambda s: (s > 0).sum()),
    taiwan_any=("n_taiwan_total", lambda s: (s > 0).sum())).reset_index()
g.to_csv(out / "keyword_counts_by_office_year.csv", index=False)
print(df.groupby(["state", "office"]).agg(releases=("url", "size"),
      china=("n_china_total", lambda s: (s > 0).sum()), taiwan=("n_taiwan_total", lambda s: (s > 0).sum())))
