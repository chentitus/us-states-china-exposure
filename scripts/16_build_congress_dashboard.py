import pandas as pd, json
from common import *
M = pd.read_csv(CLEAN/'congress_members.csv'); B = pd.read_csv(CLEAN/'congress_bills.csv'); C = pd.read_csv(CLEAN/'congress_cosponsors.csv'); G = pd.read_csv(CLEAN/'crec_granules.csv'); SP = pd.read_csv(CLEAN/'crec_speakers.csv')
B['introduced'] = pd.to_datetime(B.introduced); B = B[B.introduced >= '2019-01-03']
C = C[C.withdrawn.isna()].merge(B[['bill_id','sponsor_party']], on='bill_id'); C['cross'] = C.party != C.sponsor_party
ncross = C.groupby('bill_id').cross.sum()
def nn(v): return None if (v is None or (isinstance(v,float) and pd.isna(v))) else v
MEM = [{k: nn(v) for k,v in r.items()} for r in M.round(3).to_dict('records')]
BILLS = [{'id':r.bill_id,'congress':int(r.congress),'type':r.type,'number':int(r.number),'introduced':str(r.introduced.date()),'title':(r.title or '')[:220],'china':bool(r.china),'taiwan':bool(r.taiwan),'sponsor':nn(r.sponsor_bioguide),'sponsor_name':nn(r.sponsor_name),'sponsor_party':{'D':'Democrat','R':'Republican','I':'Independent'}.get(r.sponsor_party, r.sponsor_party),'n_cos':int(r.n_cosponsors),'n_cross':int(ncross.get(r.bill_id,0)),'policy':nn(r.policy_area),'law':nn(r.law),'latest':nn(r.latest_action),'url':r.url} for r in B.itertuples()]
COS = {}
for r in C.itertuples(): COS.setdefault(r.bioguide, []).append(r.bill_id)
S = SP[SP.role=='SPEAKING'].merge(G[['granuleId','china','taiwan','date','title','snippet','packageId']], on='granuleId').drop_duplicates(['granuleId','bioguide'])
SPEECH = [{'b':r.bioguide,'g':r.granuleId,'pkg':r.packageId,'date':str(r.date)[:10],'title':(r.title or '')[:120],'cn':bool(r.china),'tw':bool(r.taiwan),'snip':(r.snippet if isinstance(r.snippet,str) else '')[:400]} for r in S.itertuples()]
NET = json.loads((CLEAN/'congress_network_taiwan.json').read_text())
js = 'const MEM='+json.dumps(MEM,ensure_ascii=False,separators=(',',':'))+';\nconst BILLS='+json.dumps(BILLS,ensure_ascii=False,separators=(',',':'))+';\nconst COS='+json.dumps(COS,separators=(',',':'))+';\nconst SPEECH='+json.dumps(SPEECH,ensure_ascii=False,separators=(',',':'))+';\nconst NET='+json.dumps(NET,ensure_ascii=False,separators=(',',':'))+';\nconst STATES_ZH='+json.dumps(STATES_ZH,ensure_ascii=False)+';\nconst ABOUT='+json.dumps((SCRIPTS/'dashboard_congress_about.html').read_text(encoding='utf-8'),ensure_ascii=False)+';'
html = (SCRIPTS/'dashboard_congress_template.html').read_text(encoding='utf-8').replace('/*__DATA__*/', js)
(ROOT/'dashboard/congress.html').write_text(html, encoding='utf-8'); print('dashboard/congress.html', round((ROOT/'dashboard/congress.html').stat().st_size/1e6,1),'MB; members',len(MEM),'bills',len(BILLS),'speech rows',len(SPEECH))
