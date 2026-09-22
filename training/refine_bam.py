"""Refine a GPU-trained gait against the full reference BAM actuator model."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import time
import numpy as np
from gait import ROOT,LOW,HIGH,load,save
from evaluate import evaluate


def score(r):
    if not r['passed'] or r['warnings']:return -100.
    stride=r['body_distance_per_cycle_m'] or 0.
    return float(5*np.exp(-r['velocity_rmse']**2/.0025)
        +3*np.exp(-r['yaw_rmse']**2/.0064)+2*np.clip(stride/.12,0,1)
        -90*np.deg2rad(r['tilt_rms_deg'])**2-10*r['body_rp_rate_rms']**2
        -80*r['vertical_velocity_rms']**2-80*r['slip_rms_m_s']**2
        -1.5*(.025*r['target_rate_rms']**2+.00015*r['target_acceleration_rms']**2)
        -8e-8*r['target_jerk_rms']**2
        -2*max(r['slip_rms_m_s']/.055-1,0)-2*max(r['target_jerk_rms']/3000-1,0))


def worker(task):
    params,command,seconds,friction=task
    r=evaluate(params,command,seconds,friction=friction)
    return score(r),r


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--resume',type=Path,required=True)
    ap.add_argument('--out',type=Path,default=ROOT/'training/runs/bam-refinement')
    ap.add_argument('--population',type=int,default=24)
    ap.add_argument('--generations',type=int,default=12)
    ap.add_argument('--workers',type=int,default=8)
    ap.add_argument('--seconds',type=float,default=6.)
    ap.add_argument('--speed',type=float,default=.26)
    ap.add_argument('--seed',type=int,default=303)
    ap.add_argument('--robust',action='store_true',help='Include opposite directions, low friction, and a faster forward command')
    args=ap.parse_args()
    if args.population<8 or args.generations<1 or args.seconds<4:ap.error('population >= 8, generations >= 1, seconds >= 4 required')
    args.out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(args.seed);best=load(args.resume);mean=best.copy()
    # Seed a second candidate with the yaw gain of the already verified general
    # policy. The GPU's static servo approximation underestimates yaw loss.
    mean[4]=max(mean[4],load(ROOT/'training/policies/omni.json')[4])
    std=(HIGH-LOW)*.06
    v=args.speed
    commands=[[v,0,0],[0,v,0],[-v,0,0],[v/np.sqrt(2),v/np.sqrt(2),0],
              [0,0,.35],[0,0,-.35],[.18,.04,.25]]
    frictions=[None]*len(commands)
    if args.robust:
        commands.extend([[0,-v,0],[-v/np.sqrt(2),-v/np.sqrt(2),0],[.26,0,0],[v,0,0]])
        frictions.extend([None,None,None,.5])
    config=dict(vars(args),commands=commands,frictions=frictions,source_sha256={name:hashlib.sha256((ROOT/'training'/name).read_bytes()).hexdigest()
                for name in ['refine_bam.py','evaluate.py','gait.py']})
    (args.out/'config.json').write_text(json.dumps(config,default=str,indent=2)+'\n')
    best_score=-np.inf;start=time.time()
    with ProcessPoolExecutor(args.workers,mp_context=mp.get_context('spawn')) as pool:
        for gen in range(args.generations):
            pop=np.clip(rng.normal(mean,std,(args.population,len(mean))),LOW,HIGH)
            pop[0]=best;pop[1]=mean
            raw=list(pool.map(worker,[(p,c,args.seconds,f) for p in pop for c,f in zip(commands,frictions)]))
            scores=np.array([r[0] for r in raw]).reshape(-1,len(commands))
            scores=.7*scores.mean(1)+.3*scores.min(1)
            elite=np.argsort(scores)[-max(4,args.population//4):]
            mean=.25*mean+.75*pop[elite].mean(0)
            std=np.maximum(.35*std+.65*pop[elite].std(0),(HIGH-LOW)*.008)
            winner=int(np.argmax(scores))
            if scores[winner]>best_score:
                best_score=float(scores[winner]);best=pop[winner].copy()
                save(args.out/'policy.json',best,stage='long-stride omni BAM refinement',
                     score=best_score,generation=gen,seed=args.seed,commands=commands,
                     simulator='Original MuJoCo C with full BAM M6')
            record=dict(generation=gen,best=best_score,mean=float(scores.mean()),
                        elapsed=time.time()-start,policy=best.tolist(),
                        winner_metrics=[r[1] for r in raw[winner*len(commands):(winner+1)*len(commands)]])
            with (args.out/'log.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
            print(gen,'best',round(best_score,4),'elapsed',round(time.time()-start,1),flush=True)


if __name__=='__main__':main()
