"""State legislative district (SLDU/SLDL, 2024 plans) China/Taiwan export exposure for the observed states, 2025.
Three side-by-side measures (decided 2026-11-09), all ESTIMATES:
  (1) origin  : X_{s,i} x L_{d,i} / L_{s,i}     state exports by NAICS4 and partner (Census statenaics, Origin of
                                                Movement), split across the state's districts by employment share
  (2) production: X_{US,i} x L_{d,i} / L_{US,i}  national exports by NAICS4 and partner, split by the district's share
                                                of national employment in that industry
  (3) hybrid  : (2) for agriculture/forestry/fishing (NAICS 11) and mining (21); (1) for everything else
Employment L_{d,i}:
  non-farm : ZBP 2023 establishments by ZIP x NAICS4 x national employment per establishment (CBP 2023 US),
             ZCTA -> district by land-area share (Census rel2020 tab20_sld{u,l}202420_zcta520)
  farm (NAICS 111x/112x, absent from ZBP): BLS QCEW 2024 county private employment (CBP fill where suppressed),
             county -> district by land-area share (tab20_sld{u,l}202420_county20)
  L_{US,i} uses the same sources summed over the whole country, so (2) sums to the national total over all districts in the US.
Denominators reported side by side: China share of the district's exports to the world (same measure), and exports per
private-sector worker (district total employment from the same ZBP/QCEW build).
Inputs from the repository root (raw ZBP, CBP, QCEW; clean naics_national_trade.csv; .env CENSUS_API_KEY).
Output: data/processed/sld_exposure_2025.csv (one row per state x chamber x district), data/processed/sld_exposure_check.csv
"""
import io, json, zipfile, time
from pathlib import Path
import numpy as np, pandas as pd, requests

ROOT = Path(__file__).resolve().parents[1]
EX = ROOT.parent   # repository root (officials/ sits inside it)
P, REL = ROOT / "data" / "processed", ROOT / "data" / "raw" / "geo" / "rel"
YEAR, STATES = 2025, {"CA": "06", "TX": "48"}
PARTNERS = {"china": "5700", "taiwan": "5830", "world": "-"}
KEY = dict(l.strip().split("=", 1) for l in open(EX / ".env") if "=" in l)["CENSUS_API_KEY"]
is_farm = lambda n: n[:3] in ("111", "112")
is_ag_mining = lambda n: n[:2] in ("11", "21")

# ---------- trade ----------
nat = pd.read_csv(EX / "data/clean/naics_national_trade.csv", dtype={"naics4": str})
nat = nat[(nat.flow == "exports") & (nat.year == YEAR)].pivot_table(index="naics4", columns="partner", values="value_usd", aggfunc="sum").fillna(0)
cache = ROOT / "data" / "raw" / f"statenaics_exports_{YEAR}.json"
if cache.exists():
    st_rows = json.load(open(cache))
else:
    st_rows = []
    for st in STATES:
        for pn, cc in PARTNERS.items():
            for i in range(5):
                try:
                    r = requests.get("https://api.census.gov/data/timeseries/intltrade/exports/statenaics",
                                     params={"get": "NAICS,ALL_VAL_YR", "STATE": st, "CTY_CODE": cc, "COMM_LVL": "NA4",
                                             "time": f"{YEAR}-12", "key": KEY}, timeout=120).json()
                    break
                except Exception:
                    time.sleep(5 * (i + 1))
            st_rows += [{"state": st, "partner": pn, "naics4": x[0], "value_usd": float(x[1])} for x in r[1:]]
    json.dump(st_rows, open(cache, "w"))
stx = pd.DataFrame(st_rows).pivot_table(index=["state", "naics4"], columns="partner", values="value_usd", aggfunc="sum").fillna(0)

# ---------- employment ----------
zb = pd.read_csv(zipfile.ZipFile(EX / "data/raw/zbp/zbp23detail.zip").open("zbp23detail.txt"), dtype=str, usecols=["zip", "naics", "est"])
zb = zb[zb.naics.str.match(r"^\d{4}//$")]; zb["naics4"] = zb.naics.str[:4]; zb["est"] = pd.to_numeric(zb.est, errors="coerce").fillna(0)
us = pd.read_csv(EX / "data/clean/cbp2023_us_naics.csv", dtype={"NAICS2017": str}); us = us[us.NAICS2017.str.len() == 4]
epe = (pd.to_numeric(us.EMP, errors="coerce") / pd.to_numeric(us.ESTAB, errors="coerce")).set_axis(us.NAICS2017)
zb["emp"] = zb.est * zb.naics4.map(epe).fillna(0)
zb = zb[~zb.naics4.map(is_farm)]
L_us = zb.groupby("naics4").emp.sum()

