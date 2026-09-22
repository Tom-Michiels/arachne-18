"""Select a feasible reference-refined checkpoint before the full speed audit."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from itertools import product
import json
import multiprocessing as mp
from pathlib import Path
import numpy as np
from evaluate import evaluate
from benchmark_speed import passes
from gait import ROOT,LOW,HIGH,save


def worker(task):
    p,command,kw=task
    return evaluate(p,command,12.,**kw)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--runs',nargs='+',type=Path,required=True)
    ap.add_argument('--workers',type=int,default=8)
    ap.add_argument('--out',type=Path,default=ROOT/'training/results/stride_selection.json')
    ap.add_argument('--policy',type=Path,default=ROOT/'training/policies/long_stride.json')
    ap.add_argument('--local-grid',action='store_true',help='Refine the closest feasible checkpoint with small cadence/lift/stride changes')
    args=ap.parse_args();candidates=[];seen=set()
    for run in args.runs:
        for row in map(json.loads,(run/'log.jsonl').read_text().splitlines()):
            p=row['policy'];key=tuple(p)
            if key in seen:continue
            seen.add(key);candidates.append(dict(run=str(run),generation=row['generation'],parameters=p))
    angle=np.deg2rad(247.5)
    cases=[([.26,0,0],{}),([.24,0,0],dict(friction=.5)),([0,.24,0],{}),
           ([.24*np.cos(angle),.24*np.sin(angle),0],{}),([0,0,.35],{})]
    with ProcessPoolExecutor(args.workers,mp_context=mp.get_context('spawn')) as pool:
        raw=list(pool.map(worker,[(r['parameters'],c,kw) for r in candidates for c,kw in cases]))
    for i,r in enumerate(candidates):
        r['cases']=raw[i*len(cases):(i+1)*len(cases)]
        r['passed']=all(passes(c) for c in r['cases'])
        print(r['run'],r['generation'],r['passed'],
              [round(c['slip_rms_m_s'],4) for c in r['cases']],flush=True)
    if args.local_grid:
        bounds=dict(velocity_rmse=.065,yaw_rmse=.12,tilt_rms_deg=.75,slip_rms_m_s=.055,
                    target_acceleration_rms=60,target_jerk_rms=3000,joint_speed_max=4.8)
        def violation(r):
            return sum(100*(not c['passed'] or c['warnings']>0)+
                       sum(max(c[k]/v-1,0) for k,v in bounds.items()) for c in r['cases'])
        base=min(candidates,key=violation);grid=[]
        for cadence,lift,stride in product([.99,1.,1.01],[.95,1.,1.05],[.96,.98,1.]):
            p=np.array(base['parameters']);p[[0,2,3]]*=[cadence,lift,stride]
            p=np.clip(p,LOW,HIGH)
            grid.append(dict(run=base['run'],generation=base['generation'],parameters=p.tolist(),
                             local_grid_scales=[cadence,lift,stride]))
        with ProcessPoolExecutor(args.workers,mp_context=mp.get_context('spawn')) as pool:
            raw=list(pool.map(worker,[(r['parameters'],c,kw) for r in grid for c,kw in cases]))
        for i,r in enumerate(grid):
            r['cases']=raw[i*len(cases):(i+1)*len(cases)]
            r['passed']=all(passes(c) for c in r['cases'])
        candidates.extend(grid)
        print('Local grid:',sum(r['passed'] for r in grid),'/',len(grid),'feasible',flush=True)
    eligible=[r for r in candidates if r['passed']]
    chosen=max(eligible,key=lambda r:r['cases'][0]['measured_velocity'][0]) if eligible else None
    if chosen:
        save(args.policy,chosen['parameters'],stage='long-stride reference gate selection',
             simulator='Original MuJoCo C with full BAM M6',source_run=chosen['run'],
             generation=chosen['generation'],selection_cases=len(cases),
             local_grid_scales=chosen.get('local_grid_scales'),
             selection='Fastest forward checkpoint passing every reference gate')
    args.out.write_text(json.dumps(dict(candidates=candidates,selected=chosen),indent=2)+'\n')
    print('Selected',chosen['run']+' generation '+str(chosen['generation']) if chosen else 'NONE')


if __name__=='__main__':main()
