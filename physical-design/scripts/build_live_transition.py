"""Photo-matched overhead cable insertion blocking shot. Blender 4.5 Workbench.

Geometry is a visual proxy traced from the supplied prototype photograph, not
production CAD. The phone front is a neutral, uncased iPhone-sized proxy; this
shot deliberately does not pretend that the previous Pro Max is the user's 16.
"""
import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'visualization'
OUT.mkdir(exist_ok=True)
S = .00030  # photo pixels to scene meters; composition scale, not metrology
PHOTO_W, PHOTO_H = 1362, 1002
CROP_Y, CROP_H = 118, 766.125
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'
random.seed(19)


def pos(x, y, z=0): return Vector((x*S, -y*S, z*S))


def color(hexcode):
    values = [int(hexcode[i:i+2],16)/255 for i in (1,3,5)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values)+(1,)


def group(name):
    obj = bpy.data.objects.new(name, None); scene.collection.objects.link(obj)
    obj.empty_display_size = .005
    return obj


def box(name, xy, size, z, depth, tint, radius=1, parent=None, rotation=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos(*xy,z))
    obj=bpy.context.object; obj.name=name
    obj.dimensions=(size[0]*S,size[1]*S,depth*S)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if radius:
        b=obj.modifiers.new('Edge radius','BEVEL');b.width=min(radius,depth*.48)*S;b.segments=3
        obj.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    obj.rotation_euler.z = -math.radians(rotation)
    obj.color = color(tint)
    if parent: obj.parent = parent
    return obj


def rounded_plate(name, center, size, radius, z, depth, tint, rotation=0):
    # A shallow rounded rectangle needs its XY corner radius independent of thickness.
    w,h=size; vertices=[]
    for layer in (-depth/2,depth/2):
        for cx,cy,initial in [(w/2-radius,h/2-radius,0),(-w/2+radius,h/2-radius,90),
                               (-w/2+radius,-h/2+radius,180),(w/2-radius,-h/2+radius,270)]:
            for k in range(13):
                a=math.radians(initial+k*90/12)
                x=cx+radius*math.cos(a);y=cy+radius*math.sin(a)
                a2=math.radians(rotation)
                vertices.append(pos(center[0]+x*math.cos(a2)-y*math.sin(a2),
                                    center[1]+x*math.sin(a2)+y*math.cos(a2),z+layer))
    n=len(vertices)//2
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj);obj.color=color(tint)
    return obj


def disk(name,xy,r,z,depth,tint):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r*S,depth=depth*S,location=pos(*xy,z))
    obj=bpy.context.object;obj.name=name;obj.color=color(tint)
    return obj


def cable(name, points, r, tint, resolution=12):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.resolution_u=resolution
    data.bevel_depth=r*S;data.bevel_resolution=4
    spline=data.splines.new('BEZIER');spline.bezier_points.add(len(points)-1)
    for p,xyz in zip(spline.bezier_points,points):
        p.co=pos(*xyz);p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.color=color(tint)
    return obj,spline


# Small board stack with the visible modem shield, USB cages and antenna.
rounded_plate('Prototype | Raspberry Pi board proxy',(300,464),(211,306),8,23,5,'#1C6647')
rounded_plate('Prototype | blue LTE HAT proxy',(299,501),(219,241),7,73,6,'#154A70')
for x,y in [(204,391),(389,391),(205,609),(391,608)]:
    disk('HAT | mounting eyelet',(x,y),7,77,1.5,'#C4B477')
    disk('HAT | mounting bore',(x,y),3.8,78,1,'#172026')
for x in (228,297,363):
    box('Pi | connector cage',(x,335),(57,77),50,38,'#B6BAB4',3)
    box('Pi | connector opening',(x,304),(43,13),71,2,'#293130',1)
    for offset in (-11,11):
        box('Pi | connector internal contact',(x+offset,305),(4,11),73,2,'#C2B789',.5)
for x in range(206,390,12):
    box('Pi | GPIO spacer',(x,378),(7,8),53,13,'#262D2E',.7)
    box('Pi | GPIO pin',(x,378),(2,4),62,3,'#B29E58',.4)
box('Modem | shield solder perimeter',(279,488),(139,117),82,5,'#BDB280',2)
box('Modem | large RF shield',(279,488),(128,108),88,13,'#C0C3BD',3)
for y in range(438,543,9):
    for x in (215,343):box('Modem | shield edge castellations',(x,y),(4,4),86,2,'#DDD5B4',.4)
box('HAT | controller',(294,588),(25,22),82,7,'#242B2D',1.3)
box('HAT | SIM cage',(294,610),(87,12),81,5,'#A0A7A6',1)
for cx,cy,w,h in [(319,410,26,29),(361,410,16,22),(244,416,16,18),(367,554,22,19)]:
    box('HAT | IC',(cx,cy),(w,h),81,7,'#272D2E',1)
