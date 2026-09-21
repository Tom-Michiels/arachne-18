"""ARACHNE 18, mechanical CAD build source. Units mm. CadQuery 2.8.
Generated for 18 Feetech STS3215 12 V servos with supplied 20 mm / PCD14 horns.
Servo geometry is a conservative simplified reference, not a manufacturer solid.
"""
from pathlib import Path
import cadquery as cq
import math, json, csv

BASE=Path(__file__).resolve().parent
OUT=BASE.parent/'build'
OUT.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)
(OUT/'STL').mkdir(exist_ok=True)
(OUT/'STEP_parts').mkdir(exist_ok=True)
P=dict(body_rx=94,body_ry=92,anchor_rx=86,anchor_ry=86,coxa=50,femur=78,tibia=110, horn_pcd=14,
       horn_d=19.95,cheek_gap=45,cheek_t=4.5,servo_L=45.23,servo_W=24.73,
       servo_H=35,servo_axis_offset=12.5,battery_L=115,battery_W=40,battery_H=35,
       femur_up_deg=15,tibia_down_deg=65)
V=cq.Vector

def box(x,y,z,dx,dy,dz):
    return cq.Workplane('XY').box(dx,dy,dz).translate((x,y,z)).val()
def cyl(x,y,z,r,h):
    return cq.Solid.makeCylinder(r,h,V(x,y,z))
def union(*shapes):
    return shapes[0].fuse(*shapes[1:]).clean()
def cut(s,*tools):
    return s.cut(*tools).clean()
def rr(x,y,z,L,W,H,r=3):
    return cq.Workplane('XY').box(L,W,H).edges('|Z').fillet(r).val().translate((x,y,z))
def ellipse(rx,ry,z,h):
    return cq.Workplane('XY').workplane(offset=z).ellipse(rx,ry).extrude(h).val()
def slot(x,y,z,L,W,H,angle=0):
    return cq.Workplane('XY').workplane(offset=z).center(x,y).slot2D(L,W,angle).extrude(H).val()
def xz_profile(points,y,thickness):
    # coordinates in X,Z; extrusion in negative Y
    return cq.Workplane('XZ',origin=(0,y,0)).polyline(points).close().extrude(thickness).val()
def hole_y(x,y,z,r,h):
    return cq.Solid.makeCylinder(r,h,V(x,y,z),V(0,1,0))
def pose(s,angle=0,pos=(0,0,0)):
    return s.rotate((0,0,0),(0,0,1),angle).translate(pos)
def shoulder(s):
    # local servo X -> world Z, Y -> world X, Z -> world Y
    return s.rotate((0,0,0),(1,1,1),-120).translate((P['coxa'],0,0))
def knee(s):
    # local servo X -> X, Y -> -Z, Z -> Y
    return s.rotate((0,0,0),(1,0,0),-90).translate((P['femur'],0,0))
def pitch(s,a):
    return s.rotate((0,0,0),(0,1,0),-a)

def cradle():
    # Open output end, exposed connector end, bolted removable cap at tail.
    s=union(rr(-25,0,-19.75,28,42,3.5,2),
       box(-25,-14.55,-0.45,28,3.7,35.1),box(-25,14.55,-0.45,28,3.7,35.1),
       box(-37.3,0,-0.45,3.4,29.1,35.1))
    for x in (-31,-20):
        for y in (-18.3,18.3):
            s=union(s,cyl(x,y,-21.5,3.7,38.6))
            s=cut(s,cyl(x,y,11.5,2.1,6))
    s=cut(s,box(-23,0,-20,19,17,6))
    # cable tie / motor ventilation openings in the fixed end
    s=cut(s,box(-38,0,0,7,15,16))
    return s
def cap():
    s=rr(-25.5,0,19.55,21,42,3.5,2)
    s=cut(s,rr(-25.5,0,19.5,12,18,8,2))
    for x in (-31,-20):
        for y in (-18.3,18.3): s=cut(s,cyl(x,y,17,1.7,8))
    return s
def servo():
    # Axis at X=0. Casing maximum envelope, output-face relief around horns.
    s=rr(-12.5,0,0,45.23,24.73,32,1.8)
    s=union(s,rr(-26,0,0,17,24.4,35,1.3),cyl(0,0,-18.3,3,36.6))
    s=cut(s,box(-13,0,-16,12,15,4))
    return s
