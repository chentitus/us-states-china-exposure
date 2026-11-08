"""核對：各州加總 vs Census 全國合計（CTY '-' 列 = 全國）、USCBC 2024 前 10 州、AFIDA 官方總數。"""
import pandas as pd
from common import *
t = pd.read_parquet(CLEAN/'census_state_trade_raw.parquet'); t['bn']=t.value_usd/1e9
h2 = t[t.hs_level=='HS2']; rows=[]
for (f,p_),g in h2.groupby(['flow','partner']):
    for y in sorted(g.year.unique()):
        gy=g[g.year==y]; states=gy[gy.state.isin(STATES)].bn.sum(); nat=gy[gy.state=='-'].bn.sum(); unk=gy[~gy.state.isin(STATES)&(gy.state!='-')].bn.sum()
        rows.append((f'{f} {p_} {y}', round(states,1), round(nat,1), f'{(states-nat)/nat*100:+.1f}%' if nat else '—', f'未知州/其他 {unk:.1f}'))
us = pd.read_csv(CLEAN/'uscbc_state_tables.csv'); p = pd.read_csv(CLEAN/'panel_state_year.csv')
for r in us[us.measure=='goods_exports_to_china_uscbc'].itertuples():
    mine = p[(p.state==r.state)&(p.year==2024)].exports_china_usd_mn.iloc[0]/1000
    rows.append((f'USCBC 2024 goods exports {r.state}', round(mine,1), round(r.value_usd_mn/1000,1), f'{(mine-r.value_usd_mn/1000)/(r.value_usd_mn/1000)*100:+.1f}%', 'USCBC 用同一 Census 起運州資料'))
af = pd.read_csv(CLEAN/'afida_china_land_by_state_2024.csv'); rows.append(('AFIDA China acres 2024', int(af.china_total_acres.sum()), 247659, f'{(af.china_total_acres.sum()-247659)/247659*100:+.3f}%', 'USDA 公布 247,659'))
md = '| 項目 | 我算的 | 官方／全國合計 | 差異 | 備註 |\n|---|---|---|---|---|\n' + '\n'.join(f'| {a} | {b} | {c} | {d} | {e} |' for a,b,c,d,e in rows)
(CLEAN/'validation_results.md').write_text(md, encoding='utf-8'); print(md)
