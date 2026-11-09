"""Congress.gov API：第 116–119 屆所有法案標題 → 關鍵字篩出涉中／涉台法案 → 每件法案的細節、主題、提案人、共同提案人。快取於 data/raw/congress/。"""
import json, re, time, requests, pandas as pd
from common import *
K = env('DATAGOV_API_KEY'); OUT = RAW/'congress'; (OUT/'bills').mkdir(parents=True, exist_ok=True)
S = requests.Session()
def get(url, params=None, f=None):
    if f and f.exists(): return json.loads(f.read_text())
    for i in range(6):
        r = S.get(url, params={**(params or {}), 'api_key': K, 'format': 'json'}, timeout=120)
        if r.status_code == 200:
            if f: f.write_text(r.text)
            return r.json()
        if r.status_code == 429: time.sleep(60*(i+1)); continue
        time.sleep(5*(i+1))
    raise RuntimeError(f'{url} {r.status_code} {r.text[:120]}')
# 1) 所有法案標題
rows = []
for c in [116, 117, 118, 119]:
    f = OUT/f'bills_list_{c}.json'
    if f.exists(): rows += json.loads(f.read_text()); print('cached', c, flush=True); continue
    acc = []; off = 0
    while True:
        d = get(f'https://api.congress.gov/v3/bill/{c}', {'limit': 250, 'offset': off})
        acc += d.get('bills', []); off += 250
        if off % 5000 == 0: print(c, off, flush=True)
        if not d.get('pagination', {}).get('next'): break
    f.write_text(json.dumps(acc)); rows += acc; print('listed', c, len(acc), flush=True)
L = pd.DataFrame(rows); L['title'] = L.title.fillna('')
CN = re.compile(r"\b(China|Chinese|People's Republic of China|PRC|Beijing|Chinese Communist Party|CCP|Hong Kong|Xinjiang|Uyghur|Tibet)\b", re.I)
TW = re.compile(r"\b(Taiwan|Taiwanese|Taipei|Republic of China)\b", re.I)
L['china'] = L.title.str.contains(CN); L['taiwan'] = L.title.str.contains(TW)
M = L[L.china | L.taiwan].copy(); print('matched bills', len(M), 'china', M.china.sum(), 'taiwan', M.taiwan.sum(), flush=True)
# 2) 細節 + 共同提案人
detail = []; cos = []; subj = []
for i, b in enumerate(M.itertuples()):
    c, t, n = b.congress, b.type.lower(), b.number; key = f'{c}-{t}-{n}'
    d = get(f'https://api.congress.gov/v3/bill/{c}/{t}/{n}', None, OUT/'bills'/f'{key}.json')['bill']
    sp = (d.get('sponsors') or [{}])[0]
    detail.append({'bill_id': key, 'congress': c, 'type': t, 'number': n, 'title': d.get('title'), 'introduced': d.get('introducedDate'), 'policy_area': (d.get('policyArea') or {}).get('name'), 'latest_action': (d.get('latestAction') or {}).get('text'), 'latest_action_date': (d.get('latestAction') or {}).get('actionDate'), 'law': (d.get('laws') or [{}])[0].get('number') if d.get('laws') else None,
                   'sponsor_bioguide': sp.get('bioguideId'), 'sponsor_name': sp.get('fullName'), 'sponsor_party': sp.get('party'), 'sponsor_state': sp.get('state'), 'sponsor_district': sp.get('district'), 'n_cosponsors': (d.get('cosponsors') or {}).get('count', 0), 'url': f'https://www.congress.gov/bill/{c}th-congress/{ {"hr":"house-bill","s":"senate-bill","hres":"house-resolution","sres":"senate-resolution","hjres":"house-joint-resolution","sjres":"senate-joint-resolution","hconres":"house-concurrent-resolution","sconres":"senate-concurrent-resolution"}.get(t,t) }/{n}'})
    if (d.get('cosponsors') or {}).get('count', 0):
        off = 0
        while True:
            cd = get(f'https://api.congress.gov/v3/bill/{c}/{t}/{n}/cosponsors', {'limit': 250, 'offset': off}, OUT/'bills'/f'{key}_cos{off}.json')
            cos += [{'bill_id': key, 'bioguide': x['bioguideId'], 'name': x['fullName'], 'party': x['party'], 'state': x['state'], 'district': x.get('district'), 'date': x.get('sponsorshipDate'), 'original': x.get('isOriginalCosponsor'), 'withdrawn': x.get('sponsorshipWithdrawnDate')} for x in cd.get('cosponsors', [])]
            off += 250
            if not cd.get('pagination', {}).get('next'): break
    if (d.get('subjects') or {}).get('count', 0):
        sd = get(f'https://api.congress.gov/v3/bill/{c}/{t}/{n}/subjects', {'limit': 250}, OUT/'bills'/f'{key}_subj.json')
        subj += [{'bill_id': key, 'subject': s['name']} for s in (sd.get('subjects') or {}).get('legislativeSubjects', [])]
    if i % 100 == 0: print('detail', i, len(M), flush=True)
pd.DataFrame(detail).merge(M[['congress','type','number','china','taiwan']].assign(type=M.type.str.lower(), bill_id=lambda x: x.congress.astype(str)+'-'+x.type+'-'+x.number.astype(str))[['bill_id','china','taiwan']], on='bill_id').to_csv(CLEAN/'congress_bills.csv', index=False)
pd.DataFrame(cos).to_csv(CLEAN/'congress_cosponsors.csv', index=False); pd.DataFrame(subj).to_csv(CLEAN/'congress_bill_subjects.csv', index=False); print('done', len(detail), len(cos), flush=True)
