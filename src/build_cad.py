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
for path in (OUT/'STL').glob('*.stl'):path.unlink()
for path in (OUT/'STEP_parts').glob('*.step'):path.unlink()
P=dict(body_rx=94,body_ry=92,anchor_rx=86,anchor_ry=86,coxa=50,femur=78,tibia=110, horn_pcd=14,
       horn_d=19.95,horn_thickness_driven=2.5,horn_thickness_dummy=2.0,horn_outer_span=36.5,
       cheek_gap=36.9,assembly_clearance_per_side=0.2,cheek_t=5.25,
       servo_L=45.23,servo_W=24.73,shaft_clearance_d=7.2,
       servo_H=35,servo_axis_offset=12.5,battery_L=115,battery_W=40,battery_H=35,
       femur_up_deg=15,tibia_down_deg=65,yaw_inward_limit_deg=64,
       yaw_outward_limit_deg=35,yaw_middle_limit_deg=35,
       insert_hole_d=4.0,insert_length=5.7,button_head_d=5.7,
       button_head_h=1.65,horn_recess_d=6.2,horn_recess_depth=1.5,
       dummy_recess_depth=1.45)
V=cq.Vector
HORN_BOLTS=[(7*math.cos(math.radians(a)),7*math.sin(math.radians(a)))
            for a in (45,135,225,315)]

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
def insert_z(s,x,y,face,up=False):
    """Blind bore measured from the printed mating face; plus/minus Z entry."""
    direction=V(0,0,1 if up else -1)
    return cut(s,cq.Solid.makeCylinder(P['insert_hole_d']/2,6.0,V(x,y,face),direction))
def insert_y(s,x,z,face,positive=False):
    return cut(s,cq.Solid.makeCylinder(P['insert_hole_d']/2,6.0,
                                       V(x,face,z),V(0,1 if positive else -1,0)))
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
            s=union(s,cyl(x,y,-21.5,4.2,38.6))
            s=insert_z(s,x,y,17.1)
    # Both broad faces remain open for the factory bus connector and its
    # plug. The opening is 17 mm wide; it does not rely on a pinched wire.
    s=cut(s,box(-22,0,-20,30,25,7))
    # Cable exit and motor ventilation through the fixed end.
    s=cut(s,box(-38,0,0,7,15,16),plug_clearance,wire_exit_clearance)
    return s
def cap():
    s=rr(-25.5,0,19.55,21,42.5,3.5,2)
    s=cut(s,rr(-25.5,0,19.5,12,18,8,2))
    s=cut(s,box(-13,0,19.5,14,17,8))
    for x in (-31,-20):
        for y in (-18.3,18.3): s=cut(s,cyl(x,y,17,1.7,8))
    return s
def servo():
    # Axis at X=0. Casing maximum envelope, output-face relief around horns.
    s=rr(-12.5,0,-.25,45.23,24.73,32,1.8)
    s=union(s,rr(-26,0,-.25,17,24.4,35,1.3),cyl(0,0,-18.3,3,36.6))
    s=cut(s,box(-13,0,-16,12,15,4))
    return s
def disc(z,thickness):
    s=cyl(0,0,z,9.975,thickness)
    for x,y in HORN_BOLTS:s=cut(s,cyl(x,y,z-1,1.5,5))
    return cut(s,cyl(0,0,z-1,3.3,5))
def horn_holes_z(s,z):
    s=cut(s,cyl(0,0,z-1,P['shaft_clearance_d']/2,20))
    for x,y in HORN_BOLTS:s=cut(s,cyl(x,y,z-1,1.7,18))
    return s
def horn_recess_z(s,outer,down=True,depth=None):
    depth=P['horn_recess_depth'] if depth is None else depth
    for x,y in HORN_BOLTS:
        s=cut(s,cq.Solid.makeCylinder(P['horn_recess_d']/2,
             depth,V(x,y,outer),V(0,0,-1 if down else 1)))
    return s
