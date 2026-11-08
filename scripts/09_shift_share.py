"""Shift-share 郡級／選區級對中（台）貿易曝險。
曝險_g(y) = Σ_i [ L_{g,i} / L_i ] × X_i(y)，i = NAICS 4 位碼，L = CBP 2023 就業，X = 全國對中（台）出口（或進口）。
即：假設每個產業的對中貿易按就業比例分布到各郡／選區。除以郡 GDP（BEA CAGDP2）得占 GDP %。這是結構性曝險的配置估計，不是觀測到的貿易流。"""
import pandas as pd, numpy as np
from common import *
tr = pd.read_csv(CLEAN/'naics_national_trade.csv', dtype={'naics4':str})
us = pd.read_csv(CLEAN/'cbp2023_us_naics.csv', dtype={'NAICS2017':str}); us = us[us.NAICS2017.str.len()==4].rename(columns={'NAICS2017':'naics4'})
us['EMP']=pd.to_numeric(us.EMP, errors='coerce'); L_us = us.set_index('naics4').EMP
def exposure(geo_df, key_cols):
    g = geo_df[geo_df.NAICS2017.str.len()==4].copy(); g['naics4']=g.NAICS2017; g['EMP']=pd.to_numeric(g.EMP, errors='coerce').fillna(0)
    g['L_us'] = g.naics4.map(L_us); g = g[g.L_us>0]; g['w'] = g.EMP/g.L_us            # 該地區占全國該產業就業的比例
    out=[]; contrib=[]
    desc = tr.drop_duplicates('naics4').set_index('naics4').naics_desc
    for (flow,pn,y,ytd), t in tr.groupby(['flow','partner','year','ytd_through']):
        x = t.set_index('naics4').value_usd
        gg = g.assign(v = g.naics4.map(x).fillna(0)*g.w)
        if y in (2024,2025) and pn in ('china','taiwan'):
            top = gg[gg.v>0].sort_values('v',ascending=False).groupby(key_cols).head(6)
            contrib.append(top.assign(flow=flow,partner=pn,year=y,value_usd_mn=top.v/1e6,naics_desc=top.naics4.map(desc),emp=top.EMP)[key_cols+['flow','partner','year','naics4','naics_desc','emp','value_usd_mn']])
        agg = gg.groupby(key_cols).v.sum().rename(f'{flow}_{pn}_usd_mn')/1e6
        out.append(agg.to_frame().assign(year=y, ytd_through=ytd).reset_index())
    res = out[0]
    for o in out[1:]: res = res.merge(o, how='outer')
    # 合併同年各欄
    res = res.groupby(key_cols+['year','ytd_through'], as_index=False).first()
    exposure.contrib = pd.concat(contrib) if contrib else pd.DataFrame()
    return res
# ---- county
cb = pd.read_csv(CLEAN/'cbp2023_county_naics.csv', dtype={'NAICS2017':str,'state':str,'county':str})
cb['geofips'] = cb.state.str.zfill(2)+cb.county.str.zfill(3)
cty = exposure(cb, ['geofips']); exposure.contrib.to_csv(CLEAN/'county_shift_share_industries.csv', index=False)
gdp = pd.read_csv(CLEAN/'bea_county_gdp.csv', dtype={'geofips':str}); gdp['gdp_usd_mn']=gdp.gdp_usd_k/1000
g24 = gdp[gdp.year==2024][['geofips','gdp_usd_mn']]; g25 = g24.assign(year=2025); g26 = g24.assign(year=2026); g24=g24.assign(year=2024)
gdpy = pd.concat([gdp[gdp.year<=2023][['geofips','year','gdp_usd_mn']], g24, g25, g26])
cty = cty.merge(gdpy, how='left', on=['geofips','year'])
names = gdp.drop_duplicates('geofips').set_index('geofips').geoname; cty['county_name'] = cty.geofips.map(names)
cty['state'] = cty.county_name.str.extract(r', ([A-Z]{2})')[0]
emp_tot = cb[cb.NAICS2017=='00'].groupby('geofips').EMP.apply(lambda s: pd.to_numeric(s,errors='coerce').sum()); cty['emp_total_2023'] = cty.geofips.map(emp_tot)
for pn in ['china','taiwan']:
    for f in ['exports','imports']:
        c=f'{f}_{pn}_usd_mn'
        if c in cty: cty[f'{f}_{pn}_pct_gdp'] = cty[c]/cty.gdp_usd_mn*100; cty[f'{f}_{pn}_per_worker'] = cty[c]*1e6/cty.emp_total_2023