for x,y in [(302,405),(278,411)]:box('HAT | capacitor',(x,y),(10,16),82,7,'#BCAE73',1)
for row_y in (562,573,598,609):
    for x in (220,234,249,334,348,365,378):
        box('HAT | passive component',(x+random.uniform(-1,1),row_y),(5,4),79,2,'#ACB8AC',.4)
for y in (442,454,508,522,539,583):
    for x in (207,375,389):
        box('HAT | small resistor',(x,y),(4,7),79,2,'#C1C8B9',.4)
for x,y in [(239,393),(236,609)]:
    disk('HAT | red status indicator',(x,y),4,82,3,'#E9514F')
for x,y in [(397,463),(392,504),(392,537)]:
    disk('HAT | RF connector',(x,y),8,83,9,'#BDA764')
    disk('HAT | RF socket center',(x,y),3,89,1,'#5F5C42')
box('HAT | top side USB socket',(389,421),(30,24),84,10,'#BBBFBA',2)
box('HAT | data port',(405,575),(18,36),69,24,'#AEB5AD',3)
box('HAT | data port opening',(414,575),(3,24),80,2,'#1A2227',.5)
cable('Antenna | knurled adapter',[(408,465,88),(437,465,88),(476,465,88),(503,472,88),(518,472,88)],14,'#20292A')
for x in range(428,478,6):
    box('Antenna | collar',(x,465),(3,28),88,24,'#353B37',1)
antenna_poly=[(494,460),(507,432),(538,342),(550,333),(558,343),(563,374),(536,469),(524,485),(511,484)]
verts=[pos(x,y,z) for z in (82,104) for x,y in antenna_poly];n=len(antenna_poly)
faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
mesh=bpy.data.meshes.new('Antenna silhouette');mesh.from_pydata(verts,[],faces);mesh.update()
ant=bpy.data.objects.new('Prototype | external LTE antenna proxy',mesh);scene.collection.objects.link(ant)
ant.color=color('#202927');mod=ant.modifiers.new('Soft antenna edges','BEVEL');mod.width=2*S;mod.segments=3

# Screen-up, uncased neutral phone silhouette matched to this photo, not dimensional CAD.
phone_center=(1084,459); phone_angle=-2.6
rounded_plate('Phone | uncased frame proxy',phone_center,(253,525),39,18,25,'#515B60',phone_angle)
rounded_plate('Phone | thin glass perimeter',phone_center,(248,519),37,32,2,'#8A9290',phone_angle)
rounded_plate('Phone | black screen',phone_center,(243,514),35,33.2,1,'#181E22',phone_angle)
rounded_plate('Phone | dark island',(1074,225),(66,17),8,34,1,'#12171A',phone_angle)
box('Phone | volume control',(951,365),(5,58),19,9,'#687173',1,rotation=phone_angle)
box('Phone | USB-C opening',(1096,722),(32,7),18,12,'#12181B',2,rotation=phone_angle)

# Both plugs move along their insertion axes. Their cable remains one continuous curve.
pi_plug=group('Cable | modem end insertion')
phone_plug=group('Cable | phone end insertion')
box('Cable | modem metal tip',(414,575),(18,23),74,13,'#AFB6B6',2,pi_plug)
box('Cable | modem white grip',(443,575),(52,33),73,20,'#E8E9DC',5,pi_plug)
box('Cable | modem strain relief',(471,575),(14,19),72,15,'#D6D9CC',4,pi_plug)
box('Cable | phone metal tip',(1096,723),(24,19),18,12,'#B6BEBB',2,phone_plug,phone_angle)
box('Cable | phone white grip',(1098,747),(33,48),18,19,'#E8E9DC',5,phone_plug,phone_angle)
box('Cable | phone strain relief',(1100,778),(20,18),16,14,'#D4D8CF',4,phone_plug,phone_angle)
points=[(474,575,71),(530,596,47),(591,664,25),(622,771,10),(632,869,7),
        (618,1007,7),(717,1160,7),(968,1158,7),(1109,1046,7),(1122,936,7),(1107,835,7),(1100,785,15)]
wire,spline=cable('Cable | continuous flexible USB link',points,5.8,'#E3E5DA',18)
box('Table | plain blocking surface',(681,501),(2400,2000),-8,6,'#A5A398',0)

