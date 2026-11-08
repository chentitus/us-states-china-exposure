"""各州對中依賴指標與曝險分數輸入表（summary_state.csv）。分數本身在儀表板即時計算（百分位平均），這裡也輸出一份預設設定的分數供 README。"""
import pandas as pd, numpy as np
from common import *
p = pd.read_csv(CLEAN/'panel_state_year.csv'); af = pd.read_csv(CLEAN/'afida_china_land_by_state_2024.csv'); us = pd.read_csv(CLEAN/'uscbc_state_tables.csv')
Y = 2025
base = p[p.year==Y].set_index('state')
avg = p[p.year.between(2020,2025)].groupby('state')[[c for c in ['exports_china_usd_mn','imports_china_usd_mn','exports_taiwan_usd_mn','imports_taiwan_usd_mn','gdp_usd_mn'] if c in p]].sum()
S = pd.DataFrame({'state': base.index, 'state_name': base.state_name, 'state_name_zh': base.state_name_zh, 'gdp_2025_usd_mn': base.gdp_usd_mn,
    'exp_china_2025_usd_mn': base.exports_china_usd_mn, 'exp_china_share_2025': base.exports_china_share, 'exp_china_pct_gdp_2025': base.exports_china_pct_gdp,
    'exp_china_pct_gdp_2020_2025': avg.exports_china_usd_mn/avg.gdp_usd_mn*100,
    'exp_top1_hs4_share_2025': base.top1_hs4_share, 'exp_hhi_hs4_2025': base.hhi_hs4,
    'imp_china_2025_usd_mn': base.imports_china_usd_mn, 'imp_china_share_2025': base.imports_china_share, 'imp_china_pct_gdp_2025': base.imports_china_pct_gdp,
    'imp_china_pct_gdp_2020_2025': avg.imports_china_usd_mn/avg.gdp_usd_mn*100,
    'exp_taiwan_2025_usd_mn': base.get('exports_taiwan_usd_mn'), 'exp_taiwan_share_2025': base.get('exports_taiwan_share'), 'exp_taiwan_pct_gdp_2025': base.get('exports_taiwan_pct_gdp'), 'exp_top1_hs4_share_tw_2025': base.get('top1_hs4_share_tw'),
    'imp_taiwan_2025_usd_mn': base.get('imports_taiwan_usd_mn'), 'imp_taiwan_share_2025': base.get('imports_taiwan_share'), 'imp_taiwan_pct_gdp_2025': base.get('imports_taiwan_pct_gdp')}).reset_index(drop=True)
S['china_to_taiwan_export_ratio_2025'] = S.exp_china_2025_usd_mn / S.exp_taiwan_2025_usd_mn
S['china_to_taiwan_import_ratio_2025'] = S.imp_china_2025_usd_mn / S.imp_taiwan_2025_usd_mn
S = S.merge(af[['state','china_total_acres','china_ag_acres']].rename(columns={'china_total_acres':'afida_china_acres_2024','china_ag_acres':'afida_china_ag_acres_2024'}), how='left', on='state')
S[['afida_china_acres_2024','afida_china_ag_acres_2024']] = S[['afida_china_acres_2024','afida_china_ag_acres_2024']].fillna(0)   # AFIDA 未列者視為 0（申報制，為下限）
svc = us[us.measure=='services_exports_to_china'].set_index('state').value_usd_mn; tar = us[us.measure=='retaliatory_tariff_exposure'].set_index('state')
S['services_exp_china_2023_usd_mn'] = S.state.map(svc)                       # 僅前 10 州（USCBC）
S['services_exp_china_pct_gdp_2023'] = S.services_exp_china_2023_usd_mn / S.state.map(p[p.year==2023].set_index('state').gdp_usd_mn)*100
S['tariff_exposed_share_2025'] = S.state.map(tar.share_of_china_exports_pct)/100   # 僅前 10 州
S.to_csv(CLEAN/'summary_state.csv', index=False)
# 預設分數（出口依賴 + 進口依賴 兩概念）
def pct(s): return s.rank(pct=True)
S['s_export'] = pd.concat([pct(S.exp_china_pct_gdp_2025), pct(S.exp_china_share_2025)], axis=1).mean(axis=1)
S['s_vul'] = pd.concat([pct(S.exp_top1_hs4_share_2025), pct(S.exp_hhi_hs4_2025)], axis=1).mean(axis=1)
S['s_import'] = pd.concat([pct(S.imp_china_pct_gdp_2025), pct(S.imp_china_share_2025)], axis=1).mean(axis=1)
S['score'] = S[['s_export','s_import','s_vul']].mean(axis=1)
print(S.sort_values('score',ascending=False).head(15)[['state','state_name_zh','score','s_export','s_import','s_vul','exp_china_pct_gdp_2025','exp_china_share_2025','exp_top1_hs4_share_2025','imp_china_pct_gdp_2025','imp_china_share_2025','afida_china_acres_2024']].round(3).to_string(index=False))
