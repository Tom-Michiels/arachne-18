"""Held-out commands and perturbations in original MuJoCo + full BAM M6."""
import argparse
import json
import platform
from pathlib import Path
import numpy as np
import mujoco
from gait import ROOT, load
from evaluate import evaluate


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--policy',type=Path,required=True)
    ap.add_argument('--out',type=Path,default=ROOT/'training/results/validation.json')
    args=ap.parse_args();p=load(args.policy)
    cases=[]
    for angle in np.arange(16)*np.pi/8:
        cases.append((f'direction_{np.rad2deg(angle):g}',[.14*np.cos(angle),.14*np.sin(angle),0.],{}))
    for name,cmd in [('slow',[.06,0,0]),('fast',[.20,0,0]),('yaw_left',[0,0,.35]),
                     ('yaw_right',[0,0,-.35]),('curve',[.10,.04,.25]),('stand',[0,0,0])]:
        cases.append((name,cmd,{}))
    for name,kw in [('low_friction',dict(friction=.5)),('high_friction',dict(friction=1.1)),
                     ('payload_200g',dict(payload=.2)),('imu_noise',dict(imu_noise=.25))]:
        cases.append((name,[.14,0,0],kw))
    results=[]
    for name,cmd,kw in cases:
        r=evaluate(p,cmd,12.,**kw)
        # Stability and task success are separate: a stationary robot cannot pass walking.
        r['stable']=r.pop('passed')
        r['passed']=bool(r['stable'] and r['warnings']==0 and r['velocity_rmse']<.05
                         and r['yaw_rmse']<.12 and r['tilt_rms_deg']<1.5)
        results.append(dict(name=name,**r))
        print(name, 'PASS' if r['passed'] else 'FAIL',
              'velocity',np.round(r['measured_velocity'],3),
              'tilt',round(r['tilt_rms_deg'],3),'slip',round(r['slip_rms_m_s'],3),flush=True)
    report=dict(policy=str(args.policy),simulator='Original MuJoCo C with full BAM M6',
                mujoco=mujoco.__version__,numpy=np.__version__,python=platform.python_version(),
                cases=results,passed=sum(r['passed'] for r in results),total=len(results),
                all_passed=all(r['passed'] for r in results))
    args.out.parent.mkdir(exist_ok=True,parents=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(report['passed'],'/',report['total'],'passed')


if __name__=='__main__':main()
