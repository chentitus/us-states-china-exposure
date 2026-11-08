"""Census International Trade API：各州對中國（CTY_CODE 5700）與對全世界（CTY_CODE '-'）的商品出口（Origin of Movement）與進口（state of destination）。
年度值用 time=YYYY-12 的 ALL_VAL_YR / GEN_VAL_YR（年累計）；2026 用最新可得月份的年累計（YTD）。原始 JSON 快取於 data/raw/census/。"""
import sys, json, time, requests, pandas as pd
from common import *
K = env('CENSUS_API_KEY'); OUT = RAW/'census'; OUT.mkdir(parents=True, exist_ok=True)
YEARS = [2020, 2021, 2022, 2023, 2024, 2025]; LATEST = '2026-09'
def get(flow, params, name):
    f = OUT/f'{name}.json'
    if f.exists(): return json.loads(f.read_text())
    url = f'https://api.census.gov/data/timeseries/intltrade/{flow}/statehs'
    for i in range(8):
        r = requests.get(url, params={**params, 'key': K}, timeout=300)
        if r.status_code == 200: f.write_text(r.text); return r.json()
        if r.status_code == 204: f.write_text('[]'); return []
        time.sleep(20 * (i + 1))
    raise RuntimeError(f'{name}: HTTP {r.status_code} {r.text[:200]}')
rows = []
for flow, val, comm, desc in [('exports','ALL_VAL_YR','E_COMMODITY','E_COMMODITY_SDESC'), ('imports','GEN_VAL_YR','I_COMMODITY','I_COMMODITY_SDESC')]:
    for cty in ['5700', '5830', '-']:            # 5700 中國、5830 台灣、'-' 全世界
        for lvl in (['HS2', 'HS4', 'HS6'] if cty in ('5700','5830') else ['HS2']):
            for t in [f'{y}-12' for y in YEARS] + [LATEST]:
                name = f'{flow}_{ {"5700":"china","5830":"taiwan","-":"world"}[cty] }_{lvl}_{t}'
                d = get(flow, {'get': f'STATE,CTY_CODE,CTY_NAME,{comm},{desc},{val}', 'COMM_LVL': lvl, 'CTY_CODE': cty, 'time': t}, name)
                if not d: print('empty', name); continue
                h = d[0]
                for r in d[1:]:
                    rec = dict(zip(h, r)); rows.append({'flow': flow, 'partner': {'5700':'China','5830':'Taiwan','-':'World'}[cty], 'state': rec['STATE'], 'hs_level': lvl, 'hs': rec[comm], 'hs_desc': rec[desc], 'time': t, 'year': int(t[:4]), 'ytd_through': t[5:], 'value_usd': float(rec[val])})
                print(name, len(d)-1)
df = pd.DataFrame(rows); df.to_parquet(CLEAN/'census_state_trade_raw.parquet', index=False)
print(df.shape); print(df.groupby(['flow','partner','hs_level']).size())
