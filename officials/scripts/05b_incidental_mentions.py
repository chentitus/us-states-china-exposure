"""Step 1b: drop bills whose every keyword occurrence is incidental (non-foreign-policy).
Incidental contexts removed from the bill text before recounting keywords:
  - named local institutions / ethnic-community uses: Chinese Hospital, Chinese Cultural Center, Chinatown,
    Chinese American, Chinese medicine / Traditional Chinese, Chinese (Mandarin|Cantonese|language), Chinese New Year
  - demographic or language enumerations: a keyword within 60 characters of two or more other
    Asian ethnic/language/country names (Japanese, Korean, Filipino, Vietnamese, Hmong, ...)
A bill with zero remaining keyword hits gets rule_excluded = 'R4_incidental'.
Updates data/processed/bills_rules.csv in place.
"""
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P, TX = ROOT / "data" / "processed", ROOT / "data" / "raw" / "legiscan" / "texts"
KW = re.compile(r"China|Chinese|Beijing|Communist Party|Hong Kong|Taiwan|Taipei|foreign adversar|countr(y|ies) of concern|TikTok|Huawei|ByteDance", re.I)
NAMED = re.compile(r"Chinese (Hospital|Cultural Center|Historical Society|Six Companies|Consolidated Benevolent|Community|Center|"
                   r"American|Americans|medicine|herbal|New Year|Mandarin|Cantonese|language|Exclusion)|Traditional Chinese|Chinatown|"
                   r"Chinese-American|Taiwanese American|Taiwanese-American|Lunar New Year", re.I)
OTHERS = re.compile(r"Japanese|Korean|Filipino|Vietnamese|Hmong|Cambodian|Laotian|Thai|Asian Indian|Indonesian|Malaysian|Pakistani|"
                    r"Samoan|Tagalog|Spanish|Russian|Armenian|Arabic|Farsi|Punjabi|Hindi|Japan|Korea|Vietnam|Laos|Cambodia|Philippines|Mongolia", re.I)

def residual(t):
    t = NAMED.sub(" ", t)
    keep = 0
    for m in KW.finditer(t):
        ctx = t[max(0, m.start() - 60): m.end() + 60]
        if len(set(x.lower() for x in OTHERS.findall(ctx))) >= 2:
            continue
        keep += 1
    return keep

B = pd.read_csv(P / "bills_rules.csv")
for i, r in B[B.rule_excluded.isna()].iterrows():
    f = TX / f"{r.bill_id}.txt"
    t = f"{r.title} {r.description} " + (f.read_text() if f.exists() else "")
    if residual(t) == 0:
        B.at[i, "rule_excluded"] = "R4_incidental"
B.to_csv(P / "bills_rules.csv", index=False)
print(B.groupby("state").rule_excluded.value_counts(dropna=False).unstack(fill_value=0))
