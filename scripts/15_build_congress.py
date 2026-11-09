"""議員×法案×國會記錄 → congress_members.csv、congress_network_taiwan.json、dashboard/congress.html。選區對接：眾議員用其最近一屆（第 119 屆優先）的州＋選區接 USCBC／shift-share；參議員接州級指標。"""
import pandas as pd, numpy as np, json, networkx as nx
from common import *
B = pd.read_csv(CLEAN/'congress_bills.csv'); C = pd.read_csv(CLEAN/'congress_cosponsors.csv'); T = pd.read_csv(CLEAN/'legislators_terms_2019_2026.csv')
G = pd.read_csv(CLEAN/'crec_granules.csv'); SP = pd.read_csv(CLEAN/'crec_speakers.csv')
B['introduced'] = pd.to_datetime(B.introduced); B = B[B.introduced >= '2019-01-03']
# ---- member master: latest term on/after 2019
T = T.sort_values(['bioguide','start']); last = T.groupby('bioguide').tail(1).set_index('bioguide')
cur119 = T[(T.start<='2026-11-01')&(T.end>'2025-01-03')].groupby('bioguide').tail(1).set_index('bioguide')
def code(st, d, ch): 
    if ch!='rep' or pd.isna(d): return None
    return f"{st}-{'AL' if int(d)==0 else str(int(d)).zfill(2)}"
M = pd.DataFrame({'name': last.name, 'last': last['last'], 'chamber': last.chamber, 'party': last.party, 'state': last.state, 'district': last.district, 'term_end': last.end})
M['in_119th'] = M.index.isin(cur119.index); M['cd_code'] = [code(s,d,c) for s,d,c in zip(M.state, M.district, M.chamber)]
# ---- bills
sp = B.groupby('sponsor_bioguide').agg(sponsored_china=('china','sum'), sponsored_taiwan=('taiwan','sum'), sponsored_any=('bill_id','count'), sponsored_law=('law', lambda s: s.notna().sum()))
C = C[C.withdrawn.isna()].merge(B[['bill_id','china','taiwan','sponsor_party','sponsor_bioguide']], on='bill_id'); C['cross_party'] = C.party != C.sponsor_party
co = C.groupby('bioguide').agg(cosponsored_china=('china','sum'), cosponsored_taiwan=('taiwan','sum'), cosponsored_any=('bill_id','count'), cosponsored_cross_party=('cross_party','sum'))
# ---- CREC speeches (role SPEAKING only)
S = SP[SP.role=='SPEAKING'].merge(G[['granuleId','china','taiwan','date','title','snippet','packageId','n_china','n_taiwan']], on='granuleId')
S = S.drop_duplicates(['granuleId','bioguide'])
spk = S.groupby('bioguide').agg(speeches_china=('china','sum'), speeches_taiwan=('taiwan','sum'), speeches_any=('granuleId','count'))
M = M.join(sp).join(co).join(spk); M = M.fillna({c:0 for c in M.columns if c.startswith(('sponsored','cosponsored','speeches'))})
for c in [c for c in M.columns if c.startswith(('sponsored','cosponsored','speeches'))]: M[c] = M[c].astype(int)
M['cross_party_share'] = (M.cosponsored_cross_party/M.cosponsored_any).round(3)
# ---- exposure join
U = pd.read_csv(CLEAN/'district_uscbc_2025.csv'); U = U[U.unit=='district']; al = pd.read_csv(CLEAN/'district_uscbc_2025.csv'); al = al[(al.unit=='state')&(~al.state.isin(U.state.unique()))].copy(); al['code'] = al.state+'-AL'; U = pd.concat([U, al])
D = pd.read_csv(CLEAN/'district_shift_share.csv', dtype={'code':str}); D24 = D[D.year==2024].set_index('code')
P = pd.read_csv(CLEAN/'panel_state_year.csv'); P24 = P[P.year==2024].set_index('state')
M['u_goods_2024'] = M.cd_code.map(U.set_index('code').goods_exports_china_2024_usd_mn); M['u_goods_share_2024'] = M.cd_code.map(U.set_index('code').goods_china_share_2024_pct); M['u_jobs_2023'] = M.cd_code.map(U.set_index('code').jobs_supported_2023)
M['ss_exp_cn_pw_2024'] = M.cd_code.map(D24.exports_china_per_worker); M['ss_exp_tw_pw_2024'] = M.cd_code.map(D24.exports_taiwan_per_worker); M['ss_ratio_cn_tw_2024'] = M.cd_code.map(D24.exports_china_usd_mn/D24.exports_taiwan_usd_mn)
sen = M.chamber=='sen'
M.loc[sen,'st_exp_cn_pct_gdp_2024'] = M.loc[sen,'state'].map(P24.exports_china_pct_gdp); M.loc[sen,'st_exp_cn_share_2024'] = M.loc[sen,'state'].map(P24.exports_china_share); M.loc[sen,'st_exp_tw_pct_gdp_2024'] = M.loc[sen,'state'].map(P24.exports_taiwan_pct_gdp)
M = M.reset_index().rename(columns={'index':'bioguide'}); M.to_csv(CLEAN/'congress_members.csv', index=False)
# ---- cosponsorship network (Taiwan bills, 116–119)
TB = B[B.taiwan]; E = {}
for bid, grp in C[C.bill_id.isin(TB.bill_id)].groupby('bill_id'):
    s = TB.set_index('bill_id').sponsor_bioguide.get(bid); nodes = [s] + grp.bioguide.tolist() if isinstance(s,str) else grp.bioguide.tolist()
    for a in nodes:
        for b in nodes:
            if a < b: E[(a,b)] = E.get((a,b),0)+1
Gx = nx.Graph(); 
for (a,b),w in E.items(): Gx.add_edge(a,b,weight=w)
deg = dict(Gx.degree(weight='weight')); keep = [n for n,d in sorted(deg.items(), key=lambda x:-x[1])[:220]]; H = Gx.subgraph(keep)
pos = nx.spring_layout(H, weight='weight', seed=7, k=0.35)
MM = M.set_index('bioguide')
net = {'nodes': [{'id':n,'x':round(float(pos[n][0]),3),'y':round(float(pos[n][1]),3),'name':MM.name.get(n,n),'party':MM.party.get(n,''),'state':MM.state.get(n,''),'chamber':MM.chamber.get(n,''),'deg':int(deg[n]),'tw_sp':int(MM.sponsored_taiwan.get(n,0)),'tw_co':int(MM.cosponsored_taiwan.get(n,0))} for n in H.nodes()],
       'edges': [{'s':a,'t':b,'w':int(d['weight'])} for a,b,d in H.edges(data=True) if d['weight']>=2]}
(CLEAN/'congress_network_taiwan.json').write_text(json.dumps(net))
print('members', len(M), '| bills', len(B), 'china', B.china.sum(), 'taiwan', B.taiwan.sum(), 'laws', B.law.notna().sum(), '| cosponsorships', len(C), '| speech rows', len(S), 'speakers', S.bioguide.nunique(), '| network nodes', H.number_of_nodes(), 'edges', len(net['edges']))
print(M.sort_values('sponsored_taiwan',ascending=False).head(8)[['name','party','state','chamber','cd_code','sponsored_taiwan','cosponsored_taiwan','speeches_taiwan','sponsored_china','speeches_china']].to_string(index=False))