def horn_holes_y(s,x=0,z=0):
    s=cut(s,hole_y(x,-35,z,P['shaft_clearance_d']/2,70))
    for dx,dz in HORN_BOLTS:
        s=cut(s,hole_y(x+dx,-35,z+dz,1.7,70))
    return s
def horn_recess_y(s,outer,positive=False,depth=None):
    depth=P['horn_recess_depth'] if depth is None else depth
    for x,z in HORN_BOLTS:
        s=cut(s,cq.Solid.makeCylinder(P['horn_recess_d']/2,
             depth,V(x,outer,z),V(0,1 if positive else -1,0)))
    return s
def button_screw(length):
    """Envelope for ISO 7380-1 M3; the hex recess is 2 mm across flats."""
    head=cq.Workplane('XY').circle(2.85).extrude(1.65).edges('>Z').fillet(.65).val()
    s=union(head,cyl(0,0,-length,1.5,length))
    socket=cq.Workplane('XY').workplane(offset=.65).polygon(6,2.3094).extrude(1.2).val()
    return cut(s,socket)
def ruthex_insert():
    # Published RX-M3x5.7 envelope is OD 4.6 x 5.7 mm. Knurl is simplified.
    return cut(cyl(0,0,-5.7,2.3,5.7),cyl(0,0,-5.8,1.5,5.9))
def m3_hex_nut():
    s=cq.Workplane('XY').polygon(6,6.35).extrude(2.4).val()
    return cut(s,cyl(0,0,-.1,1.5,2.6))
def hardware_at(s,face,outward,recess=0):
    rotations={'+z':(0,0),'-z':('x',180),'+y':('x',-90),'-y':('x',90)}
    axis,angle=rotations[outward]
    if axis:s=s.rotate((0,0,0),(1,0,0),angle)
    x,y,z=face
    if outward=='+z':z-=recess
    elif outward=='-z':z+=recess
    elif outward=='+y':y-=recess
    else:y+=recess
    return s.translate((x,y,z))

# Clearance volume for both connectors on the dummy side. Dimensions are a
# conservative nominal envelope based on the owner-provided photograph; the
# printed fit coupon must still be tried with the actual supplied plugs.
plug_clearance=box(-15.75,0,-22.5,10.9,20.9,12.9)
wire_exit_clearance=box(-18,0,-34,6.4,20.9,10.4)
def moving_cable_clearance(s,geometry,axis,angles):
    tools=[g.rotate((0,0,0),axis,a) for g in geometry for a in angles]
    return cut(s,*tools)

cr=cradle(); cp=cap(); sv=servo()
screw6=button_screw(6); screw8=button_screw(8); screw10=button_screw(10); screw25=button_screw(25)
insert=ruthex_insert(); foot_nut=m3_hex_nut()
anchors=[]
for angle in (45,90,135,225,270,315):
    a=math.radians(angle)
    anchors.append((angle,(P['anchor_rx']*math.cos(a),P['anchor_ry']*math.sin(a),0)))

print('Making chassis',flush=True)
chassis=ellipse(P['body_rx'],P['body_ry'],-25.5,4)
for a,p in anchors:
    # A wide swept sector lets the lower coxa plate clear the chassis at ±70°.
    notch=union(cyl(0,0,-28,21,10),box(41.5,0,-23,113,100,10))
    chassis=cut(chassis,pose(notch,a,p))
    chassis=cut(chassis,pose(plug_clearance,a,p))
    chassis=union(chassis,pose(cr,a,p))
# lightening apertures away from load paths
for x in (-36,0,36):
    chassis=cut(chassis,slot(x,0,-27,26,13,8,90))
# four structural pillars with gussets; removable dorsal platform
posts=[(-68,-18),(-68,18),(68,-18),(68,18)]
for x,y in posts:
    chassis=union(chassis,cyl(x,y,-25.5,5.5,50.5))
    chassis=insert_z(chassis,x,y,25)

