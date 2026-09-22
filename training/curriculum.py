"""Gated terrain curriculum in parallel reference MuJoCo + full BAM.

Run --assess-only for an admission assessment. Without it, CEM trains each
stage that fails; promotion requires two independent held-out batches and
retention of smooth flat-ground locomotion. Failure preserves the last
promoted policy. The actor observes only IMU, command and oscillator state.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import numpy as np
from gait import ROOT, LOW, HIGH, load, save
from evaluate import evaluate


def gate(result, stage, config):
    """Return explicit failure reasons; standing cannot pass a walking task."""
    g=config['gates'];r=result;fail=[]
    if not r['passed'] or r['warnings'] or r['nonfoot_contacts']:fail.append('stability/contact')
    checks={
        'tilt_max_deg':g['tilt_max_deg'], 'tilt_rms_deg':stage['tilt_rms_max_deg'],
        'clearance_std_mm':stage['clearance_std_max_mm'],
        'velocity_rmse':g['velocity_rmse_max'], 'yaw_rmse':g['yaw_rmse_max'],
        'slip_rms_m_s':g['slip_rms_max'], 'target_rate_rms':g['target_rate_rms_max'],
        'target_acceleration_rms':g['target_acceleration_rms_max'],
        'target_jerk_rms':g['target_jerk_rms_max'],
        'clearance_rate_rms':g['clearance_rate_rms_max'], 'joint_speed_max':g['joint_speed_max']}
    for name,limit in checks.items():
        if not np.isfinite(r[name]) or r[name]>limit:fail.append(name)
    if r['clearance_min_m']<g['clearance_min_m']:fail.append('clearance_min_m')
    cmd=np.asarray(r['command'][:2]);speed=np.linalg.norm(cmd)
    if speed>.01:
        ratio=float(np.asarray(r['measured_velocity'][:2])@cmd/speed**2)
        if not g['speed_ratio_min']<=ratio<=g['speed_ratio_max']:fail.append('progress_ratio')
    if stage['terrain']['kind']!='flat' and r['terrain_exposure_fraction']<g['terrain_exposure_fraction_min']:
        fail.append('terrain_exposure_fraction')
    for metric,minimum in stage.get('minimum_encounters',{}).items():
        if r.get(metric,0)<minimum:fail.append(metric)
    return fail


def reward(r):
    if not r['passed'] or r['warnings']:return -100.
    # Terrain-relative clearance avoids penalizing a successful ascent itself.
    return float(5*np.exp(-r['velocity_rmse']**2/.0016)+1.5*np.exp(-r['yaw_rmse']**2/.09)
                 -90*np.deg2rad(r['tilt_rms_deg'])**2-20*r['body_rp_rate_rms']**2
                 -80*r['clearance_rate_rms']**2-30*r['slip_rms_m_s']**2
                 -.025*r['target_rate_rms']**2-.00015*r['target_acceleration_rms']**2
                 -1e-8*r['target_jerk_rms']**2)


def worker(task):
    p,command,stage,seconds,seed,noise=task
    return evaluate(p,command,seconds,terrain=stage['terrain'],seed=seed,imu_noise=noise)


def commands(stage, held_out=False):
    # Held-out headings lie halfway between the training directions.
    angles=np.arange(8)*np.pi/4+(np.pi/8 if held_out else 0)
    v=stage['speed_m_s']
    result=[[v*np.cos(a),v*np.sin(a),0.] for a in angles]
    result += [[v,0,.12],[v,0,-.12]]
    if stage['terrain']['kind']=='flat':result += [[0,0,.35],[0,0,-.35],[0,0,0]]
    return result


def assess(pool,p,stage,config,seed):
    batches=[]
    for batch in range(config['promotion']['consecutive_batches']):
        tasks=[(p,cmd,stage,config['episode_seconds'],seed+100*batch+s,.15)
               for s in range(config['promotion']['seeds_per_batch'])
               for cmd in commands(stage,True)]
        rows=[]
        for task,r in zip(tasks,pool.map(worker,tasks)):
            failures=gate(r,stage,config)
            rows.append(dict(seed=task[4],failures=failures,metrics=r))
        fraction=sum(not r['failures'] for r in rows)/len(rows)
        batches.append(dict(pass_fraction=fraction,cases=rows))
        # Safety/stability failures may never be hidden by the aggregate threshold.
        safe=all(r['metrics']['passed'] and not r['metrics']['warnings'] for r in rows)
        if fraction<config['promotion']['minimum_pass_fraction'] or not safe:break
    passed=(len(batches)==config['promotion']['consecutive_batches'] and
            all(b['pass_fraction']>=config['promotion']['minimum_pass_fraction'] and
                all(r['metrics']['passed'] and not r['metrics']['warnings'] for r in b['cases'])
                for b in batches))
    return dict(passed=passed,batches=batches)


def write(path,value):
    path.write_text(json.dumps(value,indent=2)+'\n')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config',type=Path,default=ROOT/'training/terrain_curriculum.json')
    ap.add_argument('--policy',type=Path)
    ap.add_argument('--workers',type=int,default=8)
    ap.add_argument('--population',type=int,default=24)
    ap.add_argument('--generations',type=int,default=8)
    ap.add_argument('--max-stage',type=int,default=6,help='Inclusive, 0 = flat admission only')
    ap.add_argument('--seed',type=int,default=701)
    ap.add_argument('--assess-only',action='store_true')
    ap.add_argument('--out',type=Path,default=ROOT/'training/runs/terrain')
    args=ap.parse_args();config=json.loads(args.config.read_text())
    if args.workers<1 or args.population<8 or args.generations<1:ap.error('workers >= 1, population >= 8, generations >= 1 required')
    if not 0<=args.max_stage<len(config['stages']):ap.error('max-stage is outside the curriculum')
    args.out.mkdir(parents=True,exist_ok=True)
    p=load(args.policy or ROOT/config['starting_policy']);rng=np.random.default_rng(args.seed)
    report=dict(status='running',config=config,seed=args.seed,stages=[],
                starting_policy=str(args.policy or config['starting_policy']),
                source_sha256={name:hashlib.sha256((ROOT/'training'/name).read_bytes()).hexdigest()
                               for name in ['gait.py','evaluate.py','terrain.py','obstacles.py','curriculum.py']})
    write(args.out/'report.json',report)
    with ProcessPoolExecutor(args.workers,mp_context=mp.get_context('spawn')) as pool:
        for index,stage in enumerate(config['stages'][:args.max_stage+1]):
            print('Assessing',stage['name'],flush=True)
            # Disjoint seed ranges for optimization, stage admission, and promotions.
            assessment=assess(pool,p,stage,config,1_000_000+index*10_000)
            entry=dict(stage=stage['name'],admission=assessment,attempts=[])
            report['stages'].append(entry)
            passed=assessment['passed']
            if not passed and not args.assess_only and index>0:
                mean=p.copy();std=(HIGH-LOW)*.08
                for gen in range(args.generations):
                    pop=np.clip(rng.normal(mean,std,(args.population,len(p))),LOW,HIGH)
                    pop[0]=p;pop[1]=mean
                    # Three terrain tasks + one flat task per candidate (25% replay).
                    if config['flat_replay_fraction']!=.25:
                        raise ValueError('This runner requires flat_replay_fraction = 0.25')
                    available=commands(stage);flat=config['stages'][0]
                    seed=args.seed+index*10_000+gen*100
                    chosen=rng.choice(len(available),3,replace=False)
                    tasks=[]
                    for candidate in pop:
                        tasks.extend((candidate,available[c],stage,config['episode_seconds'],seed+j,0.)
                                     for j,c in enumerate(chosen))
                        tasks.append((candidate,commands(flat)[gen%len(commands(flat))],flat,
                                      config['episode_seconds'],seed+90,0.))
                    raw=list(pool.map(worker,tasks))
                    returns=np.array([reward(r) for r in raw]).reshape(-1,4)
                    scores=.7*returns.mean(1)+.3*returns.min(1)
                    elite=np.argsort(scores)[-max(4,args.population//4):]
                    mean=.25*mean+.75*pop[elite].mean(0)
                    std=np.maximum(.35*std+.65*pop[elite].std(0),(HIGH-LOW)*.012)
                    p=pop[int(np.argmax(scores))].copy()
                    # Selection can never reuse the optimization seed distribution.
                    test=assess(pool,p,stage,config,2_000_000+index*100_000+gen*1000)
                    retained=assess(pool,p,flat,config,4_000_000+index*100_000+gen*1000) if test['passed'] else None
                    passed=bool(test['passed'] and retained and retained['passed'])
                    entry['attempts'].append(dict(generation=gen,score=float(scores.max()),
                                                  assessment=test,flat_retention=retained))
                    save(args.out/'candidate.json',p,stage=stage['name'],promoted=False)
                    write(args.out/'report.json',report)
                    print(stage['name'],'generation',gen,'promoted',passed,flush=True)
                    if passed:break
            entry['promoted']=passed
            if not passed:
                report['status']='needs_training' if args.assess_only else 'budget_exhausted'
                report['next_stage']=stage['name']
                write(args.out/'report.json',report)
                print('Stopped at',stage['name'],'— last promoted policy preserved.',flush=True)
                break
            save(args.out/'last_promoted.json',p,stage=stage['name'],promoted=True)
            save(args.out/(stage['name']+'.json'),p,stage=stage['name'],promoted=True)
            write(args.out/'report.json',report)
        else:
            report['status']='completed' if args.max_stage==len(config['stages'])-1 else 'requested_stages_passed'
            write(args.out/'report.json',report)
    print('Report:',args.out/'report.json',flush=True)


if __name__=='__main__':main()
