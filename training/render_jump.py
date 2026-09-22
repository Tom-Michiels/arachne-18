"""Replay recorded jump physics at real time, with whole-robot clearance HUD."""
import hashlib,json
from pathlib import Path
import imageio.v2 as imageio
import mujoco
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from jump import ROOT,Robot,evaluate


def main():
    policy=ROOT/'training/policies/jump.json';p=np.array(json.loads(policy.read_text())['parameters'])
    metrics,trace=evaluate(p,record=True)
    out=ROOT/'assets/arachne-jump.mp4'
    np.savez_compressed(out.with_suffix('.npz'),**trace)
    robot=Robot();m,d=robot.model,robot.data;m.vis.global_.offwidth=1280;m.vis.global_.offheight=800
    m.mat_reflectance[:]=0;m.vis.headlight.ambient[:]=[.3,.3,.3]
    camera=mujoco.MjvCamera();mujoco.mjv_defaultCamera(camera);camera.distance=.75;camera.azimuth=125;camera.elevation=-14
    camera.lookat[:]=[0,0,.08]
    opt=mujoco.MjvOption();opt.geomgroup[3]=0;opt.sitegroup[:]=0
    font_path=next((p for p in ['/System/Library/Fonts/Supplemental/Arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'] if Path(p).exists()),None)
    font=ImageFont.truetype(font_path,24) if font_path else ImageFont.load_default()
    small=ImageFont.truetype(font_path,18) if font_path else ImageFont.load_default()
    apex=int(np.argmax(np.where(trace['airborne'],trace['clearance'],0)))
    # Audit all rendered CAD mesh vertices too: visual geometry must also clear.
    d.qpos[:]=trace['qpos'][apex];mujoco.mj_forward(m,d);cad=[]
    for g in range(m.ngeom):
        if m.geom_type[g]!=mujoco.mjtGeom.mjGEOM_MESH:continue
        mesh=m.geom_dataid[g];a=m.mesh_vertadr[mesh];n=m.mesh_vertnum[mesh]
        z=m.mesh_vert[a:a+n]@d.geom_xmat[g].reshape(3,3)[2,:]+d.geom_xpos[g,2]
        cad.append(float(z.min()))
    metrics['cad_mesh_clearance_at_apex_m']=min(cad)
    metrics.update(policy='training/policies/jump.json',policy_sha256=hashlib.sha256(policy.read_bytes()).hexdigest(),
                   playback='3.5 seconds real time, followed by a clearly labelled 4x slow replay of the same 3.5 seconds; 50 fps')
    out.with_suffix('.json').write_text(json.dumps(metrics,indent=2)+'\n')
    with mujoco.Renderer(m,800,1280) as renderer, imageio.get_writer(str(out),fps=50,codec='libx264',macro_block_size=1,ffmpeg_params=['-crf','22','-movflags','+faststart']) as writer:
        for slow in [False,True]:
            for i in range(0,len(trace['time']),1 if slow else 2):
                d.qpos[:]=trace['qpos'][i];mujoco.mj_forward(m,d);renderer.update_scene(d,camera,scene_option=opt)
                frame=Image.fromarray(renderer.render());draw=ImageDraw.Draw(frame)
                draw.rectangle((0,0,1280,86),fill=(12,23,29));draw.text((25,16),'ARACHNE / 18 — JUMP',font=font,fill='white')
                draw.text((25,53),'Whole-robot clearance / Original joint limits / MuJoCo + BAM',font=small,fill=(160,200,190))
                draw.rectangle((0,734,1280,800),fill=(12,23,29))
                label='AIRBORNE' if trace['airborne'][i] else 'GROUND CONTACT'
                draw.text((25,746),f"{label}    Collision gap: {max(0,trace['clearance'][i])*100:.2f} cm    Peak: {metrics['peak_whole_robot_clearance_m']*100:.2f} cm",font=font,fill='white')
                draw.text((1100,747),f"{trace['time'][i]:.2f} s",font=font,fill='white')
                draw.text((1010,22),'4x SLOW REPLAY' if slow else 'REAL TIME',font=small,fill=(160,200,190))
                for _ in range(2 if slow else 1):writer.append_data(np.asarray(frame))
        # Use the exact apex state for the poster even if between video frames.
        d.qpos[:]=trace['qpos'][apex];mujoco.mj_forward(m,d);renderer.update_scene(d,camera,scene_option=opt)
        poster=Image.fromarray(renderer.render());draw=ImageDraw.Draw(poster);draw.rectangle((0,0,1280,65),fill=(12,23,29));draw.text((25,20),f"JUMP APEX / All CAD parts at least {metrics['cad_mesh_clearance_at_apex_m']*100:.2f} cm above ground",font=font,fill='white');poster.save(out.with_suffix('.jpg'))
    print(json.dumps(metrics,indent=2))


if __name__=='__main__':main()
