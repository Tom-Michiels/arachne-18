"""Batched episodic CEM reinforcement learning on MuJoCo-MLX's fused GPU.

Usage: PYTHONPATH=/path/to/MuJoCo-MLX-Cpp/build python training/metal_search.py
Learn a compact smooth gait policy directly from return, first forward, then
command-conditioned omnidirectional locomotion. No demonstrations are used.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path
import numpy as np
import mlx.core as mx
import _mjmlx_native as mj
from gait import ROOT, INITIAL, LOW, HIGH, target, feet, rotate, save, load, frequency


class Evaluator:
    def __init__(self, n, seconds=6., smoothness=1.):
        self.n, self.dt, self.steps = n, .01, int(seconds/.01)
        self.smoothness = smoothness
        self.model = mj.load_model(str(ROOT/'training/arachne_metal.xml'))
        ok, reason = mj.fused_supported(self.model)
        if not ok:
            raise RuntimeError('Fused simulator unsupported: '+reason)
        self.sim = mj.create_batched(self.model,n,frame_skip=5,use_gpu=True,solver_iterations=12)
        self.initial = mx.array([0.,0.,.09715873972,1.,0.,0.,0.]+[0.]*18)
        self.sim.step(mx.zeros((n,18)))
        mx.eval(self.sim.qpos,self.sim.qvel)
        self.advance = mx.compile(self._advance)

    def _advance(self, qp, qv, ws, prev, prev2, smoothed, phase, p, cmd, t):
        # IMU projected gravity in target(); gyro lead damps body oscillation.
        # Predict tilt by 25ms using body-frame gyro; no global pose in policy.
        desired = target(p,phase,cmd,qp,t,mx,gyro=qv[:,3:6])
        # 10ms policy update, one update delay, firmware slew and low-pass.
        filtered = smoothed + .35*(desired-smoothed)
        filtered = mx.clip(filtered,smoothed-.047171,smoothed+.047171)
        self.sim.set_qpos(qp); self.sim.set_qvel(qv); self.sim.qacc_warmstart=ws
        self.sim.step(smoothed)
        nq,nv,nw = self.sim.qpos,self.sim.qvel,self.sim.qacc_warmstart
        lin = rotate(nq[:,3:7], nv[:,:3],mx,True)
        g = rotate(nq[:,3:7],mx.broadcast_to(mx.array([0.,0.,-1.]),(self.n,3)),mx,True)
        tilt2 = mx.sum(g[:,:2]**2,-1)
        foot_now, foot_prev = feet(nq,mx), feet(qp,mx)
        foot_speed = (foot_now-foot_prev)/self.dt
        contact = foot_now[:,:,2] < .01
        slip2 = mx.sum(mx.sum(foot_speed[:,:,:2]**2,-1)*contact,-1)/mx.maximum(mx.sum(contact,-1),1)
        track = mx.exp(-mx.sum((lin[:,:2]-cmd[:,:2])**2,-1)/.0016)
        yaw = mx.exp(-(nv[:,5]-cmd[:,2])**2/.09)
        rate = mx.mean(((filtered-smoothed)/self.dt)**2,-1)
        accel = mx.mean(((filtered-2*smoothed+prev)/self.dt**2)**2,-1)
        torque2 = mx.mean(self.sim.qfrc_actuator[:,6:]**2,-1)
        bad = mx.logical_or(nq[:,2]<.065, nq[:,2]>.15)
        bad = mx.logical_or(bad, tilt2>.20)
        bad = mx.logical_or(bad, mx.logical_not(mx.all(mx.isfinite(nq),-1)))
        # Time-normalized terms, absolute speed tracking: standing is poor.
        reward = (5*track+1.5*yaw - 90*tilt2 - 20*mx.sum(nv[:,3:5]**2,-1)
                  - 80*nv[:,2]**2 - 400*(nq[:,2]-.095)**2
                  - 15*slip2 - self.smoothness*(.025*rate + .00015*accel) - .025*torque2
                  - 30*bad.astype(mx.float32))
        metrics = mx.stack([lin[:,0],lin[:,1],nv[:,5],tilt2,nv[:,2]**2,
                            mx.sum(nv[:,3:5]**2,-1),slip2,rate,accel,bad.astype(mx.float32),
                            mx.mean(contact.astype(mx.float32),-1),track],-1)
        return nq,nv,nw,smoothed,prev,filtered,(phase+frequency(p,cmd,mx)*self.dt)%1,reward,metrics

    def evaluate(self, params, commands, capture=None):
        p,cmd=mx.array(params.astype(np.float32)),mx.array(commands.astype(np.float32))
        qp=mx.broadcast_to(self.initial,(self.n,25)); qv=mx.zeros((self.n,24)); ws=mx.zeros_like(qv)
        prev=mx.zeros((self.n,18)); prev2=prev; sm=prev; phase=mx.zeros((self.n,))
        returns=mx.zeros((self.n,)); metrics=mx.zeros((self.n,12)); count=0
        frames=[];times=[]
        for i in range(self.steps):
            qp,qv,ws,prev,prev2,sm,phase,r,m = self.advance(qp,qv,ws,prev,prev2,sm,phase,p,cmd,mx.array(i*self.dt))
            if i>=150:
                returns=returns+r; metrics=metrics+m; count+=1
            if i%25==24:
                mx.eval(qp,qv,ws,prev,prev2,sm,phase,returns,metrics)
            if capture is not None and i%4==3:
                frames.append(np.array(qp));times.append((i+1)*self.dt)
        mx.eval(returns,metrics)
        if capture is not None:
            np.savez_compressed(capture,qpos=np.stack(frames),time=times,
                                parameters=params,commands=commands,
                                returns=np.array(returns)/count,metrics=np.array(metrics)/count)
        return np.nan_to_num(np.array(returns)/count,nan=-1e6,posinf=-1e6,neginf=-1e6), np.array(metrics)/count


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage',choices=['forward','omni'],default='forward')
    ap.add_argument('--population',type=int,default=256)
    ap.add_argument('--generations',type=int,default=35)
    ap.add_argument('--seconds',type=float,default=6.)
    ap.add_argument('--speed',type=float,default=.08)
    ap.add_argument('--smoothness',type=float,default=1.)
    ap.add_argument('--seed',type=int,default=17)
    ap.add_argument('--resume',type=Path)
    ap.add_argument('--capture-generations',nargs='*',type=int,default=[])
    ap.add_argument('--out',type=Path,default=ROOT/'training/runs/forward')
    args=ap.parse_args(); args.out.mkdir(parents=True,exist_ok=True)
    if args.population<8 or args.generations<1 or args.seconds<=1.5:
        ap.error('population >= 8, generations >= 1 and seconds > 1.5 are required')
    rng=np.random.default_rng(args.seed)
    commands=np.array([[args.speed,0,0.]]) if args.stage=='forward' else np.array(
        [[args.speed*np.cos(a),args.speed*np.sin(a),0.] for a in np.arange(8)*np.pi/4]
        +[[0.,0.,.35],[0.,0.,-.35],[args.speed*.7,0.,.25],[0.,0.,0.]])
    k=len(commands); ev=Evaluator(args.population*k,args.seconds,args.smoothness)
    mean=load(args.resume) if args.resume else INITIAL.copy()
    std=(HIGH-LOW)*(.12 if args.resume else .20)
    best_score=-np.inf; best=mean.copy(); start=time.time()
    hashes={name:hashlib.sha256((ROOT/'training'/name).read_bytes()).hexdigest()
            for name in ['gait.py','metal_search.py','arachne_metal.xml']}
    (args.out/'config.json').write_text(json.dumps(dict(vars(args),source_sha256=hashes),default=str,indent=2)+'\n')
    for gen in range(args.generations):
        pop=np.clip(rng.normal(mean,std,(args.population,len(mean))),LOW,HIGH)
        pop[0]=best; pop[1]=mean
        batch=np.repeat(pop,k,axis=0); cmds=np.tile(commands,(args.population,1))
        capture=args.out/f'generation_{gen:03d}.npz' if gen in args.capture_generations else None
        t=time.time(); scores,met=ev.evaluate(batch,cmds,capture)
        # Penalize poor directions: optimize mean and lower tail, not just the easiest axis.
        scoremat=scores.reshape(-1,k)
        scores=.7*scoremat.mean(1)+.3*scoremat.min(1)
        elite=np.argsort(scores)[-max(8,args.population//8):]
        mean=.25*mean+.75*pop[elite].mean(0)
        std=np.maximum(.35*std+.65*pop[elite].std(0),(HIGH-LOW)*.012)
        winner=int(np.argmax(scores))
        if scores[winner]>best_score:
            best_score=float(scores[winner]); best=pop[winner].copy()
            save(args.out/'policy.json',best,stage=args.stage,score=best_score,generation=gen,
                 seed=args.seed,commands=commands.tolist(),simulator='MuJoCo-MLX fused approximate model')
        rec=dict(generation=gen,best=best_score,mean=float(scores.mean()),
                 seconds=round(time.time()-t,2),elapsed=round(time.time()-start,2),
                 policy=best.tolist(),winner_metrics=met.reshape(-1,k,12)[winner].tolist())
        with (args.out/'log.jsonl').open('a') as f:f.write(json.dumps(rec)+'\n')
        print(json.dumps({key:rec[key] for key in ['generation','best','mean','seconds','elapsed']}),flush=True)
    print('Saved',args.out/'policy.json',flush=True)


if __name__=='__main__':main()