print('Making coxa',flush=True)
# Two separable yaw cheeks, joined by screws outside the servo sweep.
coxa_top=union(cyl(0,0,18.45,14,5.25),rr(22,0,21.075,44,24,5.25,5))
coxa_top=horn_recess_z(horn_holes_z(coxa_top,18.45),23.7)
coxa_bottom=union(cyl(0,0,-23.7,14,5.25),rr(17,0,-21.075,34,24,5.25,5))
coxa_bottom=horn_recess_z(horn_holes_z(coxa_bottom,-23.7),-23.7,False,P['dummy_recess_depth'])
# Backbone near X=26, connecting yaw cheeks and pitch-servo cradle
coxa_main=union(coxa_top,rr(28,0,0,8,24,45,2),shoulder(cr))
# cradle attachment gussets to backbone, positioned behind pitch axis
coxa_main=union(coxa_main,box(33,0,-17.5,9,22,10),box(36,0,17,16,22,7))
coxa_main=cut(coxa_main,coxa_bottom)
for x,y in ((28,-7),(28,7)):
    coxa_main=insert_z(coxa_main,x,y,-18.45,True)
    coxa_bottom=cut(coxa_bottom,cyl(x,y,-24,1.7,7))
    coxa_main=cut(coxa_main,cyl(x,y,-45,3.4,22.5))
coxa_bottom=moving_cable_clearance(
    coxa_bottom,(plug_clearance,wire_exit_clearance),(0,0,1),range(-64,65,8))

print('Making femur',flush=True)
# Paired sculpted cheeks. Pitch axis origin, knee axis X=78.
def femur_side(y):
    blade=xz_profile([(0,-11),(22,-7),(48,-20),(58,-20),(58,13),(37,17),(16,13),(0,14)],y+5.25,5.25)
    blade=cq.Workplane(obj=blade).edges('|Y').fillet(1.5).val()
    eye=hole_y(0,y,0,14,5.25)
    s=union(eye,blade)
    s=horn_holes_y(s)
    s=cut(s,cq.Workplane('XZ',origin=(32,y+5.75,3)).slot2D(27,7).extrude(7).val())
    return s
femur_left=horn_recess_y(femur_side(-23.7),-23.7,True,P['dummy_recess_depth'])
femur_right=horn_recess_y(femur_side(18.45),23.7)
# Both cheeks flare out locally around the knee servo and its removable cap.
# The hip eyes remain narrow and seat directly against the supplied horns.
distal_outline=[(35,-12),(42,-20),(58,-20),(58,13),(37,17)]
femur_left=cut(femur_left,box(53,-20.025,0,22,3.15,46))
femur_left=union(femur_left,xz_profile(distal_outline,-21.6,5.25))
hip_plug=pitch(shoulder(plug_clearance).translate((-P['coxa'],0,0)),-P['femur_up_deg'])
hip_wire=pitch(shoulder(wire_exit_clearance).translate((-P['coxa'],0,0)),-P['femur_up_deg'])
femur_left=moving_cable_clearance(femur_left,(hip_plug,hip_wire),(0,1,0),range(-40,41,8))
femur_right=cut(femur_right,box(53,20.025,0,22,3.15,46))
femur_right=union(femur_right,xz_profile(distal_outline,26.85,5.25))
femur_main=union(femur_left,knee(cr),box(47,-22,0,23,6,24))
femur_main=cut(femur_main,knee(plug_clearance),knee(wire_exit_clearance))
# End relief on both sides of the knee cradle: the symmetric tibia cheeks
# otherwise graze its forward lip at maximum negative knee travel.
femur_main=cut(femur_main,box(67,-20,0,10,5,42),box(67,20,0,10,5,42))
# The two cross-ties seat directly against the removable cheek (no 0.5 mm gap).
# Knee-cap service ports clear both the DIN 7380 head and a straight hex driver.
for x,z in ((32,10),(32,-8)):
    tie=hole_y(x,-20,z,4.5,38.45)
    femur_main=union(femur_main,tie)
    femur_main=insert_y(femur_main,x,z,18.45)
    femur_right=cut(femur_right,hole_y(x,18,z,1.7,7))
for x in (P['femur']-31,P['femur']-20):
    for z in (-18.3,18.3):
        femur_right=cut(femur_right,hole_y(x,21,z,4.0,7))
