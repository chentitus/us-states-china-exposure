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
NETS = json.loads((CLEAN/'congress_networks_taiwan.json').read_text())   # by chamber x Congress (17_congress_networks.py)
DD = pd.read_csv(CLEAN/'congress_districts.csv'); DIST = [{k: nn(v) for k,v in r.items()} for r in DD.round(3).to_dict('records')]
EV = pd.read_csv(CLEAN/'congress_events.csv', parse_dates=['date']); E = EV[(EV.chamber=='rep')&(EV.boundary=='119')]
TT = pd.read_csv(CLEAN/'legislators_terms_2019_2026.csv'); TT = TT[(TT.chamber=='rep')&(TT.end>'2023-01-03')]; TT['cd_code']=[f"{s}-{'AL' if int(d)==0 else str(int(d)).zfill(2)}" for s,d in zip(TT.state,TT.district)]
span = TT.groupby(['cd_code','bioguide']).agg(a=('start','min'), b=('end','max'))
EVD = {}
for (cd,bg), g in E.groupby(['cd_code','bioguide']):
    EVD.setdefault(cd,{})[bg] = {'sc':int(((g.kind=='sponsor')&g.china).sum()),'st':int(((g.kind=='sponsor')&g.taiwan).sum()),'cc':int(((g.kind=='cosponsor')&g.china).sum()),'ct':int(((g.kind=='cosponsor')&g.taiwan).sum()),'pc':int(((g.kind=='speech')&g.china).sum()),'pt':int(((g.kind=='speech')&g.taiwan).sum())}
for (cd,bg), r in span.iterrows(): EVD.setdefault(cd,{}).setdefault(bg,{})['span'] = f"{str(r.a)[:7]}–{min(str(r.b)[:7],'2026-11')}" 
js = 'const MEM='+json.dumps(MEM,ensure_ascii=False,separators=(',',':'))+';\nconst BILLS='+json.dumps(BILLS,ensure_ascii=False,separators=(',',':'))+';\nconst COS='+json.dumps(COS,separators=(',',':'))+';\nconst SPEECH='+json.dumps(SPEECH,ensure_ascii=False,separators=(',',':'))+';\nconst NETS='+json.dumps(NETS,ensure_ascii=False,separators=(',',':'))+';\nconst DIST='+json.dumps(DIST,ensure_ascii=False,separators=(',',':'))+';\nconst EVD='+json.dumps(EVD,separators=(',',':'))+';\nconst STATES_ZH='+json.dumps(STATES_ZH,ensure_ascii=False)+';\nconst ABOUT='+json.dumps((SCRIPTS/'dashboard_congress_about.html').read_text(encoding='utf-8'),ensure_ascii=False)+';'
html = (SCRIPTS/'dashboard_congress_template.html').read_text(encoding='utf-8').replace('/*__DATA__*/', js)
(ROOT/'dashboard/congress.html').write_text(html, encoding='utf-8'); print('dashboard/congress.html', round((ROOT/'dashboard/congress.html').stat().st_size/1e6,1),'MB; members',len(MEM),'bills',len(BILLS),'speech rows',len(SPEECH))
