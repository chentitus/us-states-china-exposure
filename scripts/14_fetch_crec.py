"""GovInfo：國會記錄（CREC）2020–2026 中提到中國／台灣的 granule → 每日 MODS 取 granule 的發言議員（congMember，含 bioguide ID）→ granule 全文取關鍵句。快取於 data/raw/crec/。"""
import json, re, time, html, requests, pandas as pd, xml.etree.ElementTree as ET
from common import *
K = env('DATAGOV_API_KEY'); OUT = RAW/'crec'; (OUT/'mods').mkdir(parents=True, exist_ok=True); (OUT/'htm').mkdir(exist_ok=True)
S = requests.Session()
def req(method, url, f=None, **kw):
    if f and f.exists(): return f.read_text()
    for i in range(6):
        r = S.request(method, url, params={**kw.pop('params', {}), 'api_key': K}, timeout=120, **kw)
        if r.status_code == 200:
            if f: f.write_text(r.text)
            return r.text
        if r.status_code in (429, 503): time.sleep(30*(i+1)); continue
        if r.status_code == 404: return ''
        time.sleep(5*(i+1))
    raise RuntimeError(f'{url} {r.status_code}')
# 1) search granules
Q = {'china': '(China OR Chinese OR Beijing OR "Chinese Communist Party" OR CCP OR "Hong Kong" OR Xinjiang OR Uyghur)', 'taiwan': '(Taiwan OR Taiwanese OR Taipei)'}
rows = []
for tag, q in Q.items():
    for y in range(2020, 2027):
        f = OUT/f'search_{tag}_{y}.json'
        if f.exists(): res = json.loads(f.read_text())
        else:
            res = []; mark = '*'
            while True:
                body = {'query': f'collection:CREC {q} publishdate:range({y}-01-01,{y}-12-31)', 'pageSize': 1000, 'offsetMark': mark, 'sorts': [{'field': 'publishdate', 'sortOrder': 'ASC'}]}
                d = json.loads(req('POST', 'https://api.govinfo.gov/search', json=body, headers={'Content-Type': 'application/json'}))
                res += d.get('results', []); mark = d.get('offsetMark')
                if not mark or not d.get('results') or len(res) >= d.get('count', 0): break
            f.write_text(json.dumps(res))
        print(tag, y, len(res), flush=True)
        rows += [{'tag': tag, 'granuleId': r.get('granuleId'), 'packageId': r.get('packageId'), 'date': r.get('dateIssued'), 'title': r.get('title'), 'chamber': (r.get('governmentAuthor') or [''])[0] if isinstance(r.get('governmentAuthor'), list) else r.get('governmentAuthor')} for r in res if r.get('granuleId')]
G = pd.DataFrame(rows); G = G[G.granuleId.notna()]
flags = G.groupby('granuleId').tag.agg(lambda s: set(s)); gran = G.drop_duplicates('granuleId').set_index('granuleId'); gran['china'] = [ 'china' in flags[g] for g in gran.index]; gran['taiwan'] = ['taiwan' in flags[g] for g in gran.index]
print('granules', len(gran), 'china', gran.china.sum(), 'taiwan', gran.taiwan.sum(), '| packages', gran.packageId.nunique(), flush=True)
# 2) MODS per package → congMember per granule
mem = []
pk = sorted(gran.packageId.unique())
for i, p in enumerate(pk):
    x = req('GET', f'https://api.govinfo.gov/packages/{p}/mods', OUT/'mods'/f'{p}.xml')
    if not x: continue
    try: root = ET.fromstring(x)
    except ET.ParseError: continue
    ns = {'m': 'http://www.loc.gov/mods/v3'}
    for rel in root.iter('{http://www.loc.gov/mods/v3}relatedItem'):
        rid = rel.get('ID') or ''
        gid = rid[3:] if rid.startswith('id-') else None   # granule ID 取自 relatedItem 的 ID 屬性（id-CREC-...）
        if gid not in gran.index: continue
        for ext in rel.findall('m:extension', ns):
            for cm in ext.findall('m:congMember', ns):
                nm = ''.join(cm.itertext()).strip()
                mem.append({'granuleId': gid, 'bioguide': cm.get('bioGuideId'), 'chamber': cm.get('chamber'), 'party': cm.get('party'), 'state': cm.get('state'), 'role': cm.get('role'), 'name': nm[:80]})
    if i % 100 == 0: print('mods', i, len(pk), flush=True)
MEM = pd.DataFrame(mem); print('speaker rows', len(MEM), 'granules with speakers', MEM.granuleId.nunique() if len(MEM) else 0, flush=True)
# 3) granule text → keyword sentences
KW = re.compile(r"\b(China|Chinese|Beijing|CCP|Chinese Communist Party|Hong Kong|Xinjiang|Uyghur|Taiwan|Taiwanese|Taipei)\b", re.I)
snip = []
for i, (gid, g) in enumerate(gran.iterrows()):
    t = req('GET', f'https://api.govinfo.gov/packages/{g.packageId}/granules/{gid}/htm', OUT/'htm'/f'{gid}.htm')
    if not t: continue
    txt = html.unescape(re.sub(r'<[^>]+>', ' ', t)); txt = re.sub(r'\s+', ' ', txt)
    sents = re.split(r'(?<=[.!?])\s+', txt); hits = [s for s in sents if KW.search(s)]
    snip.append({'granuleId': gid, 'n_china': len(re.findall(r"\b(China|Chinese|Beijing|CCP)\b", txt, re.I)), 'n_taiwan': len(re.findall(r"\b(Taiwan|Taiwanese|Taipei)\b", txt, re.I)), 'snippet': ' … '.join(hits[:2])[:600], 'words': len(txt.split())})
    if i % 500 == 0: print('htm', i, len(gran), flush=True)
SN = pd.DataFrame(snip)
gran.reset_index().merge(SN, how='left', on='granuleId').to_csv(CLEAN/'crec_granules.csv', index=False); MEM.to_csv(CLEAN/'crec_speakers.csv', index=False); print('done', flush=True)
