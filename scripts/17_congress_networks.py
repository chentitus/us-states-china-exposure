"""涉台法案共同提案網絡，依議院 × 屆別分開（第 116–119 屆與合併）→ data/clean/congress_networks_taiwan.json。
邊：兩位議員同時是同一件涉台法案的提案人或共同提案人（撤回者不計），權重＝共同出現的法案件數。
眾議院：hr、hres、hjres、hconres；參議院：s、sres、sjres、sconres。
顯示門檻（為了可讀性）：單屆邊權重 ≥ 2、合併各屆 ≥ 3；眾議院再取加權連結度前 100 名；去掉沒有邊的節點。
版面：networkx spring_layout（seed 7）。另算每個網絡的跨黨邊比例。"""
import pandas as pd, json, networkx as nx
from common import *
M = pd.read_csv(CLEAN/'congress_members.csv').set_index('bioguide')
B = pd.read_csv(CLEAN/'congress_bills.csv'); B = B[B.taiwan & (pd.to_datetime(B.introduced) >= '2019-01-03')]
C = pd.read_csv(CLEAN/'congress_cosponsors.csv'); C = C[C.withdrawn.isna()]
HOUSE = {'hr', 'hres', 'hjres', 'hconres'}
out = {}
for ch in ['house', 'senate']:
    Bc = B[B.type.isin(HOUSE) if ch == 'house' else ~B.type.isin(HOUSE)]
    for cg in [116, 117, 118, 119, 'all']:
        Bx = Bc if cg == 'all' else Bc[Bc.congress == cg]
        E, n_bills = {}, {}
        for r in Bx.itertuples():
            ppl = set(C[C.bill_id == r.bill_id].bioguide) | ({r.sponsor_bioguide} if isinstance(r.sponsor_bioguide, str) else set())
            for p in ppl: n_bills[p] = n_bills.get(p, 0) + 1
            ppl = sorted(ppl)
            for i, a in enumerate(ppl):
                for b in ppl[i + 1:]: E[(a, b)] = E.get((a, b), 0) + 1
        G = nx.Graph()
        for (a, b), w in E.items(): G.add_edge(a, b, weight=w)
        if G.number_of_nodes() == 0:
            out[f'{ch}_{cg}'] = {'nodes': [], 'edges': [], 'n_bills': int(len(Bx))}; continue
        deg = dict(G.degree(weight='weight'))
        keep = [n for n, _ in sorted(deg.items(), key=lambda x: -x[1])[:100]] if ch == 'house' else list(G.nodes())
        wmin = 3 if cg == 'all' else 2
        H = G.subgraph(keep).copy(); H.remove_edges_from([(a, b) for a, b, d in H.edges(data=True) if d['weight'] < wmin]); H.remove_nodes_from([n for n in list(H.nodes()) if H.degree(n) == 0])
        pos = nx.spring_layout(H, weight='weight', seed=7, k=0.5 if ch == 'senate' else 0.35)
        party = lambda n: M.party.get(n, '')
        edges = [{'s': a, 't': b, 'w': int(d['weight'])} for a, b, d in H.edges(data=True)]
        cross = sum(party(e['s']) != party(e['t']) for e in edges)
        out[f'{ch}_{cg}'] = {'n_bills': int(len(Bx)), 'cross_share': round(cross / len(edges), 3) if edges else None,
            'nodes': [{'id': n, 'x': round(float(pos[n][0]), 3), 'y': round(float(pos[n][1]), 3), 'name': M.name.get(n, n), 'party': party(n),
                       'state': M.state.get(n, ''), 'deg': int(deg[n]), 'nb': int(n_bills.get(n, 0))} for n in H.nodes()], 'edges': edges}
        print(ch, cg, 'bills', len(Bx), 'nodes', H.number_of_nodes(), 'edges', len(edges), 'cross', out[f'{ch}_{cg}']['cross_share'])
(CLEAN/'congress_networks_taiwan.json').write_text(json.dumps(out, ensure_ascii=False))