cty.to_csv(CLEAN/'county_shift_share.csv', index=False)
# ---- congressional district：CBP 選區層級只有 2 位碼產業，故以郡級曝險 × 郡在各選區的土地面積占比配置（Census rel2020 tab20_cd11920_county20_natl；整郡屬單一選區者精確，被分割的都會郡為面積近似）
rel = pd.read_csv(RAW/'geo/rel/tab20_cd11920_county20_natl.txt', sep='|', dtype=str, encoding='utf-8-sig')
rel['w'] = rel.AREALAND_PART.astype(float)/rel.AREALAND_COUNTY_20.astype(float).replace(0,np.nan); rel = rel[rel.w>0][['GEOID_CD119_20','GEOID_COUNTY_20','w']].rename(columns={'GEOID_CD119_20':'cd_geoid','GEOID_COUNTY_20':'geofips'})
vcols = [c for c in cty.columns if c.endswith('_usd_mn') and c!='gdp_usd_mn']
m = cty[['geofips','year','ytd_through']+vcols].merge(rel, on='geofips')
for c in vcols: m[c] = m[c]*m.w
dist = m.groupby(['cd_geoid','year','ytd_through'], as_index=False)[vcols].sum()
# industry contributions for CD: aggregate county contributions with the same weights
ic = pd.read_csv(CLEAN/'county_shift_share_industries.csv', dtype={'geofips':str,'naics4':str}).merge(rel, on='geofips'); ic['value_usd_mn']*=ic.w; ic['emp']*=ic.w
icd = ic.groupby(['cd_geoid','flow','partner','year','naics4','naics_desc'], as_index=False)[['emp','value_usd_mn']].sum()
icd = icd.sort_values('value_usd_mn', ascending=False).groupby(['cd_geoid','flow','partner','year']).head(6); icd.to_csv(CLEAN/'district_shift_share_industries.csv', index=False)
FIPS2ST = {'01':'AL','02':'AK','04':'AZ','05':'AR','06':'CA','08':'CO','09':'CT','10':'DE','11':'DC','12':'FL','13':'GA','15':'HI','16':'ID','17':'IL','18':'IN','19':'IA','20':'KS','21':'KY','22':'LA','23':'ME','24':'MD','25':'MA','26':'MI','27':'MN','28':'MS','29':'MO','30':'MT','31':'NE','32':'NV','33':'NH','34':'NJ','35':'NM','36':'NY','37':'NC','38':'ND','39':'OH','40':'OK','41':'OR','42':'PA','44':'RI','45':'SC','46':'SD','47':'TN','48':'TX','49':'UT','50':'VT','51':'VA','53':'WA','54':'WV','55':'WI','56':'WY'}
dist['state'] = dist.cd_geoid.str[:2].map(FIPS2ST); dist = dist[dist.state.notna()]; dist['district'] = dist.cd_geoid.str[2:]
dist['code'] = dist.state + '-' + dist.district.replace({'00':'AL','98':'AL'})
cdemp = pd.read_csv(CLEAN/'cbp2023_cd_naics.csv', dtype=str); cdemp['cd_geoid']=cdemp.state.str.zfill(2)+cdemp['congressional district'].str.zfill(2)
emp_cd = cdemp[cdemp.NAICS2017=='00'].set_index('cd_geoid').EMP.astype(float); dist['emp_total_2023'] = dist.cd_geoid.map(emp_cd)
for pn in ['china','taiwan']:
    for f in ['exports','imports']:
        c=f'{f}_{pn}_usd_mn'
        if c in dist: dist[f'{f}_{pn}_per_worker'] = dist[c]*1e6/dist.emp_total_2023
dist.to_csv(CLEAN/'district_shift_share.csv', index=False)
# ---- 校驗 1：郡加總 vs Census 州級觀測值（起運州）；校驗 2：選區 shift-share vs USCBC 2024
p = pd.read_csv(CLEAN/'panel_state_year.csv')
chk = cty.groupby(['state','year'])[['exports_china_usd_mn','imports_china_usd_mn']].sum().reset_index().merge(p[['state','year','exports_china_usd_mn','imports_china_usd_mn']], on=['state','year'], suffixes=('_ss','_census'))
chk24 = chk[chk.year==2024]; print('State-level check 2024: corr exports', round(chk24.exports_china_usd_mn_ss.corr(chk24.exports_china_usd_mn_census),3), 'imports', round(chk24.imports_china_usd_mn_ss.corr(chk24.imports_china_usd_mn_census),3))
print('  national sum ss vs census (bn):', round(chk24.exports_china_usd_mn_ss.sum()/1e3,1), round(chk24.exports_china_usd_mn_census.sum()/1e3,1))
u = pd.read_csv(CLEAN/'district_uscbc_2025.csv'); u=u[u.unit=='district']
d24 = dist[dist.year==2024].merge(u[['code','goods_exports_china_2024_usd_mn','jobs_supported_2023']], on='code', how='inner')
print('District check 2024: n', len(d24), 'corr(shift-share, USCBC)', round(d24.exports_china_usd_mn.corr(d24.goods_exports_china_2024_usd_mn),3), 'rank corr', round(d24.exports_china_usd_mn.corr(d24.goods_exports_china_2024_usd_mn, method='spearman'),3))
chk.to_csv(CLEAN/'validation_shift_share_state.csv', index=False); d24.to_csv(CLEAN/'validation_shift_share_district.csv', index=False)
print(cty[cty.year==2024].sort_values('exports_china_pct_gdp',ascending=False).head(8)[['county_name','exports_china_usd_mn','exports_china_pct_gdp','imports_china_pct_gdp','gdp_usd_mn']].round(2).to_string(index=False))
