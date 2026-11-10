"""Legislative China/Taiwan indicators, from the coded bills (07).
Core codes only: R (bill targets China/foreign adversaries), Rc (China clause in a general bill), C (cooperation), T (Taiwan-friendly).
Direction and Taiwan share use R (subject) only.
Peripheral codes (Rp, Tp) and X are not counted.

STATE level, separately for bills and resolutions, for the analysis window (sessions starting 2025+) pooled and by year of introduction:
  total            all bills (or resolutions) introduced
  R, C, T          counts introduced;  R_pass, C_pass, T_pass  counts passed (LegiScan status 4)
  R_per_1000       salience  = 1000 * R / total            (likewise T_per_1000, C_per_1000)
  direction        (R - C) / (R + C)                       +1 = all restrictive, -1 = all cooperative; NaN if R+C = 0
  taiwan_share     T / (R + C + T)
  R_pass_rate      R_pass / R                              (likewise T_pass_rate)

LEGISLATOR level (one row per LegiScan people_id, party/district from the latest session they served):
  spons_{R,C,T}_primary   bills/resolutions where the legislator is primary sponsor
  spons_{R,C,T}_any       primary + co-sponsor
  yea_{R,C,T}, nay_{R,C,T}   votes cast on all recorded roll calls (committee and floor) on those bills
  yea_share_{R,C,T}       yea / (yea + nay); NaN if the legislator cast no yea/nay vote
Output: data/processed/ind_state_{pooled,yearly}.csv, data/processed/ind_legislator.csv
"""
import glob, json
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P, LS = ROOT / "data" / "processed", ROOT / "data" / "raw" / "legiscan"
CORE = ["R", "Rc", "C", "T"]
# Analysis window (decided 2026-11-10): legislatures that START in 2025 or later, i.e. the 2025-26 session
# (CA 2025-26 Regular; TX 89th Regular + special sessions). Bills prefiled in late 2024 for these sessions are
# included and counted in year 2025.
START_YEAR = 2025

# ---------- state level ----------
rows = []
for f in glob.glob(str(LS / "*_*/*/*/bill/*.json")):
    b = json.load(open(f))["bill"]; h = b["history"]
    y0 = b["session"]["year_start"]
    yr = (h[0]["date"] if h else str(b["status_date"]))[:4]
    rows.append({"state": b["state"], "bill_id": b["bill_id"], "kind": "bill" if b["bill_type"] == "B" else "resolution",
                 "session_start": y0, "year": str(max(int(yr), y0)) if yr.isdigit() else str(y0), "passed": b["status"] == 4})
A = pd.DataFrame(rows)
A = A[A.session_start >= START_YEAR]
IN_WINDOW = set(A.bill_id)
A = A.merge(pd.read_csv(P / "bills_coded.csv")[["bill_id", "code"]], on="bill_id", how="left")
A["code"] = A.code.fillna("none")

def summarise(g):
    out = {"total": len(g)}
    for c in CORE:
        out[c] = int((g.code == c).sum())
        out[c + "_pass"] = int(((g.code == c) & g.passed).sum())
        out[c + "_per_1000"] = round(1000 * out[c] / len(g), 2)
    rc = out["R"] + out["C"]
    out["direction"] = (out["R"] - out["C"]) / rc if rc else np.nan
    out["taiwan_share"] = out["T"] / (rc + out["T"]) if rc + out["T"] else np.nan
    for c in ["R", "Rc", "T"]:
        out[c + "_pass_rate"] = out[c + "_pass"] / out[c] if out[c] else np.nan
    return pd.Series(out)

A.groupby(["state", "kind"]).apply(summarise, include_groups=False).reset_index().to_csv(P / "ind_state_pooled.csv", index=False)
A.groupby(["state", "kind", "year"]).apply(summarise, include_groups=False).reset_index().to_csv(P / "ind_state_yearly.csv", index=False)

