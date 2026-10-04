"""v08: continuous, overlapping nine-second assembly-to-photo blocking shot.

Run against Full-sequence-preview-v07.blend. Geometry and solid-color look stay
the same. Separate object tracks overlap instead of retiming the finished MP4.
"""
import json
import math
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector
from bpy_extras.object_utils import world_to_camera_view

OUT=Path(__file__).resolve().parents[1]/'visualization'
scene=bpy.context.scene
assert scene['visual_revision'].startswith('v07')
scene.frame_set(276)
product=bpy.data.objects['Product | assembly then leftward slide']
camera=scene.camera
phone_root=bpy.data.objects['Phone | enters while camera widens']
cable_root=bpy.data.objects['Cable | appears from below the frame']
pi_plug=bpy.data.objects['Cable | modem end insertion']
phone_plug=bpy.data.objects['Cable | phone end insertion']
wire=bpy.data.objects['Cable | continuous flexible USB link']
spline=wire.data.splines[0]
rest_points=[p.co.copy() for p in spline.bezier_points]
roles={role:[o for o in bpy.data.objects if o.get('sequence_role')==role]
       for role in ('enclosure','prototype','phone','cable')}
for obj in bpy.data.objects:
    obj.animation_data_clear()
    if obj.data and hasattr(obj.data,'animation_data_clear'):obj.data.animation_data_clear()
for mat in bpy.data.materials:
    if mat.node_tree:mat.node_tree.animation_data_clear()
tracks=[('02 Battery',(0,-3,22)),('03 Decorative carrier PCB',(0,0,51)),
        ('04 Official Raspberry Pi CM4',(0,4,72)),('05 Thermal concept',(0,8,98)),
        ('06 Cover',(0,12,129))]
groups=[(bpy.data.objects[name+' | ANIMATE'],Vector(offset)*.001) for name,offset in tracks]
end_product=Vector((.09,-.144,0))
end_target=Vector((681*.00030,-(118+766.125/2)*.00030,0))


def progress(frame,start,end):return max(0,min(1,(frame-start)/(end-start)))


def smooth(t):return t*t*t*(10+t*(-15+6*t))


def assembly_ease(t):
    # Beta(3,4): soft ends, with less prolonged settling than the old Beta(3,6).
    return 20*t**3-45*t**4+36*t**5-10*t**6


def visible(frame,role):
    return {'enclosure':frame<=113,'prototype':frame>=114,
            'phone':frame>=34,'cable':frame>=105}[role]


rows=[]
for frame in range(1,217):
    a=assembly_ease(progress(frame,1,67))
    slide=smooth(progress(frame,33,97))
    replacement=smooth(progress(frame,89,113))
    arrival=smooth(progress(frame,105,137))
    insertion=smooth(progress(frame,129,177))
    photo=progress(frame,169,216)
    for obj,offset in groups:
        obj.location=offset*(1-a);obj.keyframe_insert('location',frame=frame)
    product.location=end_product*slide
    product.rotation_euler=(0,0,math.radians(-9+28*a)*(1-slide))
    product.keyframe_insert('location',frame=frame);product.keyframe_insert('rotation_euler',frame=frame)
    assembly_camera=Vector((.25,-.34,.26)).lerp(Vector((.215,-.31,.265)),a)
    assembly_target=Vector((0,0,.078)).lerp(Vector((0,0,.016)),a)
    assembly_q=(assembly_target-assembly_camera).to_track_quat('-Z','Y')
    q=assembly_q.slerp(Quaternion((1,0,0,0)),slide)
    target=assembly_target.lerp(end_target,slide)
    distance=(assembly_camera-assembly_target).length*(1-slide)+.75*slide
    camera.location=target+q@Vector((0,0,distance));camera.rotation_euler=q.to_euler()
    camera.data.ortho_scale=(.38+(.182-.38)*a)*(1-slide)+.4086*slide
    camera.keyframe_insert('location',frame=frame);camera.keyframe_insert('rotation_euler',frame=frame)
    camera.data.keyframe_insert('ortho_scale',frame=frame)
    phone_root.location=(.20*(1-smooth(progress(frame,54,97))),0,0)
    phone_root.keyframe_insert('location',frame=frame)
    cable_root.location=(0,-.10*(1-arrival),0);cable_root.keyframe_insert('location',frame=frame)
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
            co.y-=phone_gap*((i-8)/3)*.0003;co.x+=phone_gap*.045*((i-8)/3)*.0003
        coords.append(co)
    for i,p in enumerate(spline.bezier_points):
        p.handle_left_type='FREE';p.handle_right_type='FREE';p.co=coords[i]
        if i==0:tangent=Vector((24*.0003,0,0))
        elif i==len(coords)-1:tangent=Vector((-1.2*.0003,25*.0003,0))
        else:tangent=(coords[i+1]-coords[i-1])/6
        p.handle_left=coords[i]-tangent;p.handle_right=coords[i]+tangent
        for prop in ('co','handle_left','handle_right'):p.keyframe_insert(prop,frame=frame)
    rows.append({'frame':frame,'assembly':a,'slide':slide,'replacement':replacement,
                 'cable_arrival':arrival,'insertion':insertion,'photo':photo})
