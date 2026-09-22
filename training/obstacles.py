"""Seeded discrete rocks and spring-mounted grass-tuft proxies, in metres.

Rocks are fixed ellipsoids, partly buried. Each grass tuft has two passive
hinges: it bends on contact and returns under spring torque. This is a reduced
mechanical model, not a calibrated botanical or soil model.
"""
import xml.etree.ElementTree as ET
import mujoco
import numpy as np
from gait import ROOT

KINDS={'rocks','grass','rocks_and_grass'}


def make_model(spec,seed):
    rng=np.random.default_rng(seed)
    root=ET.parse(ROOT/'simulation/arachne.xml').getroot()
    root.find('compiler').set('meshdir',str(ROOT/'simulation/meshes'))
    world=root.find('worldbody');objects=[];extra_dofs=0
    kinds=['rocks','grass'] if spec['kind']=='rocks_and_grass' else [spec['kind']]
    for kind in kinds:
        spacing=spec.get('rock_spacing_m',.12) if kind=='rocks' else spec.get('grass_spacing_m',.16)
        for x in np.arange(-1.25,1.26,spacing):
            for y in np.arange(-1.25,1.26,spacing):
                xy=np.array([x,y])+rng.uniform(-.22,.22,2)*spacing
                if np.linalg.norm(xy)<.42 or np.linalg.norm(xy)>1.3:continue
                index=len(objects);name=f'obstacle_{kind}_{index}'
                if kind=='rocks':
                    height=rng.uniform(*spec.get('rock_height_m',[.004,.010]))
                    radii=rng.uniform(.016,.035,2)
                    shade=rng.uniform(.32,.49)
                    ET.SubElement(world,'geom',name=name,type='ellipsoid',
                        pos=f'{xy[0]} {xy[1]} {height*.2}',size=f'{radii[0]} {radii[1]} {height*.8}',
                        euler=f'0 0 {rng.uniform(0,6.28)}',rgba=f'{shade} {shade*.95} {shade*.85} 1',
                        group='0',contype='1',conaffinity='1',friction='.8 .005 .0001')
                    objects.append(dict(name=name,kind=kind,xy=xy.tolist(),height_m=height))
                else:
                    height=rng.uniform(*spec.get('grass_height_m',[.018,.030]))
                    body=ET.SubElement(world,'body',name=name,pos=f'{xy[0]} {xy[1]} 0')
                    ET.SubElement(body,'inertial',pos=f'0 0 {height/2}',mass='.0002',diaginertia='2e-8 2e-8 1e-8')
                    for axis in ['1 0 0','0 1 0']:
                        ET.SubElement(body,'joint',name=f'{name}_bend_{extra_dofs}',type='hinge',axis=axis,
                            range='-1.2 1.2',stiffness=str(spec.get('grass_stiffness_nm_rad',.0005)),
                            damping='.00001',armature='.00000002')
                        extra_dofs+=1
                    for blade in range(3):
                        a=blade*2*np.pi/3
                        tip=[.005*np.cos(a),.005*np.sin(a),height]
                        ET.SubElement(body,'geom',name=f'{name}_blade_{blade}',type='capsule',
                            fromto=f'0 0 .002 {tip[0]} {tip[1]} {tip[2]}',size='.0015',
                            rgba='.22 .39 .10 1',group='1',contype='2',conaffinity='1',
                            friction='.4 .003 .0001',solref='.015 1')
                    objects.append(dict(name=name,kind=kind,xy=xy.tolist(),height_m=height))
    if extra_dofs:
        for key in root.findall('keyframe/key'):
            key.set('qpos',key.get('qpos')+' 0'*extra_dofs)
    model=mujoco.MjModel.from_xml_string(ET.tostring(root,encoding='unicode'))
    return model,dict(spec=spec,seed=int(seed),obstacles=objects,passive_dofs=extra_dofs,
                      spawn_clear_radius_m=.38,model='Fixed rocks; two-hinge spring grass proxies')
