"""Build the observed-states page dashboard/officials.html at the repository root (linked from the other US pages).
Embeds: state exposure scores (recomputed from data/clean/summary_state.csv with the
same percentile formulas as that project's 04_exposure.py), legislative indicators (09), coded bills (07),
coded releases (08), legislators (09), and Census 2024 cartographic boundaries (state 20m; CA/TX SLDU/SLDL 500k).
"""
import io, json, zipfile
from pathlib import Path
import pandas as pd, numpy as np, shapefile

ROOT = Path(__file__).resolve().parents[1]
P, GEO = ROOT / "data" / "processed", ROOT / "data" / "raw" / "geo"
EXPO = ROOT.parent / "data" / "clean" / "summary_state.csv"
FIPS = {"CA": "06", "TX": "48"}

def geojson(zf, idf, keep=lambda rec: True):
    z = zipfile.ZipFile(GEO / zf); base = [n for n in z.namelist() if n.endswith(".shp")][0][:-4]
    r = shapefile.Reader(shp=io.BytesIO(z.read(base + ".shp")), dbf=io.BytesIO(z.read(base + ".dbf")), shx=io.BytesIO(z.read(base + ".shx")))
    fields = [f[0] for f in r.fields[1:]]; feats = []
    def rnd(c):
        if isinstance(c[0], (float, int)):
            return [round(c[0], 3), round(c[1], 3)]
        out = [rnd(x) for x in c]
        if out and isinstance(out[0][0], float):  # drop repeated points after rounding
            out = [p for i, p in enumerate(out) if i == 0 or p != out[i - 1]]
        return out
    for sr in r.shapeRecords():
        rec = dict(zip(fields, sr.record))
        if not keep(rec):
            continue
        g = sr.shape.__geo_interface__
        feats.append({"type": "Feature", "id": rec[idf], "properties": {"name": rec.get("NAMELSAD") or rec.get("NAME")},
                      "geometry": {"type": g["type"], "coordinates": rnd(g["coordinates"])}})
    return {"type": "FeatureCollection", "features": feats}

geo = {"states": geojson("cb_2024_us_state_20m.zip", "STUSPS", lambda r: r["STUSPS"] not in ("PR",))}
# district maps: 2020 file = plans drawn in 2011 (used through the 2021-22 legislature);
# 2024 file = plans drawn after the 2020 census (first used in the 2023-24 legislature)
for st, fp in FIPS.items():
    for yr, era in (("2024", "new"),):  # window starts 2025 -> only the post-2020-census plans are needed
        geo[f"{st}_upper_{era}"] = geojson(f"cb_{yr}_{fp}_sldu_500k.zip", "SLDUST")
        geo[f"{st}_lower_{era}"] = geojson(f"cb_{yr}_{fp}_sldl_500k.zip", "SLDLST")

# state exposure (50 states + DC), same formulas as scripts/04_exposure.py
S = pd.read_csv(EXPO)
pct = lambda s: s.rank(pct=True)
S["s_export"] = pd.concat([pct(S.exp_china_pct_gdp_2025), pct(S.exp_china_share_2025)], axis=1).mean(axis=1)
S["s_vul"] = pd.concat([pct(S.exp_top1_hs4_share_2025), pct(S.exp_hhi_hs4_2025)], axis=1).mean(axis=1)
S["s_import"] = pd.concat([pct(S.imp_china_pct_gdp_2025), pct(S.imp_china_share_2025)], axis=1).mean(axis=1)
S["score"] = S[["s_export", "s_import", "s_vul"]].mean(axis=1)
expo = S[["state", "state_name_zh", "score", "s_export", "s_import", "s_vul", "exp_china_pct_gdp_2025",
          "exp_china_share_2025", "imp_china_pct_gdp_2025", "imp_china_share_2025"]].round(4)

