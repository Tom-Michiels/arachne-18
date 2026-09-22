"""Conservative plug-envelope sweep for the two sockets on each dummy face.

The owner supplied the face orientation. Plug length and strain relief remain
nominal clearance envelopes until measured on the supplied cable housings.
"""
from pathlib import Path
import cadquery as cq
import itertools, json, math

ROOT=Path(__file__).resolve().parent.parent
CACHE=ROOT/'build/.cad_cache'
meta=json.loads((CACHE/'placed.json').read_text())
P=json.loads((ROOT/'build/parameters.json').read_text())
for o in meta:
    if o['kind']=='printed':o['shape']=cq.Shape.importBrep(str(CACHE/o['file']))

def box(x,y,z,l,w,h):return cq.Workplane('XY').box(l,w,h).translate((x,y,z)).val()
def pose(s,a,p):return s.rotate((0,0,0),(0,0,1),a).translate(p)
def shoulder(s):return s.rotate((0,0,0),(1,1,1),-120).translate((P['coxa'],0,0))
def knee(s):return s.rotate((0,0,0),(1,0,0),-90).translate((P['femur'],0,0))
def pitch(s,a):return s.rotate((0,0,0),(0,1,0),-a)
def overlap(a,b):
    return all(getattr(a,k+'max')>getattr(b,k+'min')+.01 and
               getattr(b,k+'max')>getattr(a,k+'min')+.01 for k in 'xyz')

# Pair of 5264/254 three-pin cable housings, plus a straight exit allowance.
# Approximate envelope: longitudinal -21..-10.5, combined width 20.5,
# exterior projection 12.5 beyond the -16.25 mm dummy-side body face.
plug=box(-15.75,-5.125,-22.5,10.5,10.25,12.5).fuse(
     box(-15.75,5.125,-22.5,10.5,10.25,12.5)).clean()
relief=box(-18,0,-34,6,20.5,10)
envelopes={'plug':plug,'straight_exit':relief}

rows=[]
for leg,angle,yaws in [(1,45,[-64,-35,0,35]),(2,90,[-35,0,35]),
                       (3,135,[-35,0,35,64])]:
    t=math.radians(angle)
    origin=(P['anchor_rx']*math.cos(t),P['anchor_ry']*math.sin(t),0)
    hip=(origin[0]+P['coxa']*math.cos(t),origin[1]+P['coxa']*math.sin(t),0)
    kpos=(hip[0]+P['femur']*math.cos(math.radians(P['femur_up_deg']))*math.cos(t),
          hip[1]+P['femur']*math.cos(math.radians(P['femur_up_deg']))*math.sin(t),
          P['femur']*math.sin(math.radians(P['femur_up_deg'])))
    axis=(-math.sin(t),math.cos(t),0)
    def turn(s,p,a):return s.rotate(p,tuple(p[i]+axis[i] for i in range(3)),a)
    candidates=[o for o in meta if o['kind']=='printed' and
                (o['group']=='BODY' or (o['group'] or '').startswith(f'L{leg}_'))]
    for yaw,pitch_angle,flex in itertools.product(yaws,[0,15,30],[-95,-80,-65]):
        parts=[]
        for o in candidates:
            s=o['shape'];g=o['group']
            if g and g.startswith(f'L{leg}_'):
                if g.endswith('TIBIA'):s=turn(s,kpos,-(flex+80))
                if g.endswith(('FEMUR','TIBIA')):s=turn(s,hip,-(pitch_angle-15))
                s=s.rotate(origin,(origin[0],origin[1],1),yaw)
            parts.append((o['name'],s,s.BoundingBox()))
        for joint in ('yaw','hip','knee'):
            for kind,shape in envelopes.items():
                if joint=='yaw':s=pose(shape,angle,origin)
                elif joint=='hip':s=pose(shoulder(shape),angle,origin)
                else:s=pose(pitch(knee(shape),P['femur_up_deg']).translate((P['coxa'],0,0)),angle,origin)
                if joint=='hip':s=s.rotate(origin,(origin[0],origin[1],1),yaw)
                elif joint=='knee':
                    s=turn(s,hip,-(pitch_angle-15))
                    s=s.rotate(origin,(origin[0],origin[1],1),yaw)
                hits=[];bb=s.BoundingBox()
                for name,other,ob in parts:
                    if overlap(bb,ob):
                        v=s.intersect(other).Volume()
                        if v>.1:hits.append([name,round(v,2)])
                rows.append(dict(leg=leg,joint=joint,envelope=kind,yaw=yaw,
                                 hip=pitch_angle,knee_relative=flex,hits=hits))
        print('Cable sweep',leg,yaw,pitch_angle,flex,flush=True)
report={'assumptions_mm':{'plug_x':[-21,-10.5],'plug_width_total':20.5,
                          'plug_exterior_projection':12.5,'dummy_horn_outer_span':36.5},
        'positions':len(rows),'collisions':[r for r in rows if r['hits']]}
(ROOT/'build/cable_validation.json').write_text(json.dumps(report,indent=2))
print('CABLE COLLISIONS',len(report['collisions']),'/',len(rows),flush=True)