def disc(z):
    s=cyl(0,0,z,9.975,2.5)
    for a in (0,90,180,270):
        s=cut(s,cyl(7*math.cos(math.radians(a)),7*math.sin(math.radians(a)),z-1,1.5,5))
    return cut(s,cyl(0,0,z-1,3.1,5))
def shim(th=2.5):
    s=cyl(0,0,0,10,th)
    for a in (0,90,180,270):
        s=cut(s,cyl(7*math.cos(math.radians(a)),7*math.sin(math.radians(a)),-1,1.7,th+2))
    return cut(s,cyl(0,0,-1,3.2,th+2))
def horn_holes_z(s,z):
    s=cut(s,cyl(0,0,z-1,3.2,7))
    for x,y in ((7,0),(-7,0),(0,7),(0,-7)):
        s=cut(s,cyl(x,y,z-1,1.7,7))
    return s
def horn_holes_y(s,x=0,z=0):
    s=cut(s,hole_y(x,-30,z,3.2,60))
    for dx,dz in ((7,0),(-7,0),(0,7),(0,-7)):
        s=cut(s,hole_y(x+dx,-30,z+dz,1.7,60))
    return s

cr=cradle(); cp=cap(); sv=servo()
anchors=[]
for angle in (45,90,135,225,270,315):
    a=math.radians(angle)
    anchors.append((angle,(P['anchor_rx']*math.cos(a),P['anchor_ry']*math.sin(a),0)))

print('Making chassis',flush=True)
chassis=ellipse(P['body_rx'],P['body_ry'],-25.5,4)
for a,p in anchors:
    notch=union(cyl(0,0,-28,18,10),box(50,0,-23,100,36,10))
    chassis=cut(chassis,pose(notch,a,p))
    chassis=union(chassis,pose(cr,a,p))
# lightening apertures away from load paths
for x in (-36,0,36):
    chassis=cut(chassis,slot(x,0,-27,26,13,8,90))
# four structural pillars with gussets; removable dorsal platform
posts=[(-63,-20),(-63,20),(63,-20),(63,20)]
for x,y in posts:
    chassis=union(chassis,cyl(x,y,-25.5,5.5,50.5))
    chassis=cut(chassis,cyl(x,y,18,2.1,8))

print('Making coxa',flush=True)
# Two separable yaw cheeks, joined by screws outside the servo sweep.
coxa_top=union(cyl(0,0,22.5,14,4.5),rr(22,0,24.75,44,24,4.5,5))
coxa_top=horn_holes_z(coxa_top,22.5)
coxa_bottom=union(cyl(0,0,-27,14,4.5),rr(15,0,-24.75,30,24,4.5,5))
coxa_bottom=horn_holes_z(coxa_bottom,-27)
# Backbone near X=26, connecting yaw cheeks and pitch-servo cradle
coxa_main=union(coxa_top,rr(28,0,0,8,24,45,2),shoulder(cr))
# cradle attachment gussets to backbone, positioned behind pitch axis
coxa_main=union(coxa_main,box(33,0,-17.5,9,22,10),box(36,0,17,16,22,7))
for x,y in ((26,-7),(26,7)):
    coxa_main=cut(coxa_main,cyl(x,y,-24,2.1,8))
    coxa_bottom=cut(coxa_bottom,cyl(x,y,-29,1.7,9))
coxa_main=cut(coxa_main,coxa_bottom.translate((0,0,.2)))

print('Making femur',flush=True)
# Paired sculpted cheeks. Pitch axis origin, knee axis X=78.
def femur_side(y):
    s=union(hole_y(0,y,0,14,4.5),
        xz_profile([(0,-11),(22,-7),(48,-20),(58,-20),(58,13),(37,17),(16,13),(0,14)],y+4.5,4.5))
    s=horn_holes_y(s)
    s=cut(s, xz_profile([(21,-1),(40,-2),(46,4),(34,8),(21,6)],y+5.5,7))
    return s
femur_left=femur_side(-27)
femur_right=femur_side(22.5)
femur_main=union(femur_left,knee(cr),box(47,-22,0,23,6,24))
# separable opposite cheek fastens onto two cross-ties around the casing
for x,z in ((32,10),(32,-8)):
    tie=hole_y(x,-24,z,4.5,46)
    femur_main=union(femur_main,tie)
    femur_main=cut(femur_main,hole_y(x,15,z,2.1,9))
    femur_right=cut(femur_right,hole_y(x,21,z,1.7,9))

