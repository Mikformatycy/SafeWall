"""Combine the original simultaneous assembly and the photo-matched prototype.

Run against Product-keynote-v04.blend. Workbench rendering only. A short second
render pass provides the enclosure-to-prototype dissolve without PBR shaders.
"""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector, Quaternion
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'visualization'
scene=bpy.context.scene
assert scene['visual_revision'].startswith('v04')
scene.frame_set(120)
product=bpy.data.objects['SafeWall | product rotation']
product.name='Product | assembly then leftward slide'
product['sequence_role']='enclosure_root'
enclosure=list(product.children_recursive)
for obj in enclosure:obj['sequence_role']='enclosure'
camera=scene.camera
start_location=camera.location.copy()
start_quaternion=camera.rotation_euler.to_quaternion()
start_scale=camera.data.ortho_scale
start_target=Vector((0,0,.016))
end_target=Vector((681*.00030,-(118+766.125/2)*.00030,0))
end_product=Vector((300*.00030,-480*.00030,0))

# Reuse the exact phone, board, antenna and cable placement from the approved
# photo blocking study. No internet or generated image substitutes are needed.
col=bpy.data.collections.new('07 Photo-matched prototype and phone')
scene.collection.children.link(col)
with bpy.data.libraries.load(str(OUT/'Overhead-photo-transition-v06.blend'),link=False) as (src,dst):
    dst.objects=list(src.objects)
imported=[obj for obj in dst.objects if obj]
for obj in imported:col.objects.link(obj)
for obj in list(imported):
    if obj.type=='CAMERA':
        imported.remove(obj);bpy.data.objects.remove(obj,do_unlink=True)

proto=[];phone=[];cable=[]
flat_materials={}
for obj in imported:
    if obj.name.startswith(('Prototype |','HAT |','Pi |','Modem |','Antenna |')):
        obj['sequence_role']='prototype';proto.append(obj)
    elif obj.name.startswith('Phone |'):
        obj['sequence_role']='phone';phone.append(obj)
    elif obj.name.startswith('Cable |'):
        obj['sequence_role']='cable';cable.append(obj)
    if obj.type in {'MESH','CURVE'}:
        key=tuple(round(c,6) for c in obj.color)
        if key not in flat_materials:
            mat=bpy.data.materials.new(f'Preview solid color {len(flat_materials)+1:02d}')
            mat.diffuse_color=obj.color;mat.use_nodes=False;flat_materials[key]=mat
        obj.data.materials.clear();obj.data.materials.append(flat_materials[key])
    if obj.animation_data:obj.animation_data_clear()
    if obj.data and obj.data.animation_data:obj.data.animation_data_clear()
ground=next(o for o in imported if o.name.startswith('Table |'))
ground.scale.x=20;ground.scale.y=20
bpy.data.objects['Seamless studio floor'].hide_render=True
bpy.data.objects['Seamless studio floor'].hide_viewport=True


def empty(name):
    obj=bpy.data.objects.new(name,None);scene.collection.objects.link(obj)
    obj.empty_display_size=.01;return obj


phone_root=empty('Phone | enters while camera widens')
for obj in phone:obj.parent=phone_root
cable_root=empty('Cable | appears from below the frame')
for obj in cable:
    if not obj.parent:obj.parent=cable_root
pi_plug=next(o for o in cable if o.name=='Cable | modem end insertion')
phone_plug=next(o for o in cable if o.name=='Cable | phone end insertion')
wire=next(o for o in cable if o.name=='Cable | continuous flexible USB link')
spline=wire.data.splines[0]
# The reference scene was saved at the fully connected pose.
rest_points=[p.co.copy() for p in spline.bezier_points]

scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100
scene.render.fps=24;scene.render.fps_base=1
scene.frame_start=1;scene.frame_end=276
scene.render.film_transparent=False;scene.use_nodes=False
scene.display.render_aa='16'
sh=scene.display.shading;sh.light='STUDIO';sh.studio_light='paint.sl';sh.color_type='MATERIAL'
sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH'
sh.curvature_ridge_factor=.6;sh.curvature_valley_factor=.7
sh.show_specular_highlight=False;sh.show_object_outline=False
sh.background_type='WORLD';scene.world.color=ground.color[:3]
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0
camera.data.clip_start=.0001;camera.data.clip_end=30
# These viewport colors belong only to this new preview file. The premium
# source file and its shader nodes remain unchanged on disk.
bpy.data.materials['CMF | graphite polymer with polished clearcoat'].diffuse_color=(.15,.18,.22,1)
bpy.data.materials['CMF | piano black gloss cover'].diffuse_color=(.24,.28,.33,1)


def smooth(t):
    t=max(0,min(1,t));return t*t*t*(10+t*(-15+6*t))


def visibility(obj,hidden,frame):
    obj.hide_render=hidden;obj.keyframe_insert('hide_render',frame=frame)


rows=[]
for frame in range(1,277):
    # Preserve the existing assembly transforms and camera for the first 5 s.
    scene.frame_set(min(frame,120))
    p=smooth((frame-120)/48)
    product.location=end_product*p
    product.keyframe_insert('location',frame=frame)
    if frame>120:
        product.rotation_euler.z=math.radians(19)*(1-p)
        product.keyframe_insert('rotation_euler',frame=frame)
        q=start_quaternion.slerp(Quaternion((1,0,0,0)),p)
        target=start_target.lerp(end_target,p)
        distance=(start_location-start_target).length*(1-p)+.75*p
        camera.location=target+q@Vector((0,0,distance))
        camera.rotation_euler=q.to_euler()
        camera.data.ortho_scale=start_scale*(1-p)+.4086*p
        camera.keyframe_insert('location',frame=frame)
        camera.keyframe_insert('rotation_euler',frame=frame)
        camera.data.keyframe_insert('ortho_scale',frame=frame)

    # The phone enters the widening composition. The cable is absent until the
    # prototype replacement is complete, then rises smoothly into staging.
    phone_root.location=(.15*(1-smooth((frame-128)/40)),0,0)
    phone_root.keyframe_insert('location',frame=frame)
    arrive=smooth((frame-192)/24)
    cable_root.location=(0,-.15*(1-arrive),0)
    cable_root.keyframe_insert('location',frame=frame)
    insertion=smooth((frame-218)/34)
    pi_gap=65*(1-insertion);phone_gap=70*(1-insertion)
    pi_plug.location=(pi_gap*.0003,0,0)
    phone_plug.location=(phone_gap*.045*.0003,-phone_gap*.0003,0)
    pi_plug.keyframe_insert('location',frame=frame);phone_plug.keyframe_insert('location',frame=frame)
    coords=[]
    for i,rest in enumerate(rest_points):
        co=rest.copy()
        if i<3:
            co.x+=pi_gap*(1-i/3)*.0003
            co.y-=math.sin(math.pi*insertion)*5*(i/3)*.0003
        if i>8:
            co.y-=phone_gap*((i-8)/3)*.0003
            co.x+=phone_gap*.045*((i-8)/3)*.0003
        coords.append(co)
    for i,point in enumerate(spline.bezier_points):
        point.handle_left_type='FREE';point.handle_right_type='FREE';point.co=coords[i]
        if i==0:tangent=Vector((24*.0003,0,0))
        elif i==len(coords)-1:tangent=Vector((-1.2*.0003,25*.0003,0))
        else:tangent=(coords[i+1]-coords[i-1])/6
        point.handle_left=coords[i]-tangent;point.handle_right=coords[i]+tangent
        for prop in ('co','handle_left','handle_right'):point.keyframe_insert(prop,frame=frame)
    rows.append({'frame':frame,'slide_progress':p,'cable_arrival':arrive,
                 'plug_gap_mm':[pi_gap*.3,phone_gap*.3]})

for obj in enclosure:
    visibility(obj,False,1);visibility(obj,False,192);visibility(obj,True,193)
    if obj.name.startswith(('OLED | battery percentage','OLED | percent unit','OLED | battery icon',
                            'OLED | battery terminal','OLED | charge bar')):
        visibility(obj,True,1);visibility(obj,True,94);visibility(obj,False,95)