# ---------- legislator level ----------
code = pd.read_csv(P / "bills_coded.csv").set_index("bill_id").code
leg = pd.read_csv(P / "legislators.csv")
leg = leg[leg.session.str[:4].astype(int) >= START_YEAR].sort_values("session").drop_duplicates("people_id", keep="last")
leg = leg[["people_id", "state", "name", "party", "role", "district", "ballotpedia", "session"]].rename(columns={"session": "last_session"})

S = pd.read_csv(P / "sponsors_china_taiwan.csv")
S = S[S.committee_sponsor == 0].assign(code=lambda d: d.bill_id.map(code))
S = S[S.code.isin(CORE) & S.bill_id.isin(IN_WINDOW)]
sp = pd.concat([
    S[S.sponsor_type == "primary"].pivot_table(index="people_id", columns="code", values="bill_id", aggfunc="nunique").add_prefix("spons_").add_suffix("_primary"),
    S.pivot_table(index="people_id", columns="code", values="bill_id", aggfunc="nunique").add_prefix("spons_").add_suffix("_any"),
], axis=1)

V = pd.read_csv(P / "votes_china_taiwan.csv").assign(code=lambda d: d.bill_id.map(code))
V = V[V.code.isin(CORE) & V.vote.isin(["Yea", "Nay"]) & V.bill_id.isin(IN_WINDOW)]
vt = V.pivot_table(index="people_id", columns=["vote", "code"], values="roll_call_id", aggfunc="count")
vt.columns = [f"{'yea' if v == 'Yea' else 'nay'}_{c}" for v, c in vt.columns]

L = leg.set_index("people_id").join(sp).join(vt)
for c in CORE:
    for col in [f"spons_{c}_primary", f"spons_{c}_any", f"yea_{c}", f"nay_{c}"]:
        if col not in L: L[col] = 0
        L[col] = L[col].fillna(0).astype(int)
    tot = L[f"yea_{c}"] + L[f"nay_{c}"]
    L[f"yea_share_{c}"] = (L[f"yea_{c}"] / tot).where(tot > 0)
L.reset_index().to_csv(P / "ind_legislator.csv", index=False)

pd.set_option("display.width", 200)
print(pd.read_csv(P / "ind_state_pooled.csv").round(2).to_string(index=False))
print()
print(L.groupby(["state", "party"]).agg(n=("name", "size"), spons_R=("spons_R_any", "sum"), spons_T=("spons_T_any", "sum"),
      yea_share_R=("yea_share_R", "mean"), yea_share_T=("yea_share_T", "mean")).round(2).to_string())

# ---------- legislator x biennium level ----------
# Unit = one person in one two-year legislature (TX special sessions fold into their biennium).
# Indicators count only the bills of that biennium and the votes cast on them.
# Output: data/processed/ind_legislator_session.csv
def biennium(sess):
    y = int(str(sess)[:4]); y = y if y % 2 else y - 1
    return f"{y}-{y + 1}"

Bsess = pd.read_csv(P / "bills_coded.csv")[["bill_id", "session", "code"]]
Bsess["biennium"] = Bsess.session.map(biennium)
bien = Bsess.set_index("bill_id").biennium
LS_ = pd.read_csv(P / "legislators.csv").assign(biennium=lambda d: d.session.map(biennium))
LS_ = LS_[LS_.biennium.str[:4].astype(int) >= START_YEAR]
LS_ = (LS_.sort_values("session").groupby(["people_id", "biennium"])
       .agg(state=("state", "last"), name=("name", "last"), party=("party", "last"), role=("role", "last"),
            district=("district", "last"), ballotpedia=("ballotpedia", "last")).reset_index())

S2 = S.assign(biennium=S.bill_id.map(bien))
V2 = V.assign(biennium=V.bill_id.map(bien))
sp2 = pd.concat([
    S2[S2.sponsor_type == "primary"].pivot_table(index=["people_id", "biennium"], columns="code", values="bill_id", aggfunc="nunique").add_prefix("spons_").add_suffix("_primary"),
    S2.pivot_table(index=["people_id", "biennium"], columns="code", values="bill_id", aggfunc="nunique").add_prefix("spons_").add_suffix("_any"),
], axis=1)
vt2 = V2.pivot_table(index=["people_id", "biennium"], columns=["vote", "code"], values="roll_call_id", aggfunc="count")
vt2.columns = [f"{'yea' if v == 'Yea' else 'nay'}_{c}" for v, c in vt2.columns]
last_vote = V2.groupby(["people_id", "biennium"]).date.max().rename("last_vote_date")

