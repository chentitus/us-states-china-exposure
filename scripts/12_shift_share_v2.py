"""Shift-share v2。
郡：L_{g,i} = BLS QCEW 2024 年均就業（county × NAICS4，private，agglvl 76/own 5；含農場受雇者），QCEW 揭露抑制（N）時以 CBP 2023 補；全國 L_i = QCEW agglvl 16/own 5。
選區：L_{cd,i} = Σ_ZIP [ZBP 2023 設立數_{zip,i} × 全國每設立平均就業_i (CBP US)] × ZCTA 在選區的土地面積占比（Census rel2020 cd119–zcta）；全國 L_i 用同一 ZBP 估計加總，使各選區加總 = 全國可配置額。
X_i(y) = 全國對中／台出口、進口（NAICS4）。"""
import pandas as pd, numpy as np, zipfile, io
from common import *
tr = pd.read_csv(CLEAN/'naics_national_trade.csv', dtype={'naics4':str}); desc = tr.drop_duplicates('naics4').set_index('naics4').naics_desc
def run(L, key, Lnat, tag):
    """L: DataFrame[key, naics4, emp]; Lnat: Series naics4→national emp. 回傳年度曝險與產業貢獻。"""
    g = L[L.emp>0].copy(); g['L_us']=g.naics4.map(g.groupby('naics4').emp.sum()); g=g[g.L_us>0]; g['w']=g.emp/g.L_us   # 權重以各地區加總為分母，使每個產業的配置額加總 = 全國值（Lnat 僅供涵蓋率參考）
    out=[]; contrib=[]
    for (flow,pn,y,ytd), t in tr.groupby(['flow','partner','year','ytd_through']):
        x=t.set_index('naics4').value_usd; gg=g.assign(v=g.naics4.map(x).fillna(0)*g.w)
        out.append(gg.groupby(key).v.sum().rename(f'{flow}_{pn}_usd_mn').div(1e6).to_frame().assign(year=y,ytd_through=ytd).reset_index())
        if y in (2024,2025) and pn in ('china','taiwan'):
            top=gg[gg.v>0].sort_values('v',ascending=False).groupby(key).head(6)
            contrib.append(top.assign(flow=flow,partner=pn,year=y,value_usd_mn=top.v/1e6,naics_desc=top.naics4.map(desc))[[key,'flow','partner','year','naics4','naics_desc','emp','value_usd_mn']])
    res=out[0]
    for o in out[1:]: res=res.merge(o,how='outer')
    res=res.groupby([key,'year','ytd_through'],as_index=False).first()
    pd.concat(contrib).to_csv(CLEAN/f'{tag}_shift_share_industries.csv',index=False)
    return res
