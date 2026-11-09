"""依日期歸屬：每件提案（提出日）、共提（共提日）、發言（日期）歸到議員「當時」代表的州與選區（依 congress-legislators 任期）。
曝險只接第 119 屆邊界一致的任期：眾議員任期起始 ≥ 2025-01-03，或 2023-01-03 起且州不在 2024 年重劃名單（AL、GA、LA、NC、NY）。其餘標示 boundary = 'pre2023' 或 '118_redrawn'，不接選區曝險。參議員一律接州。
輸出 congress_events.csv、congress_districts.csv（以第 119 屆選區彙總 2023–2026 所有代表該區的議員）；並改寫 congress_members.csv 的選區曝險對接。"""
import pandas as pd, numpy as np
from common import *
REDRAWN_2024 = {'AL','GA','LA','NC','NY'}
T = pd.read_csv(CLEAN/'legislators_terms_2019_2026.csv'); T['start']=pd.to_datetime(T.start); T['end']=pd.to_datetime(T.end)
B = pd.read_csv(CLEAN/'congress_bills.csv'); B['introduced']=pd.to_datetime(B.introduced); B=B[B.introduced>='2019-01-03']
C = pd.read_csv(CLEAN/'congress_cosponsors.csv'); C=C[C.withdrawn.isna()]; C['date']=pd.to_datetime(C.date)
G = pd.read_csv(CLEAN/'crec_granules.csv'); SP = pd.read_csv(CLEAN/'crec_speakers.csv')
S = SP[SP.role=='SPEAKING'].merge(G[['granuleId','china','taiwan','date']], on='granuleId').drop_duplicates(['granuleId','bioguide']); S['date']=pd.to_datetime(S.date)
ev = pd.concat([
  B.rename(columns={'sponsor_bioguide':'bioguide','introduced':'date'})[['bioguide','date','bill_id','china','taiwan']].assign(kind='sponsor'),
  C.merge(B[['bill_id','china','taiwan']], on='bill_id')[['bioguide','date','bill_id','china','taiwan']].assign(kind='cosponsor'),
  S.rename(columns={'granuleId':'bill_id'})[['bioguide','date','bill_id','china','taiwan']].assign(kind='speech')], ignore_index=True).dropna(subset=['bioguide','date'])
# 依日期找任期
ev = ev.merge(T[['bioguide','chamber','state','district','start','end']], on='bioguide', how='left')
ev = ev[(ev.date>=ev.start)&(ev.date<ev.end)].drop_duplicates(['bioguide','kind','bill_id'])
def bnd(r):
    if r.chamber=='sen': return 'state'
    if r.start>=pd.Timestamp('2025-01-03'): return '119'
    if r.start>=pd.Timestamp('2023-01-03'): return '118_redrawn' if r.state in REDRAWN_2024 else '119'
    return 'pre2023'
ev['boundary'] = [bnd(r) for r in ev.itertuples()]
ev['cd_code'] = [f"{s}-{'AL' if int(d)==0 else str(int(d)).zfill(2)}" if c=='rep' and pd.notna(d) else None for s,d,c in zip(ev.state,ev.district,ev.chamber)]
ev['year'] = ev.date.dt.year
ev.drop(columns=['start','end']).to_csv(CLEAN/'congress_events.csv', index=False)
print('events', len(ev), ev.groupby(['kind','boundary']).size().unstack(fill_value=0).to_dict())
# ---- members：曝險只接 119 邊界一致的最後任期
M = pd.read_csv(CLEAN/'congress_members.csv'); Tl = T.sort_values('start').groupby('bioguide').tail(1).set_index('bioguide')
M['last_term_start'] = M.bioguide.map(Tl.start)
M['boundary'] = [('state' if c=='sen' else ('119' if s>=pd.Timestamp('2025-01-03') else ('118_redrawn' if st in REDRAWN_2024 else '119') if s>=pd.Timestamp('2023-01-03') else 'pre2023')) for c,s,st in zip(M.chamber,M.last_term_start,M.state)]
for c in ['u_goods_2024','u_goods_share_2024','u_jobs_2023','ss_exp_cn_pw_2024','ss_exp_tw_pw_2024','ss_ratio_cn_tw_2024']: M.loc[M.boundary!='119', c] = np.nan
print('members exposure-linked (House):', ((M.chamber=='rep')&M.u_goods_2024.notna()).sum(), '| blanked:', ((M.chamber=='rep')&(M.boundary!='119')).sum())
M.drop(columns=['last_term_start']).to_csv(CLEAN/'congress_members.csv', index=False)
# ---- districts：第 119 屆選區 × 2023–2026 所有代表（邊界一致的事件）
E = ev[(ev.chamber=='rep')&(ev.boundary=='119')]
agg = E.groupby('cd_code').apply(lambda g: pd.Series({
  'sponsored_china': int(((g.kind=='sponsor')&g.china).sum()), 'sponsored_taiwan': int(((g.kind=='sponsor')&g.taiwan).sum()),
  'cosponsored_china': int(((g.kind=='cosponsor')&g.china).sum()), 'cosponsored_taiwan': int(((g.kind=='cosponsor')&g.taiwan).sum()),
  'speeches_china': int(((g.kind=='speech')&g.china).sum()), 'speeches_taiwan': int(((g.kind=='speech')&g.taiwan).sum())}), include_groups=False)
TT = T[(T.chamber=='rep')&(T.end>pd.Timestamp('2023-01-03'))].copy(); TT['cd_code']=[f"{s}-{'AL' if int(d)==0 else str(int(d)).zfill(2)}" for s,d in zip(TT.state,TT.district)]
TT['ok'] = [(s>=pd.Timestamp('2025-01-03')) or (st not in REDRAWN_2024) for s,st in zip(TT.start,TT.state)]; TT=TT[TT.ok]
reps = TT.sort_values('start').groupby('cd_code').apply(lambda g: list(dict.fromkeys(g.bioguide)), include_groups=False).rename('members')
D = pd.DataFrame({'cd_code': sorted(set(TT.cd_code))}).set_index('cd_code').join(reps).join(agg).fillna({c:0 for c in agg.columns})
D['n_members'] = D.members.map(len); D['changed'] = D.n_members>1
MM = M.set_index('bioguide'); X = M[M.boundary=='119'].dropna(subset=['cd_code']).drop_duplicates('cd_code').set_index('cd_code')
for c in ['u_goods_2024','u_goods_share_2024','u_jobs_2023','ss_exp_cn_pw_2024','ss_exp_tw_pw_2024','ss_ratio_cn_tw_2024']: D[c] = D.index.map(X[c])
D['members'] = D.members.map(lambda L: ';'.join(L))
D.reset_index().to_csv(CLEAN/'congress_districts.csv', index=False)
print('districts', len(D), '| changed rep since 2023', int(D.changed.sum()), '| with exposure', D.u_goods_2024.notna().sum())