# Contact bosses bridge the 0.2 mm print allowance to the knee cap.
for z in (-10,10):
    femur_right=union(femur_right,hole_y(44,21.3,z,2.5,.3))

print('Making tibia',flush=True)
# Organic fork. Side silhouette, intersected with narrowing plan profile.
side=union(hole_y(0,18.45,0,14,5.25),xz_profile([
 (0,14),(20,15),(42,13),(68,6),(94,-2),(111,-7),(114,-12),
 (108,-17),(88,-13),(64,-8),(40,-7),(18,-10),(0,-14)],23.7,47.4))
outer=cq.Workplane('XY').polyline([(-16,-23.7),(22,-23.7),(67,-9),(114,-6),
    (116,6),(67,9),(22,23.7),(-16,23.7)]).close().extrude(60).translate((0,0,-30)).val()
tibia=side.intersect(outer).clean()
fork=cq.Workplane('XY').polyline([(-25,-18.45),(20,-18.45),(64,0),
    (20,18.45),(-25,18.45)]).close().extrude(70).translate((0,0,-35)).val()
tibia=cut(tibia,fork)
# Each horn needs a complete annular eye on both faces. The side silhouette
# begins at X=0, so the dummy eye must be added explicitly after the fork cut.
tibia=union(tibia,hole_y(0,-23.7,0,14,5.25))
tibia=horn_recess_y(horn_recess_y(horn_holes_y(tibia),-23.7,True,P['dummy_recess_depth']),23.7)
# Tie-down eyes, and a transverse M3 bolt for the TPU foot.
for x,z in ((76,-1),(99,-8)): tibia=cut(tibia,hole_y(x,-35,z,1.7,70))
foot=union(rr(108,0,-13,18,19,18,7),box(102,0,-7,10,16,8))
foot=cut(foot,tibia, hole_y(99,-20,-8,1.7,40))
# A slit lets the TPU cover fit over the toe. The foot retention eye uses X=108.
tibia=cut(tibia,hole_y(108,-25,-10,1.7,50))
foot=cut(foot,hole_y(108,-25,-10,1.7,50))
knee_plug=pitch(knee(plug_clearance).translate((-P['femur'],0,0)),80)
knee_wire=pitch(knee(wire_exit_clearance).translate((-P['femur'],0,0)),80)
tibia=moving_cable_clearance(tibia,(knee_plug,knee_wire),(0,1,0),range(-15,81,5))

def check_horn_bearings():
    """Require real print material under every head on both horn faces."""
    checks=[('coxa driven',coxa_top,'z',23.7,-1,P['horn_recess_depth']),
            ('coxa dummy',coxa_bottom,'z',-23.7,1,P['dummy_recess_depth']),
            ('hip dummy',femur_left,'y',-23.7,1,P['dummy_recess_depth']),
            ('hip driven',femur_right,'y',23.7,-1,P['horn_recess_depth']),
            ('knee dummy',tibia,'y',-23.7,1,P['dummy_recess_depth']),
            ('knee driven',tibia,'y',23.7,-1,P['horn_recess_depth'])]
    report=[]
    for label,shape,axis,outer,direction,recess in checks:
        missing=[];samples=0
        for bolt,(u,v) in enumerate(HORN_BOLTS,1):
            for depth in (recess+.45,4.5):
                for radius in (2.1,2.7):
                    for angle in range(0,360,30):
                        a=math.radians(angle)
                        uu=u+radius*math.cos(a);vv=v+radius*math.sin(a)
                        point=(uu,vv,outer+direction*depth) if axis=='z' else (uu,outer+direction*depth,vv)
                        samples+=1
                        if not shape.isInside(V(*point),.015):
                            missing.append((bolt,round(depth,2),radius,angle))
        report.append(dict(interface=label,samples=samples,missing=missing))
        if missing:raise RuntimeError(f'{label}: {len(missing)} unsupported horn-bearing samples; first {missing[:6]}')
    (OUT/'horn_support_validation.json').write_text(json.dumps(report,indent=2))
    print('Horn bearing support',sum(x['samples'] for x in report),'/',sum(x['samples'] for x in report),flush=True)