print('Making tibia',flush=True)
# Organic fork. Side silhouette, intersected with narrowing plan profile.
side=union(hole_y(0,-27,0,14,54),xz_profile([
 (0,14),(20,15),(42,13),(68,6),(94,-2),(111,-7),(114,-12),
 (108,-17),(88,-13),(64,-8),(40,-7),(18,-10),(0,-14)],27,54))
outer=cq.Workplane('XY').polyline([(-16,-27),(22,-27),(67,-9),(114,-6),
    (116,6),(67,9),(22,27),(-16,27)]).close().extrude(60).translate((0,0,-30)).val()
tibia=side.intersect(outer).clean()
fork=cq.Workplane('XY').polyline([(-25,-22.5),(20,-22.5),(64,0),
    (20,22.5),(-25,22.5)]).close().extrude(70).translate((0,0,-35)).val()
tibia=cut(tibia,fork)
tibia=horn_holes_y(tibia)
# Tie-down eyes, and a transverse M3 bolt for the TPU foot.
for x,z in ((76,-1),(99,-8)): tibia=cut(tibia,hole_y(x,-35,z,1.7,70))
foot=union(rr(108,0,-13,18,19,18,7),box(102,0,-7,10,16,8))
foot=cut(foot,tibia, hole_y(99,-20,-8,1.7,40))
# A slit lets the TPU cover fit over the toe. The foot retention eye uses X=108.
tibia=cut(tibia,hole_y(108,-25,-10,1.7,50))
foot=cut(foot,hole_y(108,-25,-10,1.7,50))

print('Making dorsal compartment',flush=True)
deck=ellipse(83,51,25,3.5)
for a,p in anchors: deck=cut(deck,pose(cyl(0,0,24,18,7),a,p))
for x,y in posts: deck=cut(deck,cyl(x,y,24,1.7,8))
earpts=[(-66,-36),(-66,36),(66,-36),(66,36)]
for x,y in earpts:
    deck=union(deck,cyl(x,y,25,7,3.5))
    deck=cut(deck,cyl(x,y,24,2.1,6))
# Battery cradle has 115 x 40 x 35 unobstructed envelope. Extra 1 mm lateral margin.
tray=rr(0,0,30,122,47,3,3)
tray=union(tray,box(0,-22.25,37,122,2.5,14),box(0,22.25,37,122,2.5,14),
    box(-59.75,0,37,2.5,44.5,14),box(59.75,0,37,2.5,44.5,14))
for x in (-38,38):
    for y in (-20,20): tray=cut(tray,slot(x,y,27,18,3,20))
for x,y in ((-52,-17),(-52,17),(52,-17),(52,17)):
    tray=cut(tray,cyl(x,y,27,1.7,8)); deck=cut(deck,cyl(x,y,24,2.1,6))
# Universal removable electronics deck on four posts, independent of battery straps.
elec=rr(0,0,73.5,108,75,3,5)
eposts=[(-48,-31),(-48,31),(48,-31),(48,31)]
for x,y in eposts:
    deck=union(deck,cyl(x,y,28,4.5,44))
    deck=cut(deck,cyl(x,y,65,2.1,8))
    elec=cut(elec,cyl(x,y,71,1.7,8))
for y in (-24,-12,0,12,24):
    for x in (-32,0,32): elec=cut(elec,slot(x,y,71,23,3.4,7))
# Cable windows and strap anchors in service deck.
for x in (-69,69): deck=cut(deck,slot(x,0,24,18,10,8,90))

def shell_loft(inner=False):
    d=2.6 if inner else 0
    sections=[(28,87,56),(52,85,55),(78,80,53),(96,76,50),(108,58,38),(116,25,16),(118,6,4)]
    if inner: sections=[(z,rx-d,ry-d) for z,rx,ry in sections[:-2]]+[(113.4,24,15),(115.4,5,3)]
    w=cq.Workplane('XY')
    for z,rx,ry in sections:
        w=w.add(cq.Workplane('XY').workplane(offset=z).ellipse(rx,ry).val())
    return w.toPending().loft(combine=True,ruled=False).val()
shell=cut(shell_loft(),shell_loft(True),box(0,0,26,220,180,4.1)).translate((0,0,.6))
for x,y in earpts:
    shell=union(shell,cyl(x,y,28.5,6,3),box(x,y*.94,30,10,8,3))
    shell=cut(shell,cyl(x,y,27,1.7,8))
