"""AFIDA 2024 年報 Report 11（中國投資者持有美國農地，按州×郡）→ 各州中國持有英畝數。來源：pdftotext -layout 第 256–290 頁。"""
import re, pandas as pd
from common import *
txt = (RAW/'afida/AFIDA_2024_Report_p256-290_layout.txt').read_text()
NAME2ABBR = {v:k for k,v in STATES.items()}
rows=[]; cur=None
for line in txt.splitlines():
    s=line.strip()
    m=re.match(r'^(New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|South Carolina|South Dakota|West Virginia|Rhode Island|Puerto Rico|[A-Z][a-z]+)\s{2,}\S', s)
    if m and m.group(1) in NAME2ABBR: cur=m.group(1)
    if s.startswith('State Totals:') and cur:
        nums=[int(x.replace(',','')) for x in re.findall(r'[\d,]+', s)]
        if len(nums)>=6: rows.append({'state':NAME2ABBR[cur],'state_name':cur,'china_cropland':nums[0],'china_pasture':nums[1],'china_forest':nums[2],'china_other_ag':nums[3],'china_non_ag':nums[4],'china_total_acres':nums[5]})
        cur=None
df=pd.DataFrame(rows).groupby(['state','state_name'],as_index=False).sum()
df['china_ag_acres']=df.china_total_acres-df.china_non_ag
df.to_csv(CLEAN/'afida_china_land_by_state_2024.csv',index=False)
print(df.sort_values('china_total_acres',ascending=False).head(8).to_string(index=False)); print('states',len(df),'total acres',df.china_total_acres.sum())