check_horn_bearings()

print('Making dorsal compartment',flush=True)
deck=ellipse(83,51,25,3.5)
for a,p in anchors: deck=cut(deck,pose(cyl(0,0,24,18,7),a,p))
for x,y in posts: deck=cut(deck,cyl(x,y,24,1.7,8))
earpts=[(-40,-42),(-40,42),(40,-42),(40,42)]
for x,y in earpts:
    deck=union(deck,cyl(x,y,22,6.5,6.5))
    deck=insert_z(deck,x,y,28.5)
# Battery cradle has 115 x 40 x 35 unobstructed envelope. Extra 1 mm lateral margin.
tray=rr(0,0,30,122,47,3,3)
tray=union(tray,box(0,-22.25,37,122,2.5,14),box(0,22.25,37,122,2.5,14),
    box(-59.75,0,37,2.5,44.5,14),box(59.75,0,37,2.5,44.5,14))
for x in (-38,38):
    for y in (-20,20): tray=cut(tray,slot(x,y,27,18,3,20))
tray_mounts=[(-32,-30),(-32,30),(32,-30),(32,30)]
for x,y in tray_mounts:
    tray=union(tray,cyl(x,y,28.5,5,3),box(x,y*.87,30,12,10,3))
    tray=cut(tray,cyl(x,y,27,1.7,8))
    deck=union(deck,cyl(x,y,22,5,3))
    deck=insert_z(deck,x,y,28.5)
# Universal removable electronics deck on four posts, independent of battery straps.
elec=rr(0,0,73.5,108,75,3,5)
eposts=[(-48,-31),(-48,31),(48,-31),(48,31)]
for x,y in eposts:
    deck=union(deck,cyl(x,y,28,4.5,44))
    deck=insert_z(deck,x,y,72)
    elec=cut(elec,cyl(x,y,71,1.7,8))
for y in (-24,-12,0,12,24):
    for x in (-32,0,32): elec=cut(elec,slot(x,y,71,23,3.4,7))
# Cable windows and strap anchors in service deck.
for x in (-69,69): deck=cut(deck,slot(x,0,24,18,10,8,90))
# Vertical tool ports keep all yaw clamps reachable after the deck is fitted.
for a,p in anchors:
    for x in (-31,-20):
        for y in (-18.3,18.3):
            v=pose(cyl(x,y,20,4.0,18),a,p)
            deck=cut(deck,v)

def shell_loft(inner=False):
    d=2.6 if inner else 0
    # A forward brow, fuller rear abdomen and gently swept roof make the
    # enclosure read as a carapace while retaining the battery/controller bay.
    sections=[(28,0,87,56),(52,0,85,55),(78,0,80,53),
              (96,-5,76,50),(108,-7,58,38),(116,-8,25,16),(118,-8,6,4)]
    if inner:
        sections=[(z,cx,rx-d,ry-d) for z,cx,rx,ry in sections[:-2]]+[
                  (113.4,-8,24,15),(115.4,-8,5,3)]
    w=cq.Workplane('XY')
    for z,cx,rx,ry in sections:
        w=w.add(cq.Workplane('XY').workplane(offset=z).center(cx,0).ellipse(rx,ry).val())
    return w.toPending().loft(combine=True,ruled=False).val()
shell=cut(shell_loft(),shell_loft(True),box(0,0,26,220,180,4.1)).translate((0,0,.6))
for x,y in earpts:
    shell=union(shell,cyl(x,y,28.5,6,3),
                box(x,y+math.copysign(5,y),30,14,18,3))
    shell=cut(shell,cyl(x,y,27,1.7,8))
# Four vertical access bores emerge through the curved roof over the shell tabs.
# Remove the shell to service the other fasteners.
for x,y in earpts:
    shell=cut(shell,cyl(x,y,31.5,3.5,90))
