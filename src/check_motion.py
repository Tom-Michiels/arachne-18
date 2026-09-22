from pathlib import Path
import cadquery as cq, json, math, itertools
BASE=Path(__file__).resolve().parent
OUT=BASE.parent/'build'
OUT.mkdir(exist_ok=True)
CACHE=OUT/'.cad_cache'
meta=json.loads((CACHE/'placed.json').read_text())
params=json.loads((OUT/'parameters.json').read_text())
items=[]
for o in meta:
    if o['kind'] not in ('printed','servo'):continue
    o['shape']=cq.Shape.importBrep(str(CACHE/o['file']))
    items.append(o)
def overlaps(a,b):
    return all(getattr(a,k+'max')>getattr(b,k+'min')+.01 and getattr(b,k+'max')>getattr(a,k+'min')+.01 for k in 'xyz')
rows=[]
for leg,angle,yaws in [(1,45,[-64,-35,0,35]),
                       (2,90,[-35,0,35]),
                       (3,135,[-35,0,35,64])]:
    t=math.radians(angle); root=(params['anchor_rx']*math.cos(t),params['anchor_ry']*math.sin(t),0)
    hip=(root[0]+params['coxa']*math.cos(t),root[1]+params['coxa']*math.sin(t),0)
    knee=(hip[0]+params['femur']*math.cos(math.radians(params['femur_up_deg']))*math.cos(t),
          hip[1]+params['femur']*math.cos(math.radians(params['femur_up_deg']))*math.sin(t),
          params['femur']*math.sin(math.radians(params['femur_up_deg'])))
    axis=(-math.sin(t),math.cos(t),0)
    def turn(s,p,a): return s.rotate(p,tuple(p[i]+axis[i] for i in range(3)),a)
    for yaw,pitch,flex in itertools.product(yaws,[0,15,30],[-95,-80,-65]):
        parts=[]
        for o in items:
            s=o['shape']; g=o['group']; moving=g and g.startswith(f'L{leg}_')
            if moving:
                if g.endswith('TIBIA'):s=turn(s,knee,-(flex+80))
                if g.endswith(('FEMUR','TIBIA')):s=turn(s,hip,-(pitch-15))
                s=s.rotate(root,(root[0],root[1],1),yaw)
            parts.append((o,s,s.BoundingBox(),moving))
        hits=[]
        for i,(a,sa,ba,ma) in enumerate(parts):
            for b,sb,bb,mb in parts[i+1:]:
                if not (ma or mb) or a['group']==b['group'] or not overlaps(ba,bb):continue
                v=sa.intersect(sb).Volume()
                if v>.2:hits.append([a['name'],b['name'],round(v,2)])
        row=dict(leg=leg,yaw=yaw,hip=pitch,knee_relative=flex,collisions=hits)
        rows.append(row)
        print(leg,yaw,pitch,flex,'OK' if not hits else hits,flush=True)
(OUT/'motion_validation.json').write_text(json.dumps(rows,indent=2))
print('PASS',sum(not r['collisions'] for r in rows),'/',len(rows),flush=True)
