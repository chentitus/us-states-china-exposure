"""Build bill-level and legislator-vote-level tables for China/Taiwan bills (LegiScan full-text hits).
Output: data/processed/bills_china_taiwan.csv     one row per bill
        data/processed/sponsors_china_taiwan.csv  one row per bill x sponsor
        data/processed/votes_china_taiwan.csv     one row per roll call x legislator
        data/processed/legislators.csv            LegiScan people (party, chamber, district) per session
"""
import glob, json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LS = ROOT / "data" / "raw" / "legiscan"
OUT = ROOT / "data" / "processed"
STATUS = {1: "introduced", 2: "engrossed", 3: "enrolled", 4: "passed", 5: "vetoed", 6: "failed"}

bills, spons, votes, people = [], [], [], []
for state in ["CA", "TX"]:
    hits = {h["bill_id"]: h["terms"] for h in json.load(open(LS / f"search_{state}.json"))}
    for sess in glob.glob(str(LS / f"{state}_*/{state}/*")):
        sname = Path(sess).name
        for f in glob.glob(sess + "/people/*.json"):
            p = json.load(open(f))["person"]
            if not p["committee_sponsor"]:
                people.append({"state": state, "session": sname, "people_id": p["people_id"], "name": p["name"],
                               "party": p["party"], "role": p["role"], "district": p["district"], "ballotpedia": p["ballotpedia"]})
        for f in glob.glob(sess + "/bill/*.json"):
            b = json.load(open(f))["bill"]
            if b["bill_id"] not in hits:
                continue
            last = b["history"][-1] if b["history"] else {}
            bills.append({"state": state, "session": sname, "bill_id": b["bill_id"], "bill_number": b["bill_number"],
                          "bill_type": b["bill_type"], "title": b["title"], "description": b["description"],
                          "status": STATUS.get(b["status"], b["status"]), "status_date": b["status_date"],
                          "first_action": b["history"][0]["date"] if b["history"] else "", "last_action": last.get("action", ""),
                          "subjects": "; ".join(s["subject_name"] for s in b["subjects"]),
                          "search_terms": "; ".join(hits[b["bill_id"]]),
                          "n_sponsors": len(b["sponsors"]), "n_rollcalls": len(b["votes"]),
                          "url": b["url"], "state_link": b["state_link"]})
            for s in b["sponsors"]:
                spons.append({"bill_id": b["bill_id"], "people_id": s["people_id"], "name": s["name"], "party": s["party"],
                              "role": s["role"], "district": s["district"], "committee_sponsor": s["committee_sponsor"],
                              "sponsor_type": {1: "primary", 2: "co", 3: "joint"}.get(s["sponsor_type_id"], s["sponsor_type_id"])})
            for v in b["votes"]:
                vf = Path(sess) / "vote" / f"{v['roll_call_id']}.json"
                if not vf.exists():
                    continue
                rc = json.load(open(vf))["roll_call"]
                for x in rc["votes"]:
                    votes.append({"bill_id": b["bill_id"], "roll_call_id": rc["roll_call_id"], "date": rc["date"],
                                  "desc": rc["desc"], "chamber": rc["chamber"], "passed": rc["passed"],
                                  "people_id": x["people_id"], "vote": x["vote_text"]})

B = pd.DataFrame(bills).sort_values(["state", "first_action"])
B.to_csv(OUT / "bills_china_taiwan.csv", index=False)
pd.DataFrame(spons).to_csv(OUT / "sponsors_china_taiwan.csv", index=False)
pd.DataFrame(votes).to_csv(OUT / "votes_china_taiwan.csv", index=False)
pd.DataFrame(people).drop_duplicates().to_csv(OUT / "legislators.csv", index=False)
print(B.groupby(["state", "bill_type"]).size().unstack(fill_value=0))
print("sponsor rows", len(spons), "vote rows", len(votes), "legislator-session rows", len(people))
print(B.groupby("state").status.value_counts().unstack(fill_value=0))
