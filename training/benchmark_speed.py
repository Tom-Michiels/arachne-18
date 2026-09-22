"""Reference BAM checks for speed, actual foot excursion and smoothness."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import numpy as np
from gait import ROOT,load
from evaluate import evaluate


def passes(r):
    stable=r.get('stable',r.get('passed',False))
    return bool(stable and r['warnings']==0 and r['velocity_rmse']<.065
                and r['yaw_rmse']<.12 and r['tilt_rms_deg']<.75
                and r['slip_rms_m_s']<.055 and r['target_acceleration_rms']<60
                and r['target_jerk_rms']<3000 and r['joint_speed_max']<4.8)


def run(task):
    name,policy,command,kwargs=task
    path=Path(policy).resolve()
    label=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else path.name
    return dict(name=name,policy=label,policy_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                **evaluate(load(policy),command,12.,**kwargs))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--policy',type=Path,required=True)
    ap.add_argument('--speed',type=float,default=.24)
    ap.add_argument('--forward-speed',type=float,default=.26)
    ap.add_argument('--out',type=Path,default=ROOT/'training/results/long_stride_validation.json')
    ap.add_argument('--workers',type=int,default=8)
    args=ap.parse_args();path=str(args.policy)
    tasks=[('original_omni',str(ROOT/'training/policies/omni.json'),[.14,0,0],{}),
           ('previous_fast',str(ROOT/'training/policies/fast.json'),[.20,0,0],{})]
    for angle in np.arange(16)*np.pi/8:
        tasks.append((f'direction_{np.rad2deg(angle):g}',path,
                      [args.speed*np.cos(angle),args.speed*np.sin(angle),0],{}))
    for name,cmd in [('fast_forward',[args.forward_speed,0,0]),('slow',[.14,0,0]),('yaw_left',[0,0,.35]),('yaw_right',[0,0,-.35]),
                     ('curve',[.18,.04,.25]),('stand',[0,0,0])]:
        tasks.append((name,path,cmd,{}))
    for name,kw in [('low_friction',dict(friction=.5)),('high_friction',dict(friction=1.1)),
                    ('payload_200g',dict(payload=.2)),('imu_noise',dict(imu_noise=.25))]:
        tasks.append((name,path,[args.speed,0,0],kw))
    with ProcessPoolExecutor(args.workers,mp_context=mp.get_context('spawn')) as pool:
        rows=list(pool.map(run,tasks))
    # Predeclared bounds for a faster gait. These are separate from the stricter,
    # lower-speed terrain admission thresholds and the prior 26-test suite.
    for r in rows:
        r['stable']=r.pop('passed')
        r['passed']=passes(r)
        print(r['name'],'PASS' if r['passed'] else 'FAIL',
              'v',np.round(r['measured_velocity'],3),'foot',r['foot_excursion_mean_m'],
              'slip',round(r['slip_rms_m_s'],3),'jerk',round(r['target_jerk_rms']),flush=True)
    report=dict(policy=path,speed_command_m_s=args.speed,forward_command_m_s=args.forward_speed,
                reference_cases=rows[:2],cases=rows[2:],
                passed=sum(r['passed'] for r in rows[2:]),total=len(rows)-2)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