for obj in proto:
    visibility(obj,True,1);visibility(obj,True,192);visibility(obj,False,193)
for obj in phone:
    visibility(obj,True,1);visibility(obj,True,120);visibility(obj,False,121)
for obj in cable:
    visibility(obj,True,1);visibility(obj,True,192);visibility(obj,False,193)

owners=[product,camera,camera.data,phone_root,cable_root,pi_plug,phone_plug,wire.data]+enclosure+proto+phone+cable
for obj in owners:
    if not obj.animation_data or not obj.animation_data.action:continue
    action=obj.animation_data.action
    curves=list(action.fcurves) if action.is_action_legacy else [fc for l in action.layers for s in l.strips for b in s.channelbags for fc in b.fcurves]
    for fc in curves:
        for key in fc.keyframe_points:key.interpolation='CONSTANT' if fc.data_path=='hide_render' else 'LINEAR'
scene.timeline_markers.clear()
for frame,label in [(1,'Simultaneous assembly'),(120,'Closed hero / start move left'),(168,'Overhead composition reached'),
                    (169,'Enclosure to prototype blend starts'),(193,'Prototype / cable arrives'),(218,'Plug insertion'),
                    (252,'CLICK / both plugs seated'),(276,'Photo morph starts in edit')]:
    scene.timeline_markers.new(label,frame=frame)
scene['visual_revision']='v07 | full assembly-to-prototype-to-photo preview'
scene['delivery_duration_seconds']=15
scene['delivery_frames']=360
scene['replacement_blend_frames']=[169,192]
scene['click_frame']=252
scene['photo_transition_seconds']=[11.5,13]
scene['premium_shader_rendering']=False

# Verify camera framing for the complete enclosure throughout its visible path.
framing=[]
for frame in range(1,193):
    scene.frame_set(frame);bpy.context.view_layer.update()
    points=[world_to_camera_view(scene,camera,o.matrix_world@Vector(c)) for o in enclosure
            if o.type in {'MESH','CURVE','FONT'} for c in o.bound_box]
    b=[min(v.x for v in points),min(v.y for v in points),max(v.x for v in points),max(v.y for v in points)]
    assert min(b[:2])>.005 and max(b[2:])<.995,(frame,b)
    framing.append({'frame':frame,'bounds':b})
scene.frame_set(252)
assert pi_plug.location.length<1e-8 and phone_plug.location.length<1e-8
scene.frame_set(168)
assert (product.location-end_product).length<1e-7
screen_center=world_to_camera_view(scene,camera,product.location)
assert screen_center.x<.3,screen_center
scene.frame_set(276)
scene.render.filepath=str(OUT/'full-sequence-frames-v07'/'sequence_')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='SOLID';area.spaces.active.shading.color_type='MATERIAL'
            area.spaces.active.overlay.show_overlays=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Full-sequence-preview-v07.blend'),compress=True)
report={'status':'scene_ready','resolution':[960,540],'fps':24,'duration_seconds':15,
        'CG_frames':276,'delivery_frames':360,'assembly_seconds':[0,5],'slide_seconds':[5,7],
        'replacement_seconds':[7,8],'cable_arrival_seconds':[8,9],
        'click_frame':252,'click_seconds':251/24,'photo_transition_seconds':[11.5,13],'photo_hold_seconds':[13,15],
        'premium_shaders':False,'previous_scenes_preserved':True,'framing_checks':framing,'motion_checks':rows}
(OUT/'full-sequence-v07.json').write_text(json.dumps(report,indent=2))
for frame,label in [(1,'exploded'),(120,'assembled'),(144,'moving-left'),(168,'case-left'),(216,'cable-ready'),(252,'connected')]:
    scene.frame_set(frame);scene.render.filepath=str(OUT/f'full-sequence-{label}-v07.png')
    bpy.ops.render.render(write_still=True)
print('FULL_SEQUENCE_SCENE_READY',flush=True)
