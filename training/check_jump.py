"""Independent jump timestep and perturbation checks; no upright gate."""
import argparse,json,hashlib
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from jump import ROOT,evaluate


def run(task):
    name,p,kw=task
    r=evaluate(p,**kw)
    return dict(name=name,metrics=r,whole_robot_airborne=bool(r['score_m']>.001 and r['warnings']==0))


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--policy',type=Path,default=ROOT/'training/policies/jump.json');ap.add_argument('--out',type=Path,default=ROOT/'training/results/jump_validation.json');args=ap.parse_args()
    path=args.policy.resolve();p=np.array(json.loads(path.read_text())['parameters'])
    tasks=[('nominal',p,{}),('half_timestep',p,dict(timestep=.0005)),('quarter_timestep',p,dict(timestep=.00025)),
           ('friction_0_5',p,dict(friction=.5)),('friction_1_1',p,dict(friction=1.1)),('payload_200g',p,dict(payload=.2))]
    with ProcessPoolExecutor(6) as pool:rows=list(pool.map(run,tasks))
    report=dict(policy=str(path.relative_to(ROOT)),policy_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                scope='Timestep conditions diagnose the maximum-height policy and were used to select the robust policy; friction and payload are additional checks. No landing or upright requirement.',cases=rows)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    for r in rows:print(r['name'],r['whole_robot_airborne'],r['metrics']['peak_whole_robot_clearance_m'],flush=True)


if __name__=='__main__':main()
