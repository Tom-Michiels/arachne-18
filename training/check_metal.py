"""Check Metal against independent MuJoCo C before trusting search results."""
import json
import numpy as np
import mujoco
import mlx.core as mx
import _mjmlx_native as mj
from gait import ROOT, INITIAL, target, feet


def main():
    n=32; rng=np.random.default_rng(2026)
    path=str(ROOT/'training/arachne_metal.xml')
    model=mj.load_model(path); sim=mj.create_batched(model,n,frame_skip=5,solver_iterations=12)
    cm=mujoco.MjModel.from_xml_path(path)
    qp=np.tile(cm.key_qpos[0],(n,1)).astype(np.float32)
    qp[:,7:]+=rng.uniform(-.015,.015,(n,18))
    qv=rng.uniform(-.015,.015,(n,24)).astype(np.float32)
    control=rng.uniform(-.03,.03,(n,18)).astype(np.float32)
    sim.set_qpos(mx.array(qp));sim.set_qvel(mx.array(qv));sim.qacc_warmstart=mx.zeros((n,24))
    sim.step(mx.array(control));mx.eval(sim.qpos,sim.qvel)
    expected_q=[];expected_v=[]
    for i in range(n):
        d=mujoco.MjData(cm);d.qpos[:]=qp[i];d.qvel[:]=qv[i];d.ctrl[:]=control[i]
        mujoco.mj_step(cm,d,nstep=5)
        expected_q.append(d.qpos.copy());expected_v.append(d.qvel.copy())
    pos_error=float(np.max(np.abs(np.array(sim.qpos)-expected_q)))
    vel_error=float(np.max(np.abs(np.array(sim.qvel)-expected_v)))
    p=np.tile(INITIAL,(n,1)).astype(np.float32);cmd=rng.uniform(-.12,.12,(n,3)).astype(np.float32)
    phase=rng.uniform(0,1,n).astype(np.float32)
    cpu=target(p,phase,cmd,qp,2.,gyro=qv[:,3:6])
    gpu=target(mx.array(p),mx.array(phase),mx.array(cmd),mx.array(qp),mx.array(2.),mx,gyro=mx.array(qv[:,3:6]))
    target_error=float(np.max(np.abs(cpu-np.array(gpu))))
    result=dict(backend=sim.backend,qpos_max_abs_error=pos_error,qvel_max_abs_error=vel_error,
                controller_max_abs_error=target_error,environments=n,physics_steps=5,
                passed=pos_error<1e-4 and vel_error<.02 and target_error<2e-6)
    print(json.dumps(result,indent=2))
    dest=ROOT/'training/results/metal_conformance.json';dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(result,indent=2)+'\n')
    assert result['passed'],result


if __name__=='__main__':main()
