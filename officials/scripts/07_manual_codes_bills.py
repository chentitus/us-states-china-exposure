"""Step 2 of classification: manual coding of bills that survived rule exclusions (05, 05b).
Coded from title + keyword-in-context snippets of the latest bill text (see 06).
Codes:
  R  = "R subject": the bill itself targets China / foreign adversaries
       (foreign-adversary/country-of-concern restrictions, CCP/human-rights condemnation)
  Rc = "R clause": a general bill (privacy, bonds, procurement, homeland security, ...) carrying an operative
       China / foreign-adversary clause; split from R on 2026-11-10 because votes on such bills mostly reflect the
       rest of the bill
  Rp = China framed critically, but only peripherally (findings/whereas clauses; bill is about something else)
  C  = cooperation / engagement with China is the subject
  T  = Taiwan-friendly (resolution, office funding)
  Tp = Taiwan mentioned favourably, peripherally
  X  = incidental / unrelated (place names, history, recycling-market facts, lists of countries)
Any surviving bill not listed below is coded X. Output: data/processed/bills_coded.csv
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
CODES = {
    # California
    1456723: "Rp", 1584601: "Rp", 2118604: "Rp", 1655612: "R", 1345542: "C", 1849336: "Rp", 1385557: "C",
    1974460: "Rp", 1453447: "Rp", 1639202: "Rp", 1742861: "R", 1745999: "R", 1504274: "R", 1273586: "Tp",
    2117191: "R", 1594832: "Rp", 1970450: "R", 1655619: "R", 2083561: "R", 1227222: "Rp", 1885717: "T",
    2151886: "T", 1521875: "T", 2042443: "T", 1372511: "R", 1624071: "T",
    # Texas: restriction / condemnation bills
    1891172: "R", 2005897: "R", 2005933: "R", 1644222: "R", 2005926: "R", 2005649: "R", 2005961: "R", 2005802: "R",
    2005818: "R", 2005691: "R", 1891002: "R", 1444153: "R", 1919831: "R", 1923345: "R", 1699187: "R", 1704923: "R",
    1947399: "R", 1464139: "R", 1953508: "R", 1954352: "R", 1954608: "R", 1710854: "R", 1959335: "R", 1963278: "R",
    1720033: "R", 1719934: "R", 1472923: "R", 1473083: "R", 1973285: "R", 1520255: "R", 1474965: "R", 2005656: "R",
    1728875: "R", 1730445: "R", 1730521: "R", 1996208: "R", 1996709: "R", 1999515: "R", 1481498: "R", 2000727: "R",
    2002729: "R", 2005197: "R", 2005148: "R", 2004689: "R", 1733436: "R", 1733440: "R", 2005935: "R", 2006581: "R",
    2006623: "R", 2008407: "R", 1382360: "R", 1509981: "R", 1231708: "R", 1890835: "R", 1713745: "R", 1714004: "R",
    1721730: "R", 1970154: "R", 1973528: "R", 1726269: "R", 1981890: "R", 1976809: "R", 1987786: "R", 1990936: "R",
    1730281: "R", 1990854: "R", 1730472: "R", 1731166: "R", 1994153: "R", 1481896: "R", 1732645: "R", 2000179: "R",
    1735264: "R", 1734503: "R", 2005834: "R", 2005673: "R", 1734516: "R", 1734279: "R", 2006218: "R", 2006257: "R",
    2006895: "R", 2007383: "R", 2006168: "R", 1675911: "R", 1897734: "R", 1918777: "R", 1942187: "R", 1407123: "R",
    1734263: "R", 1254211: "R",
    # Texas: peripheral criticism
    1892959: "Rp", 1891018: "Rp", 1668059: "Rp", 1698414: "Rp", 2030143: "Rp", 1513235: "Rp", 1513244: "Rp",
    1767626: "Rp", 1768094: "Rp", 1920124: "Rp", 1734882: "Rp", 1892829: "Rp", 2029658: "Rp", 1763474: "Rp", 1782834: "Rp",
    # Texas: Taiwan
    2019269: "T", 1741827: "T", 1462676: "T", 1131402: "T", 1743850: "T", 1726065: "T",
}
RC = {2117191, 1970450, 1655619, 2083561,                       # CA: data brokers x2, wildfire tech office, research bond
      1891172, 2006168, 1918777, 2002729, 1735264, 1996709, 2008407}  # TX: gold specie, homeland security x2, airport fund, tech fund, hemp x2
CODES.update({b: "Rc" for b in RC})
B = pd.read_csv(P / "bills_rules.csv")
B["code"] = B.apply(lambda r: "X" if isinstance(r.rule_excluded, str) else CODES.get(r.bill_id, "X"), axis=1)
B["coded_by"] = B.rule_excluded.fillna("manual")
B.to_csv(P / "bills_coded.csv", index=False)
print(B.groupby(["state", "code"]).size().unstack(fill_value=0))