# ---------- QCEW
z=zipfile.ZipFile(RAW/'qcew/2024_annual_singlefile.zip'); q=pd.read_csv(z.open(z.namelist()[0]), dtype=str, usecols=['area_fips','own_code','industry_code','agglvl_code','disclosure_code','annual_avg_emplvl'])
q['emp']=pd.to_numeric(q.annual_avg_emplvl,errors='coerce').fillna(0)
nat=q[(q.agglvl_code=='16')&(q.own_code=='5')].set_index('industry_code').emp
cq=q[(q.agglvl_code=='76')&(q.own_code=='5')][['area_fips','industry_code','emp','disclosure_code']].rename(columns={'area_fips':'geofips','industry_code':'naics4'})
cb=pd.read_csv(CLEAN/'cbp2023_county_naics.csv',dtype={'NAICS2017':str,'state':str,'county':str}); cb=cb[cb.NAICS2017.str.len()==4]; cb['geofips']=cb.state.str.zfill(2)+cb.county.str.zfill(3); cb['emp_cbp']=pd.to_numeric(cb.EMP,errors='coerce')
cq=cq.merge(cb[['geofips','NAICS2017','emp_cbp']].rename(columns={'NAICS2017':'naics4'}),how='outer',on=['geofips','naics4'])
cq['emp']=np.where((cq.disclosure_code=='N')|cq.emp.isna()|(cq.emp==0), cq.emp_cbp.fillna(0), cq.emp)   # 抑制或缺 → CBP
cq=cq[cq.geofips.str[:2]<'57']
supp=(cq.disclosure_code=='N').mean(); print(f'QCEW county cells suppressed: {supp:.1%} (filled with CBP)')
cty=run(cq[['geofips','naics4','emp']], 'geofips', nat, 'county')
gdp=pd.read_csv(CLEAN/'bea_county_gdp.csv',dtype={'geofips':str}); gdp['gdp_usd_mn']=gdp.gdp_usd_k/1000
g24=gdp[gdp.year==2024][['geofips','gdp_usd_mn']]; gdpy=pd.concat([gdp[gdp.year<=2023][['geofips','year','gdp_usd_mn']],g24.assign(year=2024),g24.assign(year=2025),g24.assign(year=2026)])
cty=cty.merge(gdpy,how='left',on=['geofips','year']); names=gdp.drop_duplicates('geofips').set_index('geofips').geoname; cty['county_name']=cty.geofips.map(names); cty['state']=cty.county_name.str.extract(r', ([A-Z]{2})')[0]
cty['emp_total_2023']=cty.geofips.map(cq.groupby('geofips').emp.sum())
for pn in ['china','taiwan']:
    for f in ['exports','imports']:
        c=f'{f}_{pn}_usd_mn'; cty[f'{f}_{pn}_pct_gdp']=cty[c]/cty.gdp_usd_mn*100; cty[f'{f}_{pn}_per_worker']=cty[c]*1e6/cty.emp_total_2023
cty.to_csv(CLEAN/'county_shift_share.csv',index=False)
# ---------- ZBP → CD119
zb=pd.read_csv(zipfile.ZipFile(RAW/'zbp/zbp23detail.zip').open('zbp23detail.txt'),dtype=str,usecols=['zip','naics','est'])
zb=zb[zb.naics.str.match(r'^\d{4}//$')]; zb['naics4']=zb.naics.str[:4]; zb['est']=pd.to_numeric(zb.est,errors='coerce').fillna(0)
us=pd.read_csv(CLEAN/'cbp2023_us_naics.csv',dtype={'NAICS2017':str}); us=us[us.NAICS2017.str.len()==4]; epe=(pd.to_numeric(us.EMP,errors='coerce')/pd.to_numeric(us.ESTAB,errors='coerce')).set_axis(us.NAICS2017)
zb['emp']=zb.est*zb.naics4.map(epe).fillna(0)
rel=pd.read_csv(RAW/'geo/rel/tab20_cd11920_zcta520_natl.txt',sep='|',dtype=str,encoding='utf-8-sig'); rel=rel[rel.GEOID_ZCTA5_20.notna()&(rel.GEOID_ZCTA5_20!='')]
rel['w']=rel.AREALAND_PART.astype(float)/rel.AREALAND_ZCTA5_20.astype(float).replace(0,np.nan); rel=rel[rel.w>0][['GEOID_CD119_20','GEOID_ZCTA5_20','w']].rename(columns={'GEOID_CD119_20':'cd_geoid','GEOID_ZCTA5_20':'zip'})
m=zb.merge(rel,on='zip'); m['emp']*=m.w; print(f'ZBP zips matched to ZCTA/CD: {zb.zip.nunique()} zips, {m.zip.nunique()} matched; emp matched {m.emp.sum()/zb.emp.sum():.1%}')
Lcd=m.groupby(['cd_geoid','naics4'],as_index=False).emp.sum(); Lnat_zbp=zb.groupby('naics4').emp.sum()
dist=run(Lcd,'cd_geoid',Lnat_zbp,'district')
FIPS2ST={'01':'AL','02':'AK','04':'AZ','05':'AR','06':'CA','08':'CO','09':'CT','10':'DE','11':'DC','12':'FL','13':'GA','15':'HI','16':'ID','17':'IL','18':'IN','19':'IA','20':'KS','21':'KY','22':'LA','23':'ME','24':'MD','25':'MA','26':'MI','27':'MN','28':'MS','29':'MO','30':'MT','31':'NE','32':'NV','33':'NH','34':'NJ','35':'NM','36':'NY','37':'NC','38':'ND','39':'OH','40':'OK','41':'OR','42':'PA','44':'RI','45':'SC','46':'SD','47':'TN','48':'TX','49':'UT','50':'VT','51':'VA','53':'WA','54':'WV','55':'WI','56':'WY'}
dist['state']=dist.cd_geoid.str[:2].map(FIPS2ST); dist=dist[dist.state.notna()]; dist['district']=dist.cd_geoid.str[2:]; dist['code']=dist.state+'-'+dist.district.replace({'00':'AL','98':'AL'})
dist['emp_total_2023']=dist.cd_geoid.map(Lcd.groupby('cd_geoid').emp.sum())
for pn in ['china','taiwan']:
    for f in ['exports','imports']:
        c=f'{f}_{pn}_usd_mn'; dist[f'{f}_{pn}_per_worker']=dist[c]*1e6/dist.emp_total_2023
