"""Manual coding of executive-branch releases that survived rule exclusions (05).
Coded from title + first keyword-in-context snippet. Codes stored in data/processed/release_codes_manual.json (url -> code).
Codes:
  R  = restriction / criticism of China is the subject      Rp = critical, peripheral
  C  = cooperation / engagement with China is the subject   Cp = cooperation mentioned peripherally
                                                                 (incl. boilerplate list of 2023 China MOUs)
  K  = competition framing: China as economic/technological rival, used mainly to attack federal policy
       ("Trump cedes the clean-energy economy to China")
  T  = Taiwan-friendly subject                              Tp = Taiwan mentioned favourably, peripherally
  X  = incidental (biographies, language lists, place names, GDP rankings)
Unlisted rows = X. Output: data/processed/releases_coded.csv
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
import json
CODES = json.load(open(P / "release_codes_manual.json"))  # url -> code (keyed by URL so re-running 02/05 cannot shift rows)
R = pd.read_csv(P / "releases_rules.csv")
R["code"] = [("X" if isinstance(r.rule_excluded, str) else CODES.get(r.url, "X")) for _, r in R.iterrows()]
R["coded_by"] = R.rule_excluded.fillna("manual")
R.to_csv(P / "releases_coded.csv", index=False)
print(R.groupby(["state", "office", "code"]).size().unstack(fill_value=0))
