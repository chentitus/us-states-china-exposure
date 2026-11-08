import pandas as pd, json
from common import *
P = pd.read_csv(CLEAN/'panel_state_year.csv'); T = pd.read_csv(CLEAN/'top_products_state_year.csv', dtype={'hs':str}); S = pd.read_csv(CLEAN/'summary_state.csv')
for d in (P,T,S):
    for c in d.columns:
        if d[c].dtype==float: d[c]=d[c].round(4)
latest = P[P.year==P.year.max()].iloc[0]; latest_info = {'year': int(latest.year), 'month': int(latest.ytd_through)}
js = {'panel': P.astype(object).where(P.notna(),None).to_dict('records'), 'top': T.astype(object).where(T.notna(),None).to_dict('records'), 'summary': S.astype(object).where(S.notna(),None).to_dict('records'),
      'years': sorted(int(y) for y in P.year.unique()), 'latest': latest_info, 'about': (SCRIPTS/'dashboard_about.html').read_text(encoding='utf-8')}
html = (SCRIPTS/'dashboard_template.html').read_text(encoding='utf-8').replace('/*__DATA__*/', 'const DATA = '+json.dumps(js, ensure_ascii=False, separators=(',',':'))+';\nconst STATES='+json.dumps(STATES, ensure_ascii=False)+';\nconst STATES_ZH='+json.dumps(STATES_ZH, ensure_ascii=False)+';')
(ROOT/'dashboard/index.html').write_text(html, encoding='utf-8'); print('dashboard/index.html', round((ROOT/'dashboard/index.html').stat().st_size/1e6,2), 'MB')