dist.to_csv(CLEAN/'district_shift_share.csv',index=False)
# ---------- 校驗
p=pd.read_csv(CLEAN/'panel_state_year.csv')
chk=cty.groupby(['state','year'])[['exports_china_usd_mn','imports_china_usd_mn']].sum().reset_index().merge(p[['state','year','exports_china_usd_mn','imports_china_usd_mn']],on=['state','year'],suffixes=('_ss','_census'))
c24=chk[chk.year==2024]; print('State check 2024: corr exports',round(c24.exports_china_usd_mn_ss.corr(c24.exports_china_usd_mn_census),3),'imports',round(c24.imports_china_usd_mn_ss.corr(c24.imports_china_usd_mn_census),3),'| sum ss',round(c24.exports_china_usd_mn_ss.sum()/1e3,1),'census',round(c24.exports_china_usd_mn_census.sum()/1e3,1))
t24=tr[(tr.flow=='exports')&(tr.partner=='china')&(tr.year==2024)]; print('coverage (QCEW nat>0):', round(t24[t24.naics4.isin(nat[nat>0].index)].value_usd.sum()/t24.value_usd.sum(),3), '| (ZBP nat>0):', round(t24[t24.naics4.isin(Lnat_zbp[Lnat_zbp>0].index)].value_usd.sum()/t24.value_usd.sum(),3))
u=pd.read_csv(CLEAN/'district_uscbc_2025.csv'); u=u[u.unit=='district']
d24=dist[dist.year==2024].merge(u[['code','goods_exports_china_2024_usd_mn','jobs_supported_2023']],on='code')
print('District check 2024: n',len(d24),'Pearson',round(d24.exports_china_usd_mn.corr(d24.goods_exports_china_2024_usd_mn),3),'Spearman',round(d24.exports_china_usd_mn.corr(d24.goods_exports_china_2024_usd_mn,method='spearman'),3),'| ratio median',round((d24.goods_exports_china_2024_usd_mn/d24.exports_china_usd_mn).median(),2))
chk.to_csv(CLEAN/'validation_shift_share_state.csv',index=False); d24.to_csv(CLEAN/'validation_shift_share_district.csv',index=False)
print(cty[(cty.year==2024)&(cty.emp_total_2023>=5000)].sort_values('exports_china_pct_gdp',ascending=False).head(8)[['county_name','exports_china_usd_mn','exports_china_pct_gdp','gdp_usd_mn','emp_total_2023']].round(2).to_string(index=False))