# Dorsal gills. Through both sides, and an aft XT60/cable service window.
for x in (-36,-18,0,18,36):
    shell=cut(shell,rr(x,0,85,11,130,3.2,1.4))
shell=cut(shell,box(-82,0,41,25,23,14))

# Fit gauge, axial adjustment shims, and universal controller spacers.
gauge=union(cyl(0,0,0,14,4.5),box(22,0,2.25,20,12,4.5))
gauge=horn_holes_z(gauge,0)
for x,r in ((16,1.6),(23,1.7),(30,2.1)): gauge=cut(gauge,cyl(x,0,-1,r,7))
spacer=cut(cyl(0,0,0,3.5,6),cyl(0,0,-1,1.7,8))

prints={
'01_chassis':(chassis,1,'PETG/PA12'), '02_dorsal_deck':(deck,1,'PETG'),
'03_battery_tray':(tray,1,'PETG'), '04_controller_plate':(elec,1,'PETG'),
'05_organic_shell':(shell,1,'PETG'), '06_coxa_bracket':(coxa_main,6,'PETG/PA12'),
'07_coxa_bottom_plate':(coxa_bottom,6,'PETG/PA12'), '08_servo_clamp_cap':(cp,18,'PETG/PA12'),
'09_femur_bracket':(femur_main,6,'PETG/PA12'), '10_femur_side_plate':(femur_right,6,'PETG/PA12'),
'11_tibia_fork':(tibia,6,'PETG/PA12'), '12_foot':(foot,6,'TPU95A'),
'13_horn_shim_2p5':(shim(2.5),36,'PETG'),
'14_controller_spacer':(spacer,4,'PETG'), '15_fit_gauge':(gauge,1,'PETG'),
'16_optional_shim_0p5':(shim(.5),0,'PETG'), '17_optional_shim_1p0':(shim(1),0,'PETG')}

colors={'PETG':(.22,.43,.42),'PETG/PA12':(.15,.30,.30),'TPU95A':(.10,.12,.13)}
assembly=cq.Assembly(name='ARACHNE_18_STS3215_12V')
placed=[]
def add(name,s,kind='printed',color=(.23,.43,.42),group=None):
    assembly.add(s,name=name,color=cq.Color(*color))
    placed.append(dict(name=name,shape=s,kind=kind,group=group,color=color))
for name,s in [('01_CHASSIS',chassis),('02_DORSAL_DECK',deck),('03_BATTERY_TRAY',tray),
              ('04_CONTROLLER_PLATE',elec),('05_SHELL',shell)]: add(name,s,group='BODY')
battery=rr(0,0,49,115,40,35,2)
pcb=rr(0,0,81.8,90,60,1.6,2)
board_envelope=rr(0,0,90,90,60,18,2)
add('REF_3S_BATTERY_115x40x35',battery,'reference',(.73,.49,.12),'BODY')
add('REF_CONTROLLER_90x60x18',board_envelope,'reference',(.23,.43,.68),'BODY')
for x,y in [(-32,-24),(-32,24),(32,-24),(32,24)]:
    add('PCB_spacer_'+str(x)+'_'+str(y),spacer.translate((x,y,75)),group='BODY')

