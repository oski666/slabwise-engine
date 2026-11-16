# Protocol §67b (D307): §67 pairs re-judged with the same-era rule. Reads <work>/pairs.json of scripts/ja_twin_match.py.
import json,random,os,sys
sys.path.insert(0,'/home/claude/slabwise-engine')
from slabwise.series import series_of
from PIL import Image
W='/home/claude/work/twins/'
d=json.load(open(W+'pairs.json'))
same=lambda r: series_of(r['ja'])==series_of(r['en'])
seen={(r['en'],r['ja']) for r in json.load(open(W+'g3_M0.json'))}|{(r['en'],r['ja']) for r in json.load(open(W+'g3_M1.json'))}
res={}
for v,ix in (('M0',0),('M1',1)):
    g1=[r['d'][ix]<=80 for r in d.values() if r['kind']=='G1' and r['d']]
    g2=[r['d'][ix]<=80 for r in d.values() if r['kind']=='G2' and r['d'] and same(r)]
    best={}
    for r in d.values():
        if r['kind']=='new' and r['d'] and same(r) and r['d'][ix]<=80:
            if r['ja'] not in best or r['d'][ix]<best[r['ja']]['d'][ix]: best[r['ja']]=r
    links=sorted(best.values(),key=lambda r:(r['en'],r['ja']))
    json.dump(links,open(W+f'links67b_{v}.json','w'),indent=1)
    res[v]=dict(G1=round(sum(g1)/len(g1),4),G2=round(sum(g2)/max(1,len(g2)),4),G2_n=len(g2),new_links=len(links),new_en=len({r['en'] for r in links}))
print(json.dumps(res,indent=1))
json.dump(res,open('/home/claude/slabwise-engine/results/ja_twins/summary_67b.json','w'),indent=1)
