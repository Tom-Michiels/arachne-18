"""MuJoCo-rendered replay of DISTINCT, recorded parallel training candidates.

Every robot pose comes from its own GPU physics environment. Grid translations
are display offsets only; the independent training worlds do not interact.
Small hidden hardware is omitted in the overview, while body/leg CAD is kept.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import mujoco
import imageio.v2 as imageio
from PIL import Image,ImageDraw
from gait import ROOT
from video_hud import HUD


def make_scene(n):
    tree=ET.parse(ROOT/'simulation/arachne.xml');root=tree.getroot()
    root.find('compiler').set('meshdir',str(ROOT/'simulation/meshes'))
    for tag in ['actuator','sensor','keyframe']:
        root.remove(root.find(tag))
    world=root.find('worldbody');original=world.find('body');world.remove(original)
    keep={'01_CHASSIS','02_DORSAL_DECK','05_SHELL'}
    keep.update(f'L{i}_{part}' for i in range(1,7)
                for part in ['coxa','coxa_bottom','femur','femur_side_plate','tibia','foot'])
    keep.update(g.get('mesh') for g in original.iter('geom') if '_STS3215' in g.get('mesh',''))
    for body in original.iter('body'):
        for child in list(body):
            if child.tag in ['site','camera'] or (child.tag=='geom' and child.get('mesh') not in keep):
                body.remove(child)
    for mesh in list(root.find('asset').findall('mesh')):
        if mesh.get('name') not in keep:root.find('asset').remove(mesh)
    offsets=np.array([[(i%16-7.5)*.82,(i//16-3.5)*.82,0.] for i in range(n)])
    for i in range(n):
        robot=copy.deepcopy(original)
        for element in robot.iter():
            if 'name' in element.attrib:element.set('name',f'robot{i}_{element.get("name")}')
        world.append(robot)
    material=root.find("asset/material[@name='floor_mat']")
    material.set('reflectance','0');material.set('texrepeat','35 35')
    world.find("geom[@name='ground']").set('size','50 50 .1')
    light=world.find('light');light.set('directional','true');light.set('ambient','.4 .4 .4')
    light.set('diffuse','.85 .85 .85');light.set('dir','-.2 -.4 -1')
    root.find('visual/global').set('offwidth','1440');root.find('visual/global').set('offheight','900')
    model=mujoco.MjModel.from_xml_string(ET.tostring(root,encoding='unicode'))
    return model,offsets


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run',type=Path,default=ROOT/'training/recordings/army')
    ap.add_argument('--out',type=Path,default=ROOT/'assets/arachne-training-army.mp4')
    ap.add_argument('--preview',action='store_true')
    args=ap.parse_args();files=sorted(args.run.glob('generation_*.npz'))
    if not files:raise SystemExit('No recorded generation_*.npz files found')
    first=np.load(files[0]);n=first['qpos'].shape[1]
    m,offsets=make_scene(n);d=mujoco.MjData(m)
    cam=mujoco.MjvCamera();mujoco.mjv_defaultCamera(cam)
    cam.azimuth=90;cam.elevation=-65;cam.distance=12.5
    opt=mujoco.MjvOption();opt.geomgroup[3]=0;opt.sitegroup[:]=0
    hud=HUD(1440,900);sources=[];frame_count=0
    shell_ids=np.array([m.geom(f'robot{i}_05_SHELL_visual').id for i in range(n)])
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with mujoco.Renderer(m,900,1440,max_geom=16000) as renderer:
        with imageio.get_writer(str(args.out),fps=25,codec='libx264',quality=None,macro_block_size=1,
                                ffmpeg_params=['-crf','23','-movflags','+faststart']) as writer:
            for path in files:
                data=np.load(path);states=data['qpos'];scores=data['returns'];gen=int(path.stem.split('_')[-1])
                elite=np.argsort(scores)[-max(8,n//8):]
                m.geom_rgba[shell_ids]=[.23,.48,.46,1.]
                m.geom_rgba[shell_ids[elite]]=[.83,.53,.16,1.]
                sources.append(dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                    generation=gen,candidates=n,mean_return=float(scores.mean()),
                                    best_return=float(scores.max()),physics_seconds=float(data['time'][-1])))
                indices=[min(100,len(states)-1)] if args.preview else range(len(states))
                for frame in indices:
                    q=states[frame].copy();q[:,:3]+=offsets
                    d.qpos[:]=q.reshape(-1);mujoco.mj_kinematics(m,d);mujoco.mj_camlight(m,d)
                    cam.lookat[:]=[float(q[:,0].mean()),float(q[:,1].mean()),0.]
                    renderer.update_scene(d,cam,scene_option=opt)
                    image=Image.fromarray(renderer.render()).convert('RGBA')
                    layer=Image.new('RGBA',image.size);draw=ImageDraw.Draw(layer)
                    draw.rectangle((0,0,1440,90),fill=(12,23,29,238))
                    draw.text((30,16),'ARACHNE / 18   |   THE TRAINING ARMY',font=hud.title,fill='white')
                    draw.text((30,56),f'{n} independent physics environments  /  18 actuators each  /  CEM policy search on Metal',font=hud.small,fill=(162,196,197))
                    draw.rounded_rectangle((1150,19,1410,68),8,fill=(44,111,102))
                    draw.text((1168,31),f'GENERATION {gen+1:02d}',font=hud.font,fill='white')
                    draw.rectangle((0,828,1440,900),fill=(12,23,29,238))
                    draw.text((30,842),f'Population reward {scores.mean():.2f}     Best {scores.max():.2f}     Target 14 cm/s',font=hud.font,fill='white')
                    draw.text((30,873),'Actual recorded training rollouts, rendered in MuJoCo. Amber shells: selected elite candidates.',font=hud.small,fill=(162,196,197))
                    draw.text((1254,850),f'{data["time"][frame]:.2f} / 8 s',font=hud.font,fill='white')
                    result=Image.alpha_composite(image,layer).convert('RGB')
                    writer.append_data(np.asarray(result));frame_count+=1
                    if frame_count==1:
                        result.save(args.out.with_suffix('.jpg'))
                    if frame_count%100==0:print('rendered',frame_count,'frames',flush=True)
                print('generation',gen,'rendered',flush=True)
    provenance=dict(source='Actual MuJoCo-MLX fused physics training state recordings',
        render='MuJoCo C kinematic replay with grid display offsets; original structural CAD meshes',
        independent_environments=True,shared_world_collisions=False,frames=frame_count,fps=25,
        candidates=n,sources=sources)
    args.out.with_suffix('.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(args.out,flush=True)


if __name__=='__main__':main()
