"""Shift-share 輸入：(1) 全國對中國出口／進口按 NAICS 4 位碼（Census naics 端點，2020–2025＋2026 YTD）；(2) CBP 2023 郡×NAICS4、國會選區×NAICS4 就業；(3) BEA 郡 GDP（CAGDP2）。"""
import json, time, requests, pandas as pd
from common import *
K = env('CENSUS_API_KEY'); B = env('BEA_API_KEY')
def get(url, params, f, tries=6):
    if f.exists(): return json.loads(f.read_text())
    for i in range(tries):
        try:
            r = requests.get(url, params=params, timeout=600)
            if r.status_code == 200: f.write_text(r.text); return r.json()
            if r.status_code == 204: f.write_text('[]'); return []
        except requests.exceptions.RequestException as e: print('retry', f.name, e.__class__.__name__)
        time.sleep(30*(i+1))
    raise RuntimeError(f.name)
# (1) 全國 × NAICS4 貿易（statenaics 端點，STATE='-'；全州查詢會逾時），2020–2025＋2026 YTD
rows=[]
for flow,val in [('exports','ALL_VAL_YR'),('imports','GEN_VAL_YR')]:
    for cty,pn in [('5700','china'),('5830','taiwan'),('-','world')]:
        for t in ['2020-12','2021-12','2022-12','2023-12','2024-12','2025-12','2026-09']:
            d = get(f'https://api.census.gov/data/timeseries/intltrade/{flow}/statenaics', {'get':f'NAICS,NAICS_LDESC,{val}','COMM_LVL':'NA4','CTY_CODE':cty,'STATE':'-','time':t,'key':K}, RAW/'naics'/f'{flow}_{pn}_natNA4_{t}.json')
            if d: rows += [{'flow':flow,'partner':pn,'naics4':r[0],'naics_desc':r[1],'year':int(t[:4]),'ytd_through':t[5:],'value_usd':float(r[2])} for r in d[1:]]
            print(flow,pn,t,len(d)-1 if d else 0, flush=True)
pd.DataFrame(rows).to_csv(CLEAN/'naics_national_trade.csv', index=False)
# (1b) 全國 CBP 2023 NAICS4 就業（shift-share 分母）
d = get('https://api.census.gov/data/2023/cbp', {'get':'NAICS2017,NAICS2017_LABEL,EMP,ESTAB,PAYANN','for':'us:*','key':K}, RAW/'cbp'/'cbp2023_us.json')
pd.DataFrame([dict(zip(d[0],r)) for r in d[1:]]).to_csv(CLEAN/'cbp2023_us_naics.csv', index=False); print('cbp us', len(d)-1, flush=True)
# (2) CBP 2023 county & CD × NAICS4
for geo,name in [('county:*','county'),('congressional district:*','cd')]:
    out=[]
    for st in sorted({k for k in STATES if k not in ('PR','VI')}|{'DC'}):
        fips = {'AL':'01','AK':'02','AZ':'04','AR':'05','CA':'06','CO':'08','CT':'09','DE':'10','DC':'11','FL':'12','GA':'13','HI':'15','ID':'16','IL':'17','IN':'18','IA':'19','KS':'20','KY':'21','LA':'22','ME':'23','MD':'24','MA':'25','MI':'26','MN':'27','MS':'28','MO':'29','MT':'30','NE':'31','NV':'32','NH':'33','NJ':'34','NM':'35','NY':'36','NC':'37','ND':'38','OH':'39','OK':'40','OR':'41','PA':'42','RI':'44','SC':'45','SD':'46','TN':'47','TX':'48','UT':'49','VT':'50','VA':'51','WA':'53','WV':'54','WI':'55','WY':'56'}[st]
        d = get('https://api.census.gov/data/2023/cbp', {'get':'NAICS2017,NAICS2017_LABEL,EMP,ESTAB,PAYANN','for':geo,'in':f'state:{fips}','key':K}, RAW/'cbp'/f'cbp2023_{name}_{st}.json')
        if d: h=d[0]; out += [dict(zip(h,r)) for r in d[1:]]
        print('cbp',name,st,len(d)-1 if d else 0, flush=True)
    pd.DataFrame(out).to_csv(CLEAN/f'cbp2023_{name}_naics.csv', index=False)
# (3) BEA county GDP
rows=[]
for y in [2020,2021,2022,2023,2024]:
    d = get('https://apps.bea.gov/api/data/', {'UserID':B,'method':'GetData','DatasetName':'Regional','TableName':'CAGDP2','LineCode':1,'GeoFips':'COUNTY','Year':y,'ResultFormat':'JSON'}, RAW/'bea'/f'cagdp2_{y}.json')
    for r in d['BEAAPI']['Results'].get('Data',[]): rows.append({'geofips':r['GeoFips'],'geoname':r['GeoName'],'year':y,'gdp_usd_k':pd.to_numeric(r['DataValue'].replace(',',''),errors='coerce')})
pd.DataFrame(rows).to_csv(CLEAN/'bea_county_gdp.csv', index=False); print('done')