# Rounded, subtly swept gills on both sides; aft cable/XT60 service window.
for x in (-38,-19,0,19,38):
    vent=cq.Workplane('XZ',origin=(x,70,84-.06*abs(x))).slot2D(12,3.2,-10 if x<0 else 10).extrude(140).val()
    shell=cut(shell,vent)
shell=cut(shell,box(-82,0,41,25,23,14))

# The small coupon checks both the PCD/shaft hole and the 36.9 mm inner span.
gauge=union(cyl(0,0,0,14,5.25),box(29,0,2.625,44,12,5.25),
            box(18,0,2.625,7,43,5.25),
            box(35,19.95,2.625,34,3,5.25),box(35,-19.95,2.625,34,3,5.25))
gauge=horn_recess_z(horn_holes_z(gauge,0),5.25)
for x,r in ((20,2.0),(31,2.05),(42,2.1)):
    gauge=cut(gauge,cyl(x,0,-1,r,7))
spacer=cut(cyl(0,0,0,3.5,6),cyl(0,0,-1,1.7,8))

prints={
'01_chassis':(chassis,1,'PETG/PA12'), '02_dorsal_deck':(deck,1,'PETG'),
'03_battery_tray':(tray,1,'PETG'), '04_controller_plate':(elec,1,'PETG'),
'05_organic_shell':(shell,1,'PETG'), '06_coxa_bracket':(coxa_main,6,'PETG/PA12'),
'07_coxa_bottom_plate':(coxa_bottom,6,'PETG/PA12'), '08_servo_clamp_cap':(cp,18,'PETG/PA12'),
'09_femur_bracket':(femur_main,6,'PETG/PA12'), '10_femur_side_plate':(femur_right,6,'PETG/PA12'),
'11_tibia_fork':(tibia,6,'PETG/PA12'), '12_foot':(foot,6,'TPU95A'),
'13_controller_spacer':(spacer,4,'PETG'), '14_direct_horn_fit_gauge':(gauge,1,'PETG')}

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
steel=(.70,.72,.74); brass=(.70,.50,.19)
tool_paths=[]
def add_m3(name,face,outward,transform,group,length=8,recess=0):
    model={6:screw6,8:screw8,10:screw10,25:screw25}[length]
    add(name,transform(hardware_at(model,face,outward,recess)),
        'fastener',steel,group)
    driver=cyl(0,0,1.65,2.0,100 if name.startswith('BODY_shell_') else 14)
    tool_paths.append((name,transform(hardware_at(driver,face,outward,recess))))
def add_insert(name,face,outward,transform,group):
    add(name,transform(hardware_at(insert,face,outward)),
        'insert',brass,group)
for x,y in posts:
    tag=f'{x}_{y}'
    add_m3(f'BODY_deck_M3x8_{tag}',(x,y,28.5),'+z',lambda s:s,'BODY')
    add_insert(f'BODY_deck_RXM3x5p7_{tag}',(x,y,25),'+z',lambda s:s,'BODY')
for x,y in tray_mounts:
    tag=f'{x}_{y}'
    add_m3(f'BODY_tray_M3x8_{tag}',(x,y,31.5),'+z',lambda s:s,'BODY')
    add_insert(f'BODY_tray_RXM3x5p7_{tag}',(x,y,28.5),'+z',lambda s:s,'BODY')
for x,y in eposts:
    tag=f'{x}_{y}'
    add_m3(f'BODY_controller_M3x8_{tag}',(x,y,75),'+z',lambda s:s,'BODY')
    add_insert(f'BODY_controller_RXM3x5p7_{tag}',(x,y,72),'+z',lambda s:s,'BODY')
