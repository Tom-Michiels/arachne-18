"""Forward CEM refinement using reference MuJoCo/BAM and unchanged speed gates."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import numpy as np
from gait import ROOT, LOW, HIGH, load, save
from evaluate import evaluate
from benchmark_speed import passes


def run(task):
    p,command=task
    r=evaluate(p,[command,0,0],6.)
    penalties=sum(max(0,r[k]/limit-1)**2 for k,limit in [
        ('velocity_rmse',.065),('yaw_rmse',.12),('tilt_rms_deg',.75),
        ('slip_rms_m_s',.055),('target_acceleration_rms',60),
        ('target_jerk_rms',3000),('joint_speed_max',4.8)])
    score=r['measured_velocity'][0]+r['foot_excursion_mean_m']-3*penalties-10*(not r['passed'])
    return dict(parameters=p.tolist(),metrics=r,passed=passes(r),score=score)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--resume',type=Path,default=ROOT/'training/policies/long_stride.json')
    ap.add_argument('--broad',action='store_true')
    ap.add_argument('--command',type=float,default=.34)
    ap.add_argument('--generations',type=int,default=10)
    ap.add_argument('--population',type=int,default=160)
    ap.add_argument('--workers',type=int,default=8)
    ap.add_argument('--out',type=Path,default=ROOT/'training/runs/sprint')
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(981);mean=load(args.resume)
    if args.broad and len(mean)==12:mean=np.r_[mean,1.]
    broad=len(mean)==13
    low=np.r_[LOW,0.] if broad else LOW;high=np.r_[HIGH,1.] if broad else HIGH
    sd=np.array([.25,.03,.004,.16,.01,.004,.005,.09,.015,.015,.015,.02]+([.15] if broad else []))
    floor=np.array([.02,.003,.0005,.01,.002,.0005,.0005,.01,.002,.002,.002,.003]+([.03] if broad else []))
    save(args.out/'initial.json',mean,command_m_s=args.command)
    allrows=[]
    with ProcessPoolExecutor(args.workers) as pool:
        for generation in range(args.generations):
            population=np.clip(rng.normal(mean,sd,(args.population,len(mean))),low,high)
            population[0]=mean
            rows=list(pool.map(run,[(p,args.command) for p in population]));allrows+=rows
            elite=sorted(rows,key=lambda r:r['score'],reverse=True)[:20]
            a=np.array([r['parameters'] for r in elite]);mean=.2*mean+.8*a.mean(0)
            sd=np.maximum(.7*a.std(0)+.3*sd,floor)
            good=sorted([r for r in allrows if r['passed']],key=lambda r:r['score'],reverse=True)
            (args.out/'search.json').write_text(json.dumps(allrows)+'\n')
            if good:save(args.out/'policy.json',good[0]['parameters'],command_m_s=args.command)
            print(generation,'best',elite[0]['score'],'feasible',len(good),flush=True)


if __name__=='__main__':main()