pooled = pd.read_csv(P / "ind_state_pooled.csv")
yearly = pd.read_csv(P / "ind_state_yearly.csv")
B = pd.read_csv(P / "bills_coded.csv")
B = B[(B.code != "X") & (B.session.str[:4].astype(int) >= 2025)][["state", "bill_number", "bill_type", "title", "status", "first_action", "code", "url", "state_link", "n_sponsors"]]
R = pd.read_csv(P / "releases_coded.csv")
R = R[(R.code != "X") & (R.date >= "2025-01-01")][["state", "office", "date", "title", "url", "code"]]
def prep(L):
    L["chamber"] = L.role.map({"Sen": "upper", "Rep": "lower"})
    L["dist"] = L.district.str.split("-").str[1]
    return L.drop(columns=[c for c in L.columns if c.endswith("_primary") or c == "ballotpedia"]).replace({np.nan: None})
L = prep(pd.read_csv(P / "ind_legislator.csv"))
LB = prep(pd.read_csv(P / "ind_legislator_session.csv"))

SL = pd.read_csv(P / "sld_exposure_2025.csv", dtype={"district": str})
cols = [f"{m}_{pn}_{k}" for m in ("origin", "production", "hybrid") for pn in ("china", "taiwan") for k in ("usd_mn", "share", "per_worker")]
sld = {f"{r.state}_{r.chamber}_{r.district}": {c: (None if pd.isna(getattr(r, c)) else round(float(getattr(r, c)), 5)) for c in cols + ["emp_total"]}
       for r in SL.itertuples()}
# sponsorship by party (window: sessions starting 2025+), per state x party x code
#   bills_primary : distinct bills with >= 1 primary sponsor from the party
#   bills_any     : distinct bills with >= 1 primary or co-sponsor from the party
#   members       : party members serving in the 2025-26 legislature (LegiScan people, both chambers)
#   share_active  : share of those members who (co)sponsored >= 1 bill of that code
SP = pd.read_csv(P / "sponsors_china_taiwan.csv")
BC = pd.read_csv(P / "bills_coded.csv")[["bill_id", "state", "code", "session"]]
BC = BC[BC.code.isin(["R", "Rc", "C", "T"]) & (BC.session.str[:4].astype(int) >= 2025)]
SP = SP[(SP.committee_sponsor == 0) & SP.party.isin(["D", "R"])].merge(BC, on="bill_id")
LW = pd.read_csv(P / "ind_legislator_session.csv"); LW = LW[LW.party.isin(["D", "R"])]
spons = []
for st in sorted(LW.state.unique()):
    for pa in ["D", "R"]:
        mem = LW[(LW.state == st) & (LW.party == pa)].people_id.unique()
        for c in ["R", "Rc", "C", "T"]:
            x = SP[(SP.state == st) & (SP.party == pa) & (SP.code == c)]
            spons.append({"state": st, "party": pa, "code": c, "members": int(len(mem)),
                          "bills_primary": int(x[x.sponsor_type == "primary"].bill_id.nunique()),
                          "bills_any": int(x.bill_id.nunique()),
                          "share_active": round(float(x.people_id.isin(mem).groupby(x.people_id).any().sum()) / len(mem), 4) if len(mem) else None})
data = {"spons": spons, "sld": sld, "expo": expo.replace({np.nan: None}).to_dict("records"), "pooled": pooled.replace({np.nan: None}).to_dict("records"),
        "yearly": yearly.replace({np.nan: None}).to_dict("records"), "bills": B.replace({np.nan: None}).to_dict("records"),
        "releases": R.to_dict("records"), "legislators": L.to_dict("records"), "leg_session": LB.to_dict("records"), "geo": geo,
        "pending": "資料期間：2025 年 1 月起的行政部門新聞稿，以及 2025–26 會期的法案、決議與表決（含 2024 年底預先提出的法案）。"}
tpl = (ROOT / "scripts" / "page_template.html").read_text()
out = ROOT.parent / "dashboard" / "officials.html"   # published with the US dashboards (GitHub Pages)
out.write_text(tpl.replace("/*__DATA__*/", "const DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";"))
print(out, round(out.stat().st_size / 1e6, 1), "MB")
