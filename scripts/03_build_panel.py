"""州—年面板：各州對中出口／進口（金額、占州總出口／進口比、占州 GDP）、前十大商品（HS4）、集中度；靜態層：AFIDA 中國農地、USCBC 服務出口與關稅曝險。"""
import pandas as pd, numpy as np
from common import *
t = pd.read_parquet(CLEAN/'census_state_trade_raw.parquet')
t = t[t.state.isin(STATES.keys())]                       # 去掉 '-'（全國合計）與未知州
t['value_usd_mn'] = t.value_usd/1e6
gdp = pd.read_csv(CLEAN/'bea_state_gdp.csv')
# ---- state-year totals (HS2 層加總 = 全部商品)
h2 = t[t.hs_level=='HS2'].groupby(['state','year','ytd_through','flow','partner']).value_usd_mn.sum().unstack(['flow','partner'])
h2.columns = [f'{f}_{p.lower()}_usd_mn' for f,p in h2.columns]; h2 = h2.reset_index()
for f in ['exports','imports']:
    for c in ['china','taiwan']:
        if f'{f}_{c}_usd_mn' in h2: h2[f'{f}_{c}_share'] = h2[f'{f}_{c}_usd_mn']/h2[f'{f}_world_usd_mn']
g = gdp.copy(); g26 = g[g.year==2025].assign(year=2026); g = pd.concat([g,g26])   # 2026 用 2025 GDP（YTD 對照）
h2 = h2.merge(g, how='left', on=['state','year'])
for f in ['exports','imports']:
    for c in ['china','taiwan']:
        if f'{f}_{c}_usd_mn' in h2: h2[f'{f}_{c}_pct_gdp'] = h2[f'{f}_{c}_usd_mn']/h2.gdp_usd_mn*100
# ---- concentration of China exports by HS4
h4 = t[(t.hs_level=='HS4')&(t.partner.isin(['China','Taiwan']))]
def conc(d):
    s = d.groupby('hs').value_usd_mn.sum(); tot = s.sum(); sh = s/tot if tot else s
    return pd.Series({'hhi_hs4': float((sh**2).sum()) if tot else np.nan, 'top1_hs4_share': float(sh.max()) if tot else np.nan, 'top3_hs4_share': float(sh.nlargest(3).sum()) if tot else np.nan})
for part, suf in [('China',''),('Taiwan','_tw')]:
    c = h4[(h4.flow=='exports')&(h4.partner==part)].groupby(['state','year']).apply(conc).reset_index()
    c.columns = ['state','year'] + [x+suf for x in ['hhi_hs4','top1_hs4_share','top3_hs4_share']]
    h2 = h2.merge(c, how='left', on=['state','year'])
h2['state_name'] = h2.state.map(STATES); h2['state_name_zh'] = h2.state.map(STATES_ZH)
cols = ['state','state_name','state_name_zh','year','ytd_through','gdp_usd_mn','exports_world_usd_mn','imports_world_usd_mn'] + [c for c in h2.columns if ('china' in c or 'taiwan' in c or 'hs4' in c) and c not in ('exports_world_usd_mn','imports_world_usd_mn')]
h2 = h2[cols].sort_values(['state','year'])
h2.to_csv(CLEAN/'panel_state_year.csv', index=False)
# ---- top products (HS4 & HS2) per state-year-flow with share
tp = t[(t.partner.isin(['China','Taiwan']))&(t.hs_level.isin(['HS2','HS4','HS6']))].copy()
tp['total'] = tp.groupby(['state','year','flow','partner','hs_level']).value_usd_mn.transform('sum'); tp['share'] = tp.value_usd_mn/tp.total
tp['rank'] = tp.groupby(['state','year','flow','partner','hs_level']).value_usd_mn.rank(ascending=False, method='first')
top = tp[tp['rank']<=10][['state','year','flow','partner','hs_level','rank','hs','hs_desc','value_usd_mn','share']].sort_values(['state','year','flow','partner','hs_level','rank'])
top.to_csv(CLEAN/'top_products_state_year.csv', index=False)
# ---- national-level check: sum of states vs '-' total
nat = t[(t.hs_level=='HS2')&(t.partner.isin(['China','Taiwan']))].groupby(['partner','year','flow']).value_usd_mn.sum()
print('Trade, sum of states (bn):'); print((nat/1000).round(1).unstack())
print(h2[h2.year==2024].sort_values('exports_china_usd_mn',ascending=False).head(10)[['state','exports_china_usd_mn','exports_china_share','exports_china_pct_gdp','imports_china_usd_mn','imports_china_share','top1_hs4_share']].round(3).to_string(index=False))
