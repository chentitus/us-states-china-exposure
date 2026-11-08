"""USCBC 2025（Trade Partnership Worldwide 估計）各州＋各國會選區一頁式 PDF → district_uscbc_2025.csv。
每頁：商品出口到中國（2024）、服務出口到中國（2023）、支撐就業、中國占該區全球出口比、前五大出口市場（含中國名次）、前五大對中出口商品／服務。總額以「出口市場」清單中 China 列為準（即使名次 >5 也會列出）。"""
import re, subprocess, pandas as pd
from common import *
NAME2ABBR = {v:k for k,v in STATES.items()}
def money(s):
    m=re.search(r'\$([\d.,]+)\s*(billion|million)', s); 
    return None if not m else float(m.group(1).replace(',',''))*(1000 if m.group(2)=='billion' else 1)
rows=[]; prods=[]
for pdf in sorted((RAW/'uscbc2025_states').glob('*.pdf')):
    txt = subprocess.run(['pdftotext','-raw',str(pdf),'-'],capture_output=True,text=True).stdout
    for pg in txt.split('\f'):
        if 'Exports to China' not in pg: continue
        head = pg.strip().splitlines()[0]
        m = re.match(r"^(.+?)'s? (?:(\d+)(?:st|nd|rd|th) District|(At-Large) District)? ?Exports to China", head)
        if not m: print('skip head:', head[:60]); continue
        sname = m.group(1).strip(); st = NAME2ABBR.get(sname, NAME2ABBR.get(sname.replace("'",""), sname))
        dist = m.group(2) or ('AL' if m.group(3) else None)
        unit = 'state' if dist is None else 'district'; code = st if dist is None else f'{st}-{dist.zfill(2) if dist.isdigit() else dist}'
        jobs = re.search(r'supported\s+([\d,]+)\s+American', pg); jobs = int(jobs.group(1).replace(',','')) if jobs else None
        gchg = re.search(r'(?:Change|Growth) \(2023-2024\): (-?\d+)%', pg); schg = re.search(r'(?:Change|Growth) \(2022-2023\): (-?\d+)%', pg)
        gsh = re.search(r'(\d+)% of .*? global goods exports', pg); ssh = re.search(r'(\d+)% of .*? global services exports', pg)
        # sections
        def section(title_a, title_b):
            i = pg.find(title_a); j = pg.find(title_b, i+1) if title_b else len(pg)
            return pg[i:j] if i>=0 else ''
        # lists appear after headers in raw order: goods markets, goods to China, services to China, services markets (order varies) → parse all numbered lines and assign by position
        lines = [l for l in pg.splitlines() if re.match(r'^\d+\. ', l)]
        blocks=[]; cur=[]; last=0
        for l in lines:
            n=int(l.split('.')[0])
            if cur and n<=last: blocks.append(cur); cur=[]
            cur.append(l); last=n
        if cur: blocks.append(cur)
        # identify blocks: market blocks contain 'China'; product blocks don't
        mkts=[b for b in blocks if any(' China ' in x or x.endswith(' China') or 'China $' in x for x in b)]
        prodb=[b for b in blocks if b not in mkts]
        gm = mkts[0] if len(mkts)>0 else []; sm = mkts[1] if len(mkts)>1 else []
        gp = prodb[0] if len(prodb)>0 else []; sp = prodb[1] if len(prodb)>1 else []
        def china_row(b):
            for x in b:
                mm=re.match(r'^(\d+)\. China (\$.+)$', x)
                if mm: return int(mm.group(1)), money(mm.group(2))
            return None, None
        grank, gval = china_row(gm); srank, sval = china_row(sm)
        rows.append({'unit':unit,'code':code,'state':st,'district':dist,'name':head.replace(' Exports to China','').strip(),
            'goods_exports_china_2024_usd_mn':gval,'goods_china_rank_2024':grank,'goods_change_2023_2024_pct':int(gchg.group(1)) if gchg else None,'goods_china_share_2024_pct':int(gsh.group(1)) if gsh else None,
            'services_exports_china_2023_usd_mn':sval,'services_china_rank_2023':srank,'services_change_2022_2023_pct':int(schg.group(1)) if schg else None,'services_china_share_2023_pct':int(ssh.group(1)) if ssh else None,
            'jobs_supported_2023':jobs,'top_goods_market_2024':gm[0].split('. ',1)[1].rsplit(' $',1)[0] if gm else None})
        for kind,b in [('goods',gp),('services',sp)]:
            for x in b:
                mm=re.match(r'^(\d+)\. (.+?) (\$[\d.,]+ (?:billion|million))$', x)
                if mm: prods.append({'code':code,'unit':unit,'kind':kind,'rank':int(mm.group(1)),'product':mm.group(2),'value_usd_mn':money(mm.group(3))})
df=pd.DataFrame(rows); pr=pd.DataFrame(prods)
df.to_csv(CLEAN/'district_uscbc_2025.csv',index=False); pr.to_csv(CLEAN/'district_uscbc_2025_top_products.csv',index=False)
d=df[df.unit=='district']; print('states',(df.unit=='state').sum(),'districts',len(d),'| goods value missing',d.goods_exports_china_2024_usd_mn.isna().sum(),'services missing',d.services_exports_china_2023_usd_mn.isna().sum())
print('sum district goods (bn):',round(d.goods_exports_china_2024_usd_mn.sum()/1000,1),'| sum state pages:',round(df[df.unit=='state'].goods_exports_china_2024_usd_mn.sum()/1000,1))
print(d.sort_values('goods_exports_china_2024_usd_mn',ascending=False).head(12)[['code','goods_exports_china_2024_usd_mn','goods_china_share_2024_pct','services_exports_china_2023_usd_mn','jobs_supported_2023','top_goods_market_2024']].to_string(index=False))
print(pr[pr.code=='TX-01'])