z = zipfile.ZipFile(EX / "data/raw/qcew/2024_annual_singlefile.zip")
q = pd.read_csv(z.open(z.namelist()[0]), dtype=str, usecols=["area_fips", "own_code", "industry_code", "agglvl_code", "disclosure_code", "annual_avg_emplvl"])
q = q[(q.agglvl_code == "76") & (q.own_code == "5") & q.industry_code.map(is_farm)]
q["emp"] = pd.to_numeric(q.annual_avg_emplvl, errors="coerce").fillna(0)
cb = pd.read_csv(EX / "data/clean/cbp2023_county_naics.csv", dtype={"NAICS2017": str, "state": str, "county": str})
cb = cb[cb.NAICS2017.str.len() == 4]; cb["area_fips"] = cb.state.str.zfill(2) + cb.county.str.zfill(3); cb["emp_cbp"] = pd.to_numeric(cb.EMP, errors="coerce")
q = q.merge(cb[["area_fips", "NAICS2017", "emp_cbp"]].rename(columns={"NAICS2017": "industry_code"}), how="left", on=["area_fips", "industry_code"])
q["emp"] = np.where((q.disclosure_code == "N") | (q.emp == 0), q.emp_cbp.fillna(0), q.emp)
farm = q[q.area_fips.str[:2] < "57"].rename(columns={"area_fips": "county", "industry_code": "naics4"})[["county", "naics4", "emp"]]
L_us = pd.concat([L_us, farm.groupby("naics4").emp.sum()])

def rel(chamber, kind):
    out = []
    for st, fp in STATES.items():
        r = pd.read_csv(REL / f"tab20_{chamber}202420_{kind}_st{fp}.txt", sep="|", dtype=str, encoding="utf-8-sig")
        g, a = f"GEOID_{kind.upper()}" if False else ("GEOID_ZCTA5_20" if kind == "zcta520" else "GEOID_COUNTY_20"), \
               ("AREALAND_ZCTA5_20" if kind == "zcta520" else "AREALAND_COUNTY_20")
        r = r[r[g].notna() & (r[g] != "")]
        r["w"] = r.AREALAND_PART.astype(float) / r[a].astype(float).replace(0, np.nan)
        out.append(r[r.w > 0].assign(state=st, district=r[f"GEOID_{chamber.upper()}2024_20"].str[2:])[["state", "district", g, "w"]].rename(columns={g: "unit"}))
    return pd.concat(out)

rows, checks = [], []
for chamber in ["sldu", "sldl"]:
    rz, rc = rel(chamber, "zcta520"), rel(chamber, "county20")
    Lz = zb.merge(rz, left_on="zip", right_on="unit"); Lz["emp"] *= Lz.w
    Lc = farm.merge(rc, left_on="county", right_on="unit"); Lc["emp"] *= Lc.w
    L = pd.concat([Lz[["state", "district", "naics4", "emp"]], Lc[["state", "district", "naics4", "emp"]]]).groupby(["state", "district", "naics4"], as_index=False).emp.sum()
    L["L_state"] = L.groupby(["state", "naics4"]).emp.transform("sum")
    L["L_us"] = L.naics4.map(L_us)
    for pn in PARTNERS:
        xs = L.set_index(["state", "naics4"]).index.map(lambda k: stx[pn].get(k, 0.0) if pn in stx else 0.0)
        xn = L.naics4.map(nat[pn] if pn in nat else pd.Series(dtype=float)).fillna(0)
        L[f"origin_{pn}"] = np.where(L.L_state > 0, np.asarray(xs, dtype=float) * L.emp / L.L_state, 0)
        L[f"production_{pn}"] = np.where(L.L_us > 0, xn * L.emp / L.L_us, 0)
        L[f"hybrid_{pn}"] = np.where(L.naics4.map(is_ag_mining), L[f"production_{pn}"], L[f"origin_{pn}"])
    vals = [c for c in L.columns if c.split("_")[0] in ("origin", "production", "hybrid")]
    D = L.groupby(["state", "district"]).agg(emp_total=("emp", "sum"), **{c: (c, "sum") for c in vals}).reset_index()
    D.insert(1, "chamber", "upper" if chamber == "sldu" else "lower")
    for m in ["origin", "production", "hybrid"]:
        for pn in ["china", "taiwan"]:
            D[f"{m}_{pn}_usd_mn"] = D[f"{m}_{pn}"] / 1e6
            D[f"{m}_{pn}_share"] = D[f"{m}_{pn}"] / D[f"{m}_world"].replace(0, np.nan)
            D[f"{m}_{pn}_per_worker"] = D[f"{m}_{pn}"] / D.emp_total.replace(0, np.nan)
    rows.append(D.drop(columns=vals))
    for st in STATES:
        chk = {"state": st, "chamber": chamber, "n_districts": int((D.state == st).sum()),
               "census_OM_china_usd_mn": stx.loc[st]["china"].sum() / 1e6,
               "sum_origin_china_usd_mn": D[D.state == st].origin_china.sum() / 1e6,
               "sum_production_china_usd_mn": D[D.state == st].production_china.sum() / 1e6,
               "sum_hybrid_china_usd_mn": D[D.state == st].hybrid_china.sum() / 1e6}
        checks.append(chk)
out = pd.concat(rows)
out.to_csv(P / f"sld_exposure_{YEAR}.csv", index=False)
pd.DataFrame(checks).round(1).to_csv(P / "sld_exposure_check.csv", index=False)
print(pd.DataFrame(checks).round(0).to_string(index=False))
for st in STATES:
    t = out[(out.state == st) & (out.chamber == "upper")]
    print(st, "upper corr origin/production/hybrid per worker:\n", t[[f"{m}_china_per_worker" for m in ["origin", "production", "hybrid"]]].corr().round(2).to_string())
