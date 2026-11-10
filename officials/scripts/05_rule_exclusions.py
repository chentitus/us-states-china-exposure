"""Step 1 of classification: rule-based exclusion of obvious non-foreign-policy hits.
Rules (applied to title/description; order matters, first match wins):
  R1 memorial/ceremonial : In memory of / Memorializing / Congratulating / Commending / Honoring / Recognizing ... (person) / retirement / birthday / anniversary
  R2 ethnic heritage     : heritage month, Lunar New Year, Asian American, AAPI, Chinese American, Chinese Exclusion
  R3 language services   : (bills/releases) only term 'Chinese' and text about languages, translation, voter materials, ballots
Releases that pass get rule_excluded = ''. Everything not excluded goes to manual coding.
Output: data/processed/bills_rules.csv, data/processed/releases_rules.csv
"""
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
R1 = re.compile(r"^\s*(In memory of|Memorializing|Congratulating|Commending|Honoring|Celebrating|Recognizing .* (on|for) (his|her|their) |"
                r"Relative to the (life|memory)|In honor of)|retire(ment|s)|\bbirthday\b|\bdays?\b.*\bin Texas\b", re.I)
R2 = re.compile(r"heritage month|Lunar New Year|Asian (American|Pacific)|\bAAPI\b|\bAANHPI\b|Chinese[- ]American|Chinese Exclusion|"
                r"anti-Asian|Chinatown|Relative to .* (Month|Day|Week)\b", re.I)
R3 = re.compile(r"language|translat|ballot|voter|election|multilingual|interpret", re.I)

B = pd.read_csv(P / "bills_china_taiwan.csv")
def bill_rule(r):
    t = f"{r.title} {r.description}"
    terms = str(r.search_terms)
    political = re.search(r"Taiwan|Taipei|Communist|adversar|concern|TikTok|Huawei|ByteDance|Hong Kong|Beijing", terms)
    if R1.search(str(r.title)) and not re.search(r"Taiwan|Taipei", t):
        return "R1_ceremonial"
    if R2.search(t) and not re.search(r"Taiwan|Communist|Beijing|Hong Kong", t):
        return "R2_ethnic"
    if not political and R3.search(t):
        return "R3_language"
    return ""
B["rule_excluded"] = B.apply(bill_rule, axis=1)
B.to_csv(P / "bills_rules.csv", index=False)

R = pd.read_csv(P / "releases_china_taiwan.csv")
def rel_rule(r):
    only_chinese = r.n_chinese > 0 and r.n_china_total == r.n_chinese and r.n_taiwan_total == 0
    if only_chinese and (R3.search(str(r.title)) or r.office == "secretary_of_state"):
        return "R3_language"
    if only_chinese and R2.search(str(r.title)):
        return "R2_ethnic"
    return ""
R["rule_excluded"] = R.apply(rel_rule, axis=1)
R.drop(columns=["text"]).to_csv(P / "releases_rules.csv", index=False)
print("bills", B.groupby("state").rule_excluded.value_counts().unstack(fill_value=0))
print("releases", R.groupby(["state", "office"]).rule_excluded.value_counts().unstack(fill_value=0))
