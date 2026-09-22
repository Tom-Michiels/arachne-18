"""Coordinate refinement of jump timing/poses, using the same whole-robot score."""
from concurrent.futures import ProcessPoolExecutor
import json
import numpy as np
from jump import ROOT,LOW,HIGH,evaluate


def robust(p):
    rows=[evaluate(p,timestep=dt) for dt in [.001,.0005,.00025]]
    nominal=rows[0].copy();nominal['timestep_checks']=rows
    nominal['robust_score_m']=min(r['score_m'] for r in rows)
    return nominal


def main():
    path=ROOT/'training/policies/jump.json';policy=json.loads(path.read_text());p=np.array(policy['parameters'])
    if len(p)!=13:raise ValueError('This local refinement expects the symmetric checkpoint')
    best=robust(p);history=[]
    with ProcessPoolExecutor(8) as pool:
        for fraction in [.025,.012,.006,.003]:
            for sweep in range(2):
                candidates=[p.copy()]
                for j in range(len(p)):
                    for k in [-2,-1,1,2]:
                        q=p.copy();q[j]=np.clip(q[j]+k*fraction*(HIGH[j]-LOW[j]),LOW[j],HIGH[j]);candidates.append(q)
                rows=list(pool.map(robust,candidates));i=max(range(len(rows)),key=lambda i:rows[i]['robust_score_m'])
                p=candidates[i];best=rows[i];history.append(dict(fraction=fraction,sweep=sweep,score_m=best['robust_score_m']))
                policy.update(parameters=p.tolist(),metrics=best,selection='CEM followed by coordinate refinement of whole-robot clearance across 1, 0.5 and 0.25 ms physics steps')
                path.write_text(json.dumps(policy,indent=2)+'\n')
                print(fraction,sweep,best['robust_score_m']*100,flush=True)
    (ROOT/'training/runs/jump/robust_refinement.json').write_text(json.dumps(history,indent=2)+'\n')


if __name__=='__main__':main()
