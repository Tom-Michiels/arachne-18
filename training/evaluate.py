"""Independent MuJoCo C/BAM evaluation and real physics video capture."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
import mujoco
from gait import ROOT, INITIAL, target, rotate, feet, load, frequency


def evaluate(params, command, seconds=10., backend='bam', video=None, width=960, height=640,
             schedule=None, friction=None, payload=0., imu_noise=0., seed=23):
    if backend=='bam':
        sys.path.insert(0,str(ROOT/'simulation'))
        from simulate import Robot
        robot=Robot(); m,d=robot.model,robot.data
    else:
        m=mujoco.MjModel.from_xml_path(str(ROOT/'training/arachne_metal.xml'))
        d=mujoco.MjData(m); mujoco.mj_resetDataKeyframe(m,d,0)
        robot=None
    if friction is not None:m.geom_friction[:,0]=friction
    if payload:
        body=m.body('BODY').id
        old=m.body_mass[body];m.body_mass[body]+=payload
        m.body_inertia[body]*=(old+payload)/old
        mujoco.mj_setConst(m,d)
    rng=np.random.default_rng(seed)
    dt=.01; substeps=round(dt/m.opt.timestep)
    p=np.asarray(params,dtype=float)[None,:]; cmd=np.asarray(command,dtype=float)[None,:]
    phase=np.zeros(1); sm=np.zeros((1,18)); prev=sm.copy(); prev2=sm.copy()
    samples=[]; all_q=[]; all_t=[]; all_ctrl=[]; all_commands=[]; last_feet=None
    cmd_filtered=cmd.copy()
    render=None; writer=None
    if video:
        import imageio.v2 as imageio
        from video_hud import HUD
        hud=HUD(width,height)
        Path(video).parent.mkdir(parents=True,exist_ok=True)
        m.vis.global_.offwidth=width; m.vis.global_.offheight=height
        m.mat_reflectance[:]=0
        m.light_ambient[:]=[.35,.35,.35]
        m.light_diffuse[:]=[.85,.85,.85]
        render=mujoco.Renderer(m,height,width)
        writer=imageio.get_writer(str(video),fps=50,codec='libx264',quality=None,
                                  macro_block_size=1,ffmpeg_params=['-crf','23','-movflags','+faststart'])
        camera=mujoco.MjvCamera(); mujoco.mjv_defaultCamera(camera)
        camera.distance=.82;camera.azimuth=125;camera.elevation=-27
        opt=mujoco.MjvOption();opt.geomgroup[3]=0;opt.sitegroup[:]=0
    try:
        for i in range(round(seconds/dt)):
            if schedule:
                requested=next(c for start,c in reversed(schedule) if i*dt>=start)
                cmd_filtered += (1-np.exp(-dt/.25))*(np.array(requested)[None,:]-cmd_filtered)
                cmd=cmd_filtered
            obs_q=d.qpos[None,:].copy();gyro=d.qvel[None,3:6].copy()
            if imu_noise:
                # Perturb orientation estimate only; true state remains untouched.
                axis=rng.normal(size=3);angle=rng.normal(scale=np.deg2rad(imu_noise))
                axis/=np.linalg.norm(axis); dq=np.r_[np.cos(angle/2),axis*np.sin(angle/2)]
                perturbed=np.empty(4);mujoco.mju_mulQuat(perturbed,obs_q[0,3:7],dq)
                obs_q[0,3:7]=perturbed;gyro+=rng.normal(scale=.005,size=(1,3))
            desired=target(p,phase,cmd,obs_q,i*dt,gyro=gyro)
            filtered=np.clip(sm+.35*(desired-sm),sm-.047171,sm+.047171)
            # Same one-control-step delay/filter as training; BAM adds its real delay.
            for _ in range(substeps):
                if robot:robot.step(sm[0])
                else:d.ctrl[:]=sm[0];mujoco.mj_step(m,d)
            prev2,prev,sm=prev,sm,filtered
            phase=(phase+frequency(p,cmd)*dt)%1
            q=d.qpos[None,:];v=d.qvel[None,:]
            gravity=rotate(q[:,3:7],np.array([[0.,0.,-1.]]),inverse=True)[0]
            lin=rotate(q[:,3:7],v[:,:3],inverse=True)[0]
            foot=np.array([d.site(f'L{j}_foot').xpos.copy() for j in range(1,7)])
            foot_geoms={m.geom(f'L{j}_foot_contact').id for j in range(1,7)}
            contacts=set();nonfoot=0
            for c in d.contact:
                if c.geom1==0 or c.geom2==0:
                    geom=c.geom2 if c.geom1==0 else c.geom1
                    if geom in foot_geoms:contacts.add(geom)
                    else:nonfoot+=1
            vel=np.zeros_like(foot) if last_feet is None else (foot-last_feet)/dt
            last_feet=foot
            mask=np.array([m.geom(f'L{j}_foot_contact').id in contacts for j in range(1,7)])
            slip=np.mean(np.sum(vel[mask,:2]**2,-1)) if mask.any() else 0.
            samples.append([*lin[:2],d.qvel[5],np.arccos(np.clip(-gravity[2],-1,1)),
                            d.qpos[2],d.qvel[2],np.linalg.norm(d.qvel[3:5]),slip,
                            len(contacts),nonfoot,np.sqrt(np.mean(((sm-prev)/dt)**2)),
                            np.sqrt(np.mean(((sm-2*prev+prev2)/dt**2)**2)),
                            np.max(np.abs(d.qvel[6:])),np.max(np.abs(d.actuator_force))])
            all_q.append(d.qpos.copy());all_ctrl.append(sm[0].copy());all_t.append(d.time)
            all_commands.append(cmd[0].copy())
            if render and i%2==0:
                camera.lookat[:]=d.qpos[:3]+[0,0,.015]
                render.update_scene(d,camera,scene_option=opt)
                frame=hud.draw(render.render(),d.time,cmd[0],lin,samples[-1][3],d.qpos)
                writer.append_data(frame)
        data=np.asarray(samples); skip=min(200,len(data)//2);steady=data[skip:]
        requested=np.asarray(all_commands)[skip:]
        result=dict(backend=backend,command=list(command),seconds=seconds,
            measured_velocity=steady[:,:3].mean(0).tolist(),
            velocity_rmse=float(np.sqrt(np.mean(np.sum((steady[:,:2]-requested[:,:2])**2,-1)))),
            yaw_rmse=float(np.sqrt(np.mean((steady[:,2]-requested[:,2])**2))),
            tilt_rms_deg=float(np.rad2deg(np.sqrt(np.mean(steady[:,3]**2)))),
            tilt_max_deg=float(np.rad2deg(np.max(data[:,3]))),
            height_mean_m=float(steady[:,4].mean()),height_std_mm=float(steady[:,4].std()*1000),
            vertical_velocity_rms=float(np.sqrt(np.mean(steady[:,5]**2))),
            body_rp_rate_rms=float(np.sqrt(np.mean(steady[:,6]**2))),
            slip_rms_m_s=float(np.sqrt(steady[:,7].mean())),
            feet_contacts_mean=float(steady[:,8].mean()),nonfoot_contacts=int(data[:,9].sum()),
            target_rate_rms=float(np.sqrt(np.mean(steady[:,10]**2))),
            target_acceleration_rms=float(np.sqrt(np.mean(steady[:,11]**2))),
            joint_speed_max=float(data[:,12].max()),motor_torque_max=float(data[:,13].max()),
            displacement_m=d.qpos[:2].tolist(),warnings=int(sum(w.number for w in d.warning)),
            passed=bool(np.all(data[:,4]>.065) and np.max(data[:,3])<np.deg2rad(15)
                        and not data[:,9].any() and np.isfinite(data).all()),
            friction=friction,payload_kg=payload,imu_orientation_noise_deg=imu_noise,
            schedule=schedule)
        if video:
            np.savez_compressed(str(Path(video).with_suffix('.npz')),time=all_t,qpos=all_q,
                                target=all_ctrl,metrics=data,command=all_commands)
        return result
    finally:
        if writer:writer.close()
        if render:render.close()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--policy',type=Path)
    ap.add_argument('--backend',choices=['bam','surrogate'],default='bam')
    ap.add_argument('--command',nargs=3,type=float,default=[.08,0,0])
    ap.add_argument('--seconds',type=float,default=10.)
    ap.add_argument('--video',type=Path)
    ap.add_argument('--out',type=Path)
    args=ap.parse_args()
    r=evaluate(load(args.policy) if args.policy else INITIAL,args.command,args.seconds,args.backend,args.video)
    print(json.dumps(r,indent=2))
    if args.out:args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(r,indent=2)+'\n')


if __name__=='__main__':main()