for x,y in earpts:
    tag=f'{x}_{y}'
    add_m3(f'BODY_shell_M3x8_{tag}',(x,y,31.5),'+z',lambda s:s,'BODY')
    add_insert(f'BODY_shell_RXM3x5p7_{tag}',(x,y,28.5),'+z',lambda s:s,'BODY')

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
        for side,z,th in [('plus',15.75,2.5),('min',-18.25,2.0)]:
            add(f'L{i}_{j}_disc_{side}',trans(base(disc(z,th))),'hardware',(.68,.7,.73),horn_group)
        for side,z,out,recess in [('plus',23.7,'+z',1.5),('min',-23.7,'-z',P['dummy_recess_depth'])]:
            for k,(hx,hy) in enumerate(HORN_BOLTS,1):
                add_m3(f'L{i}_{j}_{side}_horn_M3x6_{k}',(hx,hy,z),out,
                       lambda s,base=base,trans=trans:trans(base(s)),horn_group,
                       length=6,recess=recess)
    for joint,transform,link_group in (
        ('yaw',root,'BODY'),('hip',lambda s:root(shoulder(s)),group+'_COXA'),
        ('knee',lambda s:fem(knee(s)),group+'_FEMUR')):
        for x in (-31,-20):
            for y in (-18.3,18.3):
                tag=f'{x}_{y}'
                add_m3(f'L{i}_{joint}_clamp_M3x8_{tag}',(x,y,21.3),'+z',transform,link_group)
                add_insert(f'L{i}_{joint}_clamp_RXM3x5p7_{tag}',
                           (x,y,17.1),'+z',transform,link_group)
    for y in (-7,7):
        add_m3(f'L{i}_coxa_join_M3x10_{y}',(28,y,-23.7),'-z',root,group+'_COXA',length=10)
        add_insert(f'L{i}_coxa_join_RXM3x5p7_{y}',
                   (28,y,-18.45),'-z',root,group+'_COXA')
    for z in (10,-8):
        add_m3(f'L{i}_femur_join_M3x10_{z}',(32,23.7,z),'+y',fem,group+'_FEMUR',length=10)
        add_insert(f'L{i}_femur_join_RXM3x5p7_{z}',
                   (32,18.45,z),'+y',fem,group+'_FEMUR')
    add_m3(f'L{i}_foot_M3x25',(108,-9.5,-10),'-y',tib,group+'_TIBIA',25)
    add(f'L{i}_foot_M3_locknut',tib(hardware_at(foot_nut,(108,9.5,-10),'+y')),
        'nut',steel,group+'_TIBIA')

print('Exporting and validating',flush=True)
report={'parameters_mm_deg':P,'parts':{},'intersections':[]}
print('Checking screwdriver access and fastener interference',flush=True)
printed=[o for o in placed if o['kind'] in ('printed','servo','reference')]
printed_boxes=[(o,o['shape'].BoundingBox()) for o in printed]
def bbox_hit(a,b):
    return all(getattr(a,k+'max')>getattr(b,k+'min')+.01 and
               getattr(b,k+'max')>getattr(a,k+'min')+.01 for k in 'xyz')
blocked=[]; colliding=[]
for name,driver in tool_paths:
    bb=driver.BoundingBox()
    for o,ob in printed_boxes:
        if o['name']=='05_SHELL' and not name.startswith('BODY_shell_'):
            continue  # the detachable cover is removed for service
        if bbox_hit(bb,ob) and driver.intersect(o['shape']).Volume()>.05:
            blocked.append([name,o['name']])
for screw in (o for o in placed if o['kind'] in ('fastener','nut')):
    bb=screw['shape'].BoundingBox()
    for o,ob in printed_boxes:
        if bbox_hit(bb,ob) and screw['shape'].intersect(o['shape']).Volume()>.05:
            colliding.append([screw['name'],o['name']])
fastener_report=dict(screw_count=sum(o['kind']=='fastener' for o in placed),
    insert_count=sum(o['kind']=='insert' for o in placed),
    nut_count=sum(o['kind']=='nut' for o in placed),
    insert_hole_d_mm=P['insert_hole_d'],insert_length_mm=P['insert_length'],
    screwdriver_radius_mm=2.0,
    screwdriver_service_condition='Remove dorsal shell except when fitting its four screws',
    screw_print_intersections=colliding,
    blocked_straight_driver_paths=blocked)
(OUT/'fastener_validation.json').write_text(json.dumps(fastener_report,indent=2))
print('Screw/print intersections',len(colliding),'blocked tools',len(blocked),flush=True)
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
