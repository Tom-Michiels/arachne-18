"""Initial forward obstacle assessment; this does not promote curriculum stages."""
import json,time,hashlib
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from gait import ROOT,load
from evaluate import evaluate
from curriculum import gate

def run(task):
 i,seed=task;c=json.loads((ROOT/'training/obstacle_curriculum.json').read_text());s=c['stages'][i]
 t=time.time();r=evaluate(load(ROOT/'training/policies/omni.json'),[.1,0,0],12.,terrain=s['terrain'],seed=seed)
 return dict(stage=s['name'],seed=seed,failures=gate(r,s,c),metrics=r,wall_seconds=time.time()-t)
if __name__=='__main__':
 with ProcessPoolExecutor(4) as p:r=list(p.map(run,[(i,s) for i in [1,2,3,4] for s in [701,702,703]]))
 (ROOT/'training/results/obstacle_admission.json').write_text(json.dumps(dict(status='Initial forward assessment; not curriculum promotion',policy='training/policies/omni.json',policy_sha256=hashlib.sha256((ROOT/'training/policies/omni.json').read_bytes()).hexdigest(),cases=r),indent=2)+'\n')
 for a in r:print(a['stage'],a['seed'],a['failures'],a['metrics']['rock_foot_contact_steps'],a['metrics']['vegetation_contact_steps'],a['wall_seconds'],flush=True)