# Workbench is intentionally used: plain colors, no product PBR shaders.
scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100
scene.render.fps=24;scene.frame_start=1;scene.frame_end=96
scene.display.render_aa='16'
sh=scene.display.shading;sh.light='STUDIO';sh.studio_light='paint.sl';sh.color_type='OBJECT'
sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH'
sh.curvature_ridge_factor=.6;sh.curvature_valley_factor=.7
sh.show_specular_highlight=False;sh.show_object_outline=False
sh.background_type='WORLD';scene.world=bpy.data.worlds.new('Plain preview background')
scene.world.color=color('#A5A398')[:3]
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
bpy.ops.object.camera_add(location=pos(PHOTO_W/2,CROP_Y+CROP_H/2,2500))
camera=bpy.context.object;camera.name='Camera | locked photo-aligned overhead'
camera.rotation_euler=(0,0,0);camera.data.type='ORTHO';camera.data.ortho_scale=PHOTO_W*S
camera.data.clip_start=.001;camera.data.clip_end=10;scene.camera=camera
image=bpy.data.images.load(str(ROOT/'references/live-transition/prototype-phone-photo.png'))
image.pack()
bg=camera.data.background_images.new();bg.image=image;bg.alpha=.35
bg.show_background_image=False
camera['composition_reference']='Full-width crop: original image y=118..884.125, 1362 x 766.125 -> 960 x 540'


def smooth(t):
    t=max(0,min(1,t));return 6*t**5-15*t**4+10*t**3


checks=[]
for frame in range(1,97):
    t=smooth((frame-16)/56)
    pi_gap=65*(1-t);phone_gap=70*(1-t)
    pi_plug.location=pos(pi_gap,0,0);phone_plug.location=pos(phone_gap*.045,phone_gap,0)
    for obj in (pi_plug,phone_plug):obj.keyframe_insert('location',frame=frame)
    coords=[]
    for i,xyz in enumerate(points):
        x,y,z=xyz
        if i<3:x+=pi_gap*(1-i/3);y+=math.sin(math.pi*t)*5*(i/3)
        if i>8:y+=phone_gap*((i-8)/3);x+=phone_gap*.045*((i-8)/3)
        coords.append(pos(x,y,z))
    for i,p in enumerate(spline.bezier_points):
        p.handle_left_type='FREE';p.handle_right_type='FREE';p.co=coords[i]
        if i==0:tangent=pos(24,0,0)
        elif i==len(coords)-1:tangent=pos(-1.2,-25,0)
        else:tangent=(coords[i+1]-coords[i-1])/6
        p.handle_left=coords[i]-tangent;p.handle_right=coords[i]+tangent
        for prop in ('co','handle_left','handle_right'):p.keyframe_insert(prop,frame=frame)
    checks.append({'frame':frame,'modem_insertion_remaining_px':pi_gap,'phone_insertion_remaining_px':phone_gap})
for block in [pi_plug,phone_plug,wire.data]:
    action=block.animation_data.action
    curves=list(action.fcurves) if action.is_action_legacy else [fc for l in action.layers for s in l.strips for b in s.channelbags for fc in b.fcurves]
    for fc in curves:
        for k in fc.keyframe_points:k.interpolation='LINEAR'
assert checks[-1]['modem_insertion_remaining_px']==0 and checks[-1]['phone_insertion_remaining_px']==0
for frame,name in [(1,'Overhead reference composition'),(16,'Begin both insertions'),(72,'Both plugs seated'),(96,'Photo transition starts in edit')]:
    scene.timeline_markers.new(name,frame=frame)
scene['shot_kind']='Photo-matched overhead cable connection; illustrative prototype geometry'
scene['final_phone_case']='none, user confirmed'
scene['photo_is_placeholder']='Supplied photo has a case. Replace with first frame of the actual uncased-phone recording for final alignment.'
scene['premium_shaders']='Not used or modified; preserved in Product-keynote-v04.blend'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.overlay.show_overlays=False
scene.frame_set(96)
scene.render.filepath=str(OUT/'live-transition-frames-v06'/'overhead_')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Overhead-photo-transition-v06.blend'),compress=True)
report={'status':'shot_ready','resolution':[960,540],'fps':24,'CG_frames':96,'edit_seconds':8,
        'insertions_frames':[16,72],'CG_hold_frames':[72,96],'photo_transition_seconds':[4,6],
        'photo_hold_seconds':[6,8],'photo_crop_original_px':[0,CROP_Y,PHOTO_W,CROP_H],
        'geometry':'Photo-matched visual proxies, not production CAD','phone_case':False,
        'reference_photo_contains_case':True,'single_continuous_cable':True,'motion_checks':checks}
(OUT/'live-transition-v06.json').write_text(json.dumps(report,indent=2))
for frame,name in [(1,'overhead-disconnected-v06.png'),(96,'overhead-connected-v06.png')]:
    scene.frame_set(frame);scene.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True)
print('OVERHEAD_SCENE_READY',flush=True)
