"""USCBC 2025 State Export Report（文字版）：各州對中服務出口前 10（2023）、商品出口前 10（2024）、產品別報復關稅曝險前 10（2025-04）。全州服務出口只有地圖圖像，無法取得。"""
import re, pandas as pd
from common import *
t=(RAW/'uscbc/USCBC_2025_Export_Report_text.txt').read_text().replace('T exas','Texas').replace('New Y ork','New York')
NAME2ABBR={v:k for k,v in STATES.items()}
def table(after, n=10, pat=r'^\d+\.\s+([A-Za-z ]+?)\s+\$([\d.]+)\s*(billion|million)\s+(−|–|-)?([\d.]+)%'):
    i=t.index(after); rows=[]
    for line in t[i:].splitlines()[1:60]:
        m=re.match(pat, line.strip())
        if m:
            name=m.group(1).strip(); v=float(m.group(2))*(1000 if m.group(3)=='billion' else 1); g=float(m.group(5))*(-1 if m.group(4) else 1)
            rows.append({'state':NAME2ABBR.get(name,name),'state_name':name,'value_usd_mn':v,'growth_yoy_pct':g})
        if len(rows)>=n: break
    return pd.DataFrame(rows)
svc=table('Top services exporters to China by state, 2023'); svc['year']=2023; svc['measure']='services_exports_to_china'
goods=table('Top goods exporters to China by state, 2024'); goods['year']=2024; goods['measure']='goods_exports_to_china_uscbc'
tar=[]; i=t.index('Exposure to Chinese product-specific retaliatory tariffs by state')
for line in t[i:].splitlines()[1:40]:
    m=re.match(r'^\d+\.\s+([A-Za-z ]+?)\s+\$([\d.]+)\s*billion\s+([\d.]+)%', line.strip())
    if m: tar.append({'state':NAME2ABBR[m.group(1).strip()],'state_name':m.group(1).strip(),'exports_subject_to_product_tariffs_usd_mn':float(m.group(2))*1000,'share_of_china_exports_pct':float(m.group(3)),'year':2025,'measure':'retaliatory_tariff_exposure'})
tar=pd.DataFrame(tar)
out=pd.concat([svc,goods,tar],ignore_index=True); out.to_csv(CLEAN/'uscbc_state_tables.csv',index=False)
print(svc.to_string(index=False)); print(tar.to_string(index=False))