for i,(a,p) in enumerate(anchors,1):
    root=lambda s:pose(s,a,p)
    fem=lambda s:root(pitch(s,P['femur_up_deg']).translate((P['coxa'],0,0)))
    kneept=(P['coxa']+P['femur']*math.cos(math.radians(P['femur_up_deg'])),0,
            P['femur']*math.sin(math.radians(P['femur_up_deg'])))
    tib=lambda s:root(pitch(s,-P['tibia_down_deg']).translate(kneept))
    group=f'L{i}'
    add(f'L{i}_S{i*3-2:02}_YAW_STS3215',root(sv),'servo',(.19,.20,.22),'BODY')
    add(f'L{i}_yaw_clamp',root(cp),group='BODY')
    add(f'L{i}_coxa',root(coxa_main),group=group+'_COXA')
    add(f'L{i}_coxa_bottom',root(coxa_bottom),group=group+'_COXA')
    add(f'L{i}_S{i*3-1:02}_HIP_STS3215',root(shoulder(sv)),'servo',(.19,.20,.22),group+'_COXA')
    add(f'L{i}_hip_clamp',root(shoulder(cp)),group=group+'_COXA')
    add(f'L{i}_femur',fem(femur_main),group=group+'_FEMUR')
    add(f'L{i}_femur_side_plate',fem(femur_right),group=group+'_FEMUR')
    add(f'L{i}_S{i*3:02}_KNEE_STS3215',fem(knee(sv)),'servo',(.19,.20,.22),group+'_FEMUR')
    add(f'L{i}_knee_clamp',fem(knee(cp)),group=group+'_FEMUR')
    add(f'L{i}_tibia',tib(tibia),group=group+'_TIBIA')
    add(f'L{i}_foot',tib(foot),color=(.10,.12,.13),group=group+'_TIBIA')
    hip_horn=lambda s:pitch(shoulder(s).translate((-P['coxa'],0,0)),P['femur_up_deg']).translate((P['coxa'],0,0))
    knee_horn=lambda s:pitch(knee(s).translate((-P['femur'],0,0)),-P['tibia_down_deg']-P['femur_up_deg']).translate((P['femur'],0,0))
    for j,base,trans in [('yaw',lambda s:s,root),('hip',hip_horn,root),('knee',knee_horn,fem)]:
        horn_group=group+'_'+{'yaw':'COXA','hip':'FEMUR','knee':'TIBIA'}[j]
        for side,z in [('plus',17.5),('min',-20)]:
            add(f'L{i}_{j}_disc_{side}',trans(base(disc(z))),'hardware',(.68,.7,.73),horn_group)
        for side,z in [('plus',20),('min',-22.5)]:
            add(f'L{i}_{j}_shim_{side}',trans(base(shim().translate((0,0,z)))),group=horn_group)

print('Exporting and validating',flush=True)
report={'parameters_mm_deg':P,'parts':{},'intersections':[]}
for name,(s,qty,mat) in prints.items():
    valid=s.isValid(); solids=len(s.Solids()); b=s.BoundingBox()
    report['parts'][name]={'valid':valid,'solids':solids,'quantity':qty,'material':mat,
        'size_mm':[round(b.xlen,2),round(b.ylen,2),round(b.zlen,2)],'solid_volume_cm3':round(s.Volume()/1000,2)}
    print(name,valid,solids,flush=True)
    if not valid or solids!=1: raise RuntimeError('Bad printable solid '+name)
    # Export the part on its minimum-Z plane. Thin sideplates are reoriented flat.
    st=s
    if name in ('09_femur_bracket','10_femur_side_plate','11_tibia_fork'):
        st=st.rotate((0,0,0),(1,0,0),90)
    b=st.BoundingBox(); st=st.translate((-(b.xmin+b.xmax)/2,-(b.ymin+b.ymax)/2,-b.zmin))
    cq.exporters.export(st,str(OUT/'STL'/f'{name}.stl'),tolerance=.07,angularTolerance=.12)
    cq.exporters.export(s,str(OUT/'STEP_parts'/f'{name}.step'))

assembly.export(str(OUT/'ARACHNE_18_assembly.step'))
layout=cq.Assembly(name='ARACHNE_18_print_parts')
for i,(name,(s,qty,mat)) in enumerate(prints.items()):
    b=s.BoundingBox()
    loc=cq.Location(V((i%5)*210-(b.xmin+b.xmax)/2,(i//5)*210-(b.ymin+b.ymax)/2,-b.zmin))
    layout.add(s,name=name,loc=loc,color=cq.Color(*colors[mat]))
layout.export(str(OUT/'ARACHNE_18_parts.step'))

# Cache BREP shapes for independent checks and renders, without repeating booleans.
CACHE=OUT/'.cad_cache'; CACHE.mkdir(exist_ok=True)
for i,o in enumerate(placed):
    o['shape'].exportBrep(str(CACHE/f'{i}.brep'))
    o['file']=f'{i}.brep'
    del o['shape']
(CACHE/'placed.json').write_text(json.dumps(placed,indent=2))
(OUT/'cad_validation.json').write_text(json.dumps(report,indent=2))
(OUT/'parameters.json').write_text(json.dumps(P,indent=2))
with (OUT/'print_bom.csv').open('w') as f:
    w=csv.writer(f); w.writerow(['part','quantity','material','size_X_mm','size_Y_mm','size_Z_mm'])
    for n,d in report['parts'].items():w.writerow([n,d['quantity'],d['material'],*d['size_mm']])
print('DONE',flush=True)