for role,objects in roles.items():
    for obj in objects:
        for frame in (1,33,34,67,68,104,105,113,114,216):
            obj.hide_render=not visible(frame,role)
            if obj.name.startswith(('OLED | battery percentage','OLED | percent unit','OLED | battery icon',
                                    'OLED | battery terminal','OLED | charge bar')) and frame<67:
                obj.hide_render=True
            obj.keyframe_insert('hide_render',frame=frame)
owners=[o for o in bpy.data.objects]+[camera.data,wire.data]
for obj in owners:
    if not obj.animation_data or not obj.animation_data.action:continue
    action=obj.animation_data.action
    curves=list(action.fcurves) if action.is_action_legacy else [fc for l in action.layers for s in l.strips for b in s.channelbags for fc in b.fcurves]
    for fc in curves:
        fc.mute=False
        for k in fc.keyframe_points:k.interpolation='CONSTANT' if fc.data_path=='hide_render' else 'LINEAR'
scene.frame_start=1;scene.frame_end=216;scene.render.fps=24
scene['visual_revision']='v08 | overlapping continuous nine-second preview'
scene['delivery_duration_seconds']=9;scene['delivery_frames']=216
scene['replacement_blend_frames']=[89,113];scene['click_frame']=177
scene['photo_transition_seconds']=[168/24,215/24]
scene.timeline_markers.clear()
for frame,label in [(1,'Assembly begins immediately'),(33,'Slide overlaps assembly'),(67,'Assembly seated'),
                    (89,'Prototype blend while camera moves'),(105,'Cable arrives during replacement'),
                    (129,'Insertion overlaps cable arrival'),(169,'Photo blend overlaps final catch'),
                    (177,'CLICK at contact'),(216,'Real photograph / end')]:
    scene.timeline_markers.new(label,frame=frame)
framing=[]
for frame in range(1,114):
    scene.frame_set(frame);bpy.context.view_layer.update()
    points=[world_to_camera_view(scene,camera,o.matrix_world@Vector(c)) for o in roles['enclosure']
            if o.type in {'MESH','CURVE','FONT'} for c in o.bound_box]
    bounds=[min(v.x for v in points),min(v.y for v in points),max(v.x for v in points),max(v.y for v in points)]
    assert min(bounds[:2])>.005 and max(bounds[2:])<.995,(frame,bounds)
    framing.append({'frame':frame,'bounds':bounds})
# No repeated progress state: at least one action or transition advances every frame.
keys=('assembly','slide','replacement','cable_arrival','insertion','photo')
assert all(any(abs(b[k]-a[k])>1e-8 for k in keys) for a,b in zip(rows,rows[1:]))
scene.frame_set(177)
assert pi_plug.location.length<1e-8 and phone_plug.location.length<1e-8
scene.frame_set(216)
scene.render.filepath=str(OUT/'flow-sequence-frames-v08'/'flow_')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Full-sequence-flow-v08.blend'),compress=True)
report={'status':'ready','duration_seconds':9,'frames':216,'resolution':[960,540],'fps':24,
        'assembly_frames':[1,67],'slide_frames':[33,97],'replacement_frames':[89,113],
        'cable_arrival_frames':[105,137],'insertion_frames':[129,177],
        'photo_frames':[169,216],'click_frame':177,'click_seconds':176/24,
        'static_holds':False,'motion_checks':rows,'framing_checks':framing}
(OUT/'flow-sequence-v08.json').write_text(json.dumps(report,indent=2))
for frame,name in [(44,'assembly-moving'),(94,'replacing'),(136,'connecting')]:
    scene.frame_set(frame);scene.render.filepath=str(OUT/f'flow-{name}-v08.png')
    bpy.ops.render.render(write_still=True)
print('FLOW_SEQUENCE_READY',flush=True)
