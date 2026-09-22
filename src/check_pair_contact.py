"""Check a coordinated front/rear reach: TPU toes meet, hard parts clear."""
from pathlib import Path
import json, math
import cadquery as cq

ROOT=Path(__file__).resolve().parent.parent
CACHE=ROOT/'build/.cad_cache'
meta=json.loads((CACHE/'placed.json').read_text())
angles={1:45,3:135,4:225,6:315}
parts={i:[] for i in angles};body=[]
for item in meta:
    if item['kind'] not in ('printed','servo','hardware'):
        continue
    shape=cq.Shape.importBrep(str(CACHE/item['file']))
    if item['group']=='BODY':body.append((item['name'],shape))
    elif item['group']:
        for i in parts:
            if item['group'].startswith(f'L{i}_'):
                parts[i].append((item['name'],item['group'],shape))
                break

def pose(i,yaw,hip,knee):
    a=math.radians(angles[i]);d=(math.cos(a),math.sin(a))
    root=(86*d[0],86*d[1],0)
    hippt=(root[0]+50*d[0],root[1]+50*d[1],0)
    kneept=(hippt[0]+78*math.cos(math.radians(15))*d[0],
            hippt[1]+78*math.cos(math.radians(15))*d[1],78*math.sin(math.radians(15)))
    ax=(-d[1],d[0],0)
    def turn(s,p,deg):return s.rotate(p,tuple(p[k]+ax[k] for k in range(3)),deg)
    result=[]
    for name,group,s in parts[i]:
        if group.endswith('_TIBIA'):s=turn(s,kneept,-(knee+80))
        if group.endswith(('_FEMUR','_TIBIA')):s=turn(s,hippt,-(hip-15))
        s=s.rotate(root,(root[0],root[1],1),yaw)
        result.append((name,group,s))
    return result

def intersection(a,b):
    aa=a.BoundingBox();bb=b.BoundingBox()
    if not all(getattr(aa,k+'max')>getattr(bb,k+'min')+.01 and
               getattr(bb,k+'max')>getattr(aa,k+'min')+.01 for k in 'xyz'):
        return 0.
    return a.intersect(b).Volume()

report=[]
for pair,sign in [((1,6),(-1,1)),((3,4),(1,-1))]:
    for step in range(9):
        t=step/8
        yaw=58.3*t;hip=15-35*t;knee=-80+80*t
        left=pose(pair[0],sign[0]*yaw,hip,knee)
        right=pose(pair[1],sign[1]*yaw,hip,knee)
        hard=[];foot_contact=[]
        for na,ga,a in left:
            for nb,gb,b in right:
                v=intersection(a,b)
                if v<.1:continue
                record=[na,nb,round(v,3)]
                if na.endswith('_foot') and nb.endswith('_foot'):
                    foot_contact.append(record)
                else:hard.append(record)
        for legparts in (left,right):
            for na,ga,a in legparts:
                for nb,b in body:
                    v=intersection(a,b)
                    if v>.1:hard.append([na,nb,round(v,3)])
        line=dict(pair=list(pair),fraction=t,yaw_deg=round(yaw,3),
                  hip_deg=round(hip,3),knee_relative_deg=round(knee,3),
                  foot_contact=foot_contact,hard_intersections=hard)
        report.append(line)
        print(pair,step,'toes',len(foot_contact),'hard',len(hard),flush=True)
(ROOT/'build/pair_contact_validation.json').write_text(json.dumps(report,indent=2))
assert all(not x['hard_intersections'] for x in report)
assert all(x['foot_contact'] for x in report if x['fraction']==1)
