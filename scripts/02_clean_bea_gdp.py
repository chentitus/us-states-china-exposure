"""BEA SAGDP1：各州 GDP（current dollars，百萬美元）2020–2025。"""
import zipfile, io, pandas as pd
from common import *
z=zipfile.ZipFile(RAW/'bea/SAGDP.zip'); f=[n for n in z.namelist() if n.startswith('SAGDP1__ALL_AREAS')][0]
d=pd.read_csv(io.BytesIO(z.read(f)), encoding='latin-1')
d=d[(d['Description'].str.contains('Current-dollar GDP',na=False))&(d['Unit'].str.contains('Millions',na=False))]
NAME2ABBR={v:k for k,v in STATES.items()}
d['state']=d['GeoName'].str.strip().map(NAME2ABBR); d=d[d.state.notna()]
yrs=[c for c in d.columns if c.isdigit() and 2018<=int(c)<=2026]
g=d.melt(id_vars=['state'],value_vars=yrs,var_name='year',value_name='gdp_usd_mn'); g['year']=g.year.astype(int); g['gdp_usd_mn']=pd.to_numeric(g.gdp_usd_mn,errors='coerce')
g.to_csv(CLEAN/'bea_state_gdp.csv',index=False); print(g.pivot(index='state',columns='year',values='gdp_usd_mn').loc[['TX','CA','WY']].round(0)); print('states',g.state.nunique(), 'years', sorted(g.year.unique()))
