import pandas as pd, json
from common import *
u = pd.read_csv(CLEAN/'district_uscbc_2025.csv'); pr = pd.read_csv(CLEAN/'district_uscbc_2025_top_products.csv')
ss = pd.read_csv(CLEAN/'district_shift_share.csv', dtype={'cd_geoid':str,'district':str,'code':str}); ind_cd = pd.read_csv(CLEAN/'district_shift_share_industries.csv', dtype={'cd_geoid':str,'naics4':str})
cty = pd.read_csv(CLEAN/'county_shift_share.csv', dtype={'geofips':str}); ind_cty = pd.read_csv(CLEAN/'county_shift_share_industries.csv', dtype={'geofips':str,'naics4':str})
FIPS = {v:k for k,v in {'AL':'01','AK':'02','AZ':'04','AR':'05','CA':'06','CO':'08','CT':'09','DE':'10','DC':'11','FL':'12','GA':'13','HI':'15','ID':'16','IL':'17','IN':'18','IA':'19','KS':'20','KY':'21','LA':'22','ME':'23','MD':'24','MA':'25','MI':'26','MN':'27','MS':'28','MO':'29','MT':'30','NE':'31','NV':'32','NH':'33','NJ':'34','NM':'35','NY':'36','NC':'37','ND':'38','OH':'39','OK':'40','OR':'41','PA':'42','RI':'44','SC':'45','SD':'46','TN':'47','TX':'48','UT':'49','VT':'50','VA':'51','WA':'53','WV':'54','WI':'55','WY':'56'}.items()}
ST2FIPS = {v:k for k,v in FIPS.items()}
# USCBC district rows (at-large states: use state page as the district)
d = u[u.unit=='district'].copy(); al = u[(u.unit=='state')&(~u.state.isin(d.state.unique()))].copy(); al['code']=al.state+'-AL'; al['district']='AL'; d = pd.concat([d, al])
def geoid(code):
    s,n = code.split('-'); return ST2FIPS.get(s,'')+('00' if n=='AL' else n.zfill(2))
d['geoid'] = d.code.map(geoid)
emp = ss.drop_duplicates('cd_geoid').set_index('cd_geoid').emp_total_2023
CDrows = [{'code':r.code,'geoid':r.geoid,'state':r.state,'name':getattr(r,'name'),'u_goods':r.goods_exports_china_2024_usd_mn,'u_goods_share':r.goods_china_share_2024_pct,'u_goods_rank':r.goods_china_rank_2024,'u_goods_chg':r.goods_change_2023_2024_pct,'u_services':r.services_exports_china_2023_usd_mn,'u_services_share':r.services_china_share_2023_pct,'u_jobs':r.jobs_supported_2023,'emp':emp.get(r.geoid)} for r in d.itertuples()]
CDrows = pd.DataFrame(CDrows).astype(object).where(pd.notna(pd.DataFrame(CDrows)), None).to_dict('records')
SS_CD = {}
for r in ss.itertuples():
    code = r.state+'-'+('AL' if r.district in ('00','98') else r.district)
    SS_CD.setdefault(code, {})[int(r.year)] = {'ec':round(r.exports_china_usd_mn,2),'ic':round(r.imports_china_usd_mn,2),'et':round(getattr(r,'exports_taiwan_usd_mn',0) or 0,2),'it':round(getattr(r,'imports_taiwan_usd_mn',0) or 0,2)}
PROD = {}
for r in pr[pr.unit!='x'].itertuples():
    code = r.code if '-' in r.code else r.code+'-AL'
    PROD.setdefault(code, []).append([r.kind, int(r.rank), r.product, r.value_usd_mn])
def indmap(df, key, codef):
    m={}
    for r in df.sort_values(['year','flow','partner','value_usd_mn'],ascending=[True,True,True,False]).itertuples():
        m.setdefault(codef(r), []).append([r.flow, r.partner, int(r.year), r.naics4, (r.naics_desc or '')[:50], int(r.emp) if pd.notna(r.emp) else None, round(r.value_usd_mn,2)])
    return m
IND_CD = indmap(ind_cd, 'cd_geoid', lambda r: FIPS.get(r.cd_geoid[:2],'')+'-'+('AL' if r.cd_geoid[2:] in ('00','98') else r.cd_geoid[2:]))
IND_CTY = indmap(ind_cty, 'geofips', lambda r: r.geofips)
CTYrows = []
keep = ['exports_china_usd_mn','imports_china_usd_mn','exports_taiwan_usd_mn','imports_taiwan_usd_mn','exports_china_pct_gdp','imports_china_pct_gdp','exports_taiwan_pct_gdp','imports_taiwan_pct_gdp','exports_china_per_worker','imports_china_per_worker','gdp_usd_mn']
for g, grp in cty.groupby('geofips'):
    r0 = grp.iloc[0]; y = {}
    for r in grp.itertuples():
        y[int(r.year)] = {k: (None if pd.isna(getattr(r,k,None)) else round(float(getattr(r,k)),3)) for k in keep if hasattr(r,k)}
    CTYrows.append({'geofips':g,'name':r0.county_name,'state':r0.state,'emp_total_2023':None if pd.isna(r0.emp_total_2023) else int(r0.emp_total_2023),'y':y})
chk = pd.read_csv(CLEAN/'validation_shift_share_state.csv'); chk = chk[chk.year==2024]
STCHK = [{'state':r.state,'ss':round(r.exports_china_usd_mn_ss,1),'census':round(r.exports_china_usd_mn_census,1)} for r in chk.itertuples()]
years = sorted(int(y) for y in ss.year.unique()); latest = {'year': years[-1], 'month': int(ss[ss.year==years[-1]].ytd_through.iloc[0])}
js = ('const CD='+json.dumps(CDrows,ensure_ascii=False,separators=(',',':'))+';\nconst SS_CD='+json.dumps(SS_CD,separators=(',',':'))+';\nconst PROD='+json.dumps(PROD,ensure_ascii=False,separators=(',',':'))+';\nconst IND_CD='+json.dumps(IND_CD,ensure_ascii=False,separators=(',',':'))+';\nconst IND_CTY='+json.dumps(IND_CTY,ensure_ascii=False,separators=(',',':'))+';\nconst CTY='+json.dumps(CTYrows,ensure_ascii=False,separators=(',',':'))+';\nconst STCHK='+json.dumps(STCHK)+';\nconst YEARS='+json.dumps(years)+';\nconst LATEST='+json.dumps(latest)+';\nconst GEO_CD='+(CLEAN/'geo_cd119.geojson').read_text()+';\nconst GEO_CTY='+(CLEAN/'geo_county.geojson').read_text()+';\nconst STATES='+json.dumps(STATES,ensure_ascii=False)+';\nconst STATES_ZH='+json.dumps(STATES_ZH,ensure_ascii=False)+';\nconst ABOUT='+json.dumps((SCRIPTS/'dashboard_districts_about.html').read_text(encoding='utf-8'),ensure_ascii=False)+';')
html = (SCRIPTS/'dashboard_districts_template.html').read_text(encoding='utf-8').replace('/*__DATA__*/', js)
(ROOT/'dashboard/districts.html').write_text(html, encoding='utf-8'); print('dashboard/districts.html', round((ROOT/'dashboard/districts.html').stat().st_size/1e6,1),'MB; CD rows',len(CDrows),'counties',len(CTYrows))