LB = LS_.set_index(["people_id", "biennium"]).join(sp2).join(vt2).join(last_vote)
for c in CORE:
    for col in [f"spons_{c}_primary", f"spons_{c}_any", f"yea_{c}", f"nay_{c}"]:
        if col not in LB: LB[col] = 0
        LB[col] = LB[col].fillna(0).astype(int)
    tot = LB[f"yea_{c}"] + LB[f"nay_{c}"]
    LB[f"yea_share_{c}"] = (LB[f"yea_{c}"] / tot).where(tot > 0)
LB = LB.reset_index()
# seat holder for maps: if several people held the same seat in a biennium (special election, resignation),
# mark the one with the latest recorded vote on a coded bill as the seat holder; ties/no votes -> last listed
LB["seat_holder"] = False
LB = LB.sort_values(["state", "role", "district", "biennium", "last_vote_date"], na_position="first")
LB.loc[LB.groupby(["state", "role", "district", "biennium"]).tail(1).index, "seat_holder"] = True
LB.to_csv(P / "ind_legislator_session.csv", index=False)
print("legislator-biennium rows", len(LB), "| seats with >1 person:",
      int((LB.groupby(["state", "role", "district", "biennium"]).size() > 1).sum()))

# ---------- deviation from own party (legislator x biennium) ----------
# For each roll call on R / Rc / T bills: party majority = the vote (Yea or Nay) cast by more than half of that party's
# members who voted Yea or Nay; ties -> no majority, roll call skipped for that party.
#   dev_{c}         share of a legislator's Yea/Nay votes that went against their party majority
#   signed_dev_{c}  (Yea against a Nay majority - Nay against a Yea majority) / votes counted
#                   > 0 = votes more for the bill than own party (for R: more anti-China than the party), < 0 = less
#   n_dev_{c}       votes counted
# Output: added to data/processed/ind_legislator_session.csv
party = LS_.set_index(["people_id", "biennium"]).party
VD = V2.copy()
VD["party"] = [party.get((p, b)) for p, b in zip(VD.people_id, VD.biennium)]
VD = VD[VD.party.isin(["D", "R"])]
VD["yea"] = (VD.vote == "Yea").astype(int)
g = VD.groupby(["roll_call_id", "party"]).yea.agg(["sum", "count"]).reset_index()
g["maj"] = np.where(g["sum"] * 2 > g["count"], "Yea", np.where(g["sum"] * 2 < g["count"], "Nay", None))
VD = VD.merge(g[["roll_call_id", "party", "maj"]], on=["roll_call_id", "party"])
VD = VD[VD.maj.notna()]
VD["against"] = (VD.vote != VD.maj).astype(int)
VD["signed"] = np.where(VD.against == 0, 0, np.where(VD.vote == "Yea", 1, -1))
D = VD.groupby(["people_id", "biennium", "code"]).agg(n=("against", "size"), dev=("against", "mean"), sdev=("signed", "mean")).unstack("code")
D.columns = [{"n": "n_dev", "dev": "dev", "sdev": "signed_dev"}[a] + "_" + c for a, c in D.columns]
LB = LB.drop(columns=[c for c in LB.columns if c.startswith(("n_dev_", "dev_", "signed_dev_"))], errors="ignore")
LB = LB.merge(D.reset_index(), on=["people_id", "biennium"], how="left")
LB.to_csv(P / "ind_legislator_session.csv", index=False)
print(LB.groupby(["state", "party"])[[c for c in LB.columns if c.startswith(("dev_", "signed_dev_"))]].mean().round(3).to_string())
