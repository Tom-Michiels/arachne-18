"""Build an explicitly approximate model for the fused Metal simulator.

Keep CAD inertias and joint limits; use convex foot/chassis contacts, static
BAM-derived servo coefficients, Euler and pyramidal contacts. Validate winners
in simulation/simulate.py (original collision geometry and complete BAM M6).
"""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'training' / 'arachne_metal.xml'


def build():
    tree = ET.parse(ROOT / 'simulation/arachne.xml')
    root = tree.getroot()
    root.find('compiler').set('meshdir', '../simulation/meshes')
    root.find('option').attrib.update(timestep='.002', integrator='Euler',
                                      cone='pyramidal', iterations='12')
    root.remove(root.find('sensor'))  # IMU observations are assembled from simulator state.
    default = root.find('default')
    p = json.loads((ROOT / 'simulation/bam_sts3215_12v_approx_m6.json').read_text())
    damping = p['friction_viscous'] + p['kt']**2 / p['R']
    kp = .166 * 32 * p['error_gain_ratio'] * 12 * p['kt'] / p['R']
    torque = .97 * 12 * p['kt'] / p['R']
    default.find('joint').attrib.update(armature=str(p['armature']),
                damping=str(damping), frictionloss=str(p['friction_base']))
    default.find('geom').set('condim', '3')
    asset = root.find('asset')
    # 26 vertices, including exact poles: bottom support matches the sphere.
    vertices = np.array([(x,y,z) for x in (-1,0,1) for y in (-1,0,1)
                          for z in (-1,0,1) if (x,y,z)!=(0,0,0)], float)
    vertices /= np.linalg.norm(vertices, axis=1, keepdims=True)
    for name, scale in [('foot_hull', [.0075]*3), ('torso_hull', [.078,.049,.067])]:
        ET.SubElement(asset, 'mesh', name=name,
                      vertex=' '.join(f'{v:.9g}' for v in (vertices*scale).ravel()))
    # Strip purely visual meshes from training for quick load/compile.
    for body in root.iter('body'):
        for geom in list(body.findall('geom')):
            name = geom.get('name', '')
            if name.endswith('_foot_contact') or name == 'body_collision':
                geom.attrib.pop('size', None)
                geom.set('type', 'mesh')
                geom.set('mesh', 'torso_hull' if name == 'body_collision' else 'foot_hull')
                geom.set('contype', '2'); geom.set('conaffinity', '1')
            else:
                body.remove(geom)
    ground = root.find("worldbody/geom[@name='ground']")
    ground.set('contype', '1'); ground.set('conaffinity', '2')
    for mesh in list(asset.findall('mesh')):
        if mesh.get('name') not in ('foot_hull', 'torso_hull'):
            asset.remove(mesh)
    actuators = root.find('actuator')
    for motor in actuators:
        motor.tag = 'position'
        motor.attrib.update(kp=str(kp), ctrllimited='true',
                            ctrlrange='-.3490658504 .3490658504',
                            forcelimited='true', forcerange=f'{-torque} {torque}')
    ET.indent(tree)
    tree.write(OUT, encoding='unicode')
    meta = dict(kp_Nm_per_rad=kp, damping=damping, armature=p['armature'],
                frictionloss=p['friction_base'], max_motor_torque_Nm=torque,
                omissions=['load-dependent and Stribeck friction', 'self collision',
                           'command delay and firmware slew (applied by controller)'],
                timestep=.002, contact='26-vertex inscribed foot hull, pyramidal condim 3')
    (OUT.parent/'model_approximation.json').write_text(json.dumps(meta, indent=2)+'\n')
    print(OUT)


if __name__ == '__main__':
    build()
