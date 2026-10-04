"""Workbench shots for the complete narrated preview; premium masters are read-only.

Blender --background --python this_file.py -- assembly|prototype [--stills]
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector, Quaternion
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'visualization' / 'launch-preview-v18'
OUT.mkdir(exist_ok=True)
args = sys.argv[sys.argv.index('--') + 1:]
kind = args[0]
stills = '--stills' in args
FPS = 24


def ease(x):
    x = max(0., min(1., x))
    return x*x*x*(10+x*(-15+6*x))


def close_ease(x):
    x = max(0., min(1., x))
    return 20*x**3-45*x**4+36*x**5-10*x**6


def clear_tracks():
    for obj in bpy.data.objects:
        obj.animation_data_clear()
        if obj.data and hasattr(obj.data, 'animation_data_clear'):
            obj.data.animation_data_clear()
    for mat in bpy.data.materials:
        if mat.node_tree:
            mat.node_tree.animation_data_clear()


def configure(scene):
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.render.fps_base = 1
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.film_transparent = False
    scene.use_nodes = False
    scene.display.render_aa = '8'
    sh = scene.display.shading
    sh.light = 'STUDIO'
    sh.studio_light = 'paint.sl'
    sh.color_type = 'MATERIAL'
    sh.show_shadows = True
    sh.show_cavity = True
    sh.cavity_type = 'BOTH'
    sh.curvature_ridge_factor = .6
    sh.curvature_valley_factor = .6
    sh.show_specular_highlight = False
    sh.show_object_outline = False
    sh.background_type = 'WORLD'
    scene.world.color = (.045, .060, .075)
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0
    scene.camera.data.clip_start = .0001
    scene.camera.data.clip_end = 100
    scene.camera.data.type = 'ORTHO'


def linear_keys():
    for owner in list(bpy.data.objects) + [o.data for o in bpy.data.objects if o.type == 'CAMERA']:
        if not owner.animation_data or not owner.animation_data.action:
            continue
        action = owner.animation_data.action
        curves = list(action.fcurves) if action.is_action_legacy else [
            fc for layer in action.layers for strip in layer.strips
            for bag in strip.channelbags for fc in bag.fcurves]
        for curve in curves:
            for point in curve.keyframe_points:
                point.interpolation = 'CONSTANT' if curve.data_path == 'hide_render' else 'LINEAR'


def camera_key(camera, position, target, scale, frame):
    camera.location = position
    camera.rotation_euler = (Vector(target)-camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.ortho_scale = scale
    camera.keyframe_insert('location', frame=frame)
    camera.keyframe_insert('rotation_euler', frame=frame)
    camera.data.keyframe_insert('ortho_scale', frame=frame)


if kind == 'assembly':
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'visualization/Product-keynote-v04.blend'))
    scene = bpy.context.scene
    scene.frame_set(120)
    clear_tracks()
    configure(scene)
    root = bpy.data.objects['SafeWall | product rotation']
    root.rotation_mode = 'QUATERNION'
    camera = scene.camera
    layers = [('02 Battery', (0,-3,22)), ('03 Decorative carrier PCB', (0,0,51)),
              ('04 Official Raspberry Pi CM4', (0,4,72)), ('05 Thermal concept', (0,8,98)),
              ('06 Cover', (0,12,129))]
    groups = [(bpy.data.objects[name+' | ANIMATE'], Vector(offset)*.001) for name,offset in layers]
    floor = bpy.data.objects['Seamless studio floor']
    floor.hide_render = False
    floor.is_shadow_catcher = False
    for mat in floor.data.materials:
        mat.diffuse_color = (.045,.060,.075,1)
    for name, color in [('CMF | graphite polymer with polished clearcoat',(.028,.035,.044,1)),
                        ('CMF | piano black gloss cover',(.010,.015,.020,1))]:
        bpy.data.materials[name].diffuse_color = color
    upright = Quaternion((1,0,0), math.pi/2)
    horizontal = Quaternion((0,0,1), math.radians(-9))
    n = 168
    for frame in range(1,n+1):
        t=(frame-1)/FPS
        # Match upright Seedance pose, reveal, then all five layers close together in exactly 5 s.
        opening=ease((t-.25)/.75)
        closing=close_ease((t-1.25)/5)
        spread=opening*(1-closing)
        for obj, offset in groups:
            obj.location=offset*spread
            obj.keyframe_insert('location',frame=frame)
        rotate=ease((t-.18)/1.12)
        root.rotation_quaternion=upright.slerp(horizontal,rotate)
        if rotate>=1:
            root.rotation_quaternion=Quaternion((0,0,1),math.radians(-9+28*closing))
        root.location=(0,0,.055*(1-rotate))
        root.keyframe_insert('rotation_quaternion',frame=frame)
        root.keyframe_insert('location',frame=frame)
        opening_cam=ease((t-.16)/1.0)
        assembly_pos=Vector((.25,-.34,.26)).lerp(Vector((.215,-.31,.265)),closing)
        assembly_target=Vector((0,0,.078)).lerp(Vector((0,0,.016)),closing)
        pos=Vector((.31,-.5,.195)).lerp(assembly_pos,opening_cam)
        target=Vector((0,0,.066)).lerp(assembly_target,opening_cam)
        scale=.36*(1-opening_cam)+(.39+(.185-.39)*closing)*opening_cam
        camera_key(camera,pos,target,scale,frame)
    shot_stills=[1,25,31,70,125,155,168]
    scene['assembly_close_seconds']=[1.25,6.25]
    scene['assembly_all_layers_synchronous']=True
    visible=[o for o in root.children_recursive if o.type in {'MESH','CURVE','FONT'} and not o.hide_render]
elif kind == 'prototype':
    # Reuse detailed proxy geometry, but replace its former photograph layout and cable.
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'visualization/Overhead-photo-transition-v06.blend'))
    scene=bpy.context.scene
    scene.frame_set(96)
    clear_tracks()
    configure(scene)
    scene.display.shading.color_type='OBJECT'
    old_pi_center=Vector((300*.0003,-464*.0003,0))
    old_phone_center=Vector((1084*.0003,-459*.0003,0))
    # Coordinates of the actual 848x464 recording, padded into 960x540.
    S=.0005
    def pixel(x,y,z=0):return Vector((x*S,-y*S,z))
    def root_obj(name):
        obj=bpy.data.objects.new(name,None);scene.collection.objects.link(obj);return obj
    pi=root_obj('v18 | actual video prototype position')
    phone=root_obj('v18 | actual video phone position')
    pi_objects=[];phone_objects=[]
    for obj in list(bpy.data.objects):
        if obj.name.startswith(('Prototype |','HAT |','Pi |','Modem |','Antenna |')):
            mw=obj.matrix_world.copy();mw.translation-=old_pi_center
            obj.parent=pi;obj.matrix_world=mw;pi_objects.append(obj)
        elif obj.name.startswith('Phone |'):
            mw=obj.matrix_world.copy();mw.translation-=old_phone_center
            obj.parent=phone;obj.matrix_world=mw;phone_objects.append(obj)
        elif obj.name.startswith(('Cable |','Table |')):
            obj.hide_render=True
    pi.location=pixel(362,236)
    pi.rotation_euler.z=math.pi
    pi.scale=(.8,.66,.8)
    phone.location=pixel(636,218)
    phone.scale=(.79,.72,.8)
    # The new recording has a straight antenna pointing left, unlike the old photograph.
    for obj in pi_objects:
        if obj.name.startswith('Antenna |') or 'external LTE antenna' in obj.name:
            obj.hide_render=True
    outline=[(306,223),(280,220),(261,210),(164,198),(147,199),(143,207),
             (145,224),(252,239),(267,233),(283,236),(306,238)]
    vertices=[pixel(x,y,z) for z in (.021,.029) for x,y in outline]
    k=len(outline)
    faces=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)]
    mesh=bpy.data.meshes.new('v18 straight antenna');mesh.from_pydata(vertices,[],faces);mesh.update()
    antenna=bpy.data.objects.new('v18 | actual left-facing LTE antenna',mesh);scene.collection.objects.link(antenna)
    antenna.color=(.022,.025,.028,1)
    bevel=antenna.modifiers.new('Antenna softened edges','BEVEL');bevel.width=.0015;bevel.segments=3
    bpy.context.view_layer.update()
    antenna.parent=pi;antenna.matrix_parent_inverse=pi.matrix_world.inverted()
    pi_objects.append(antenna)
    scene.display.shading.show_shadows=False
    # Main phone, cable and PCB fit the actual entry frame. The real clip supplies the RJ45 insertion.
    def curve(name,points,r,color):
        data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.resolution_u=16
        data.bevel_depth=r*S;data.bevel_resolution=3
        spline=data.splines.new('BEZIER');spline.bezier_points.add(len(points)-1)
        for b,(x,y,z) in zip(spline.bezier_points,points):
            b.co=pixel(x,y,z);b.handle_left_type='AUTO';b.handle_right_type='AUTO'
        obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.color=color
        return obj
    dark=(.025,.028,.030,1)
    curve('v18 | USB-Ethernet lead already attached to phone',[(641,359,.008),(637,420,.003),(625,480,.003),(620,600,.003)],3.7,dark)
    curve('v18 | loose RJ45 cable',[(317,360,.007),(343,418,.004),(366,480,.003),(398,560,.003)],4.3,dark)
    curve('v18 | prototype supply lead',[(310,188,.004),(242,181,.003),(129,116,.003),(-10,2,.003)],1.8,(.4,.4,.38,1))
    def cube(name,x,y,w,h,z,depth,color):
        bpy.ops.mesh.primitive_cube_add(size=1,location=pixel(x,y,z))
        o=bpy.context.object;o.name=name;o.dimensions=(w*S,h*S,depth)
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        o.color=color;b=o.modifiers.new('Small softened edges','BEVEL');b.width=.001;b.segments=3
        return o
    cube('v18 | USB-C adapter',642,345,18,34,.010,.010,(.18,.18,.18,1))
    plug=cube('v18 | RJ45 awaiting real insertion',316,349,24,44,.010,.012,(.08,.08,.08,1));plug.rotation_euler.z=math.radians(16)
    # Bring in the closed case for the leftward move and geometry replacement.
    col=bpy.data.collections.new('v18 | case before real prototype');scene.collection.children.link(col)
    with bpy.data.libraries.load(str(ROOT/'visualization/Product-keynote-v04.blend'),link=False) as (src,dst):
        dst.objects=[name for name in src.objects if name!='Seamless studio floor' and not name.startswith(('Camera','Key','Fill','Rim','Softbox'))]
    imported=[o for o in dst.objects if o]
    for obj in imported:col.objects.link(obj)
    case=next(o for o in imported if o.name.startswith('SafeWall | product rotation'))
    imported_set=set(imported)
    case_objects=[o for o in case.children_recursive if o in imported_set]
    for obj in imported:
        obj.animation_data_clear()
        if obj.data and hasattr(obj.data,'animation_data_clear'):obj.data.animation_data_clear()
    for obj in case_objects:
        if obj.name.endswith('| ANIMATE'):obj.location=(0,0,0)
        if obj.type in {'MESH','CURVE','FONT'}:
            obj.color=(.055,.065,.08,1)
            if obj.name.startswith('OLED |'):obj.color=(.3,.35,.4,1)
    case.rotation_euler=(0,0,0)
    case.scale=(.83,.83,.83)
    case.location=pixel(455,246)
    bpy.ops.mesh.primitive_plane_add(size=20,location=(0,0,-.005))
    floor=bpy.context.object;floor.name='v18 | neutral real tabletop';floor.color=(.34,.35,.34,1)
    scene.world.color=(.34,.35,.34)
    camera=scene.camera
    camera.data.ortho_scale=960*S
    n=114
    for frame in range(1,n+1):
        t=(frame-1)/FPS;slide=ease(t/1.6)
        case.location=pixel(455+(362-455)*slide,246+(236-246)*slide)
        case.keyframe_insert('location',frame=frame)
        # Shrink the enclosure while revealing the actual board silhouette at the same center.
        swap=ease((t-1.2)/1.0)
        case.scale=Vector((.83,.83,.83))*(1-.96*swap)
        case.keyframe_insert('scale',frame=frame)
        for obj in case_objects:
            obj.hide_render=swap>=.999;obj.keyframe_insert('hide_render',frame=frame)
        pi.scale=Vector((.8,.66,.8))*(.025+.975*swap)
        pi.keyframe_insert('scale',frame=frame)
        camera_key(camera,pixel(480,270,.75),pixel(480,270,0),960*S*(1+.035*(1-ease(t/4.5))),frame)
    shot_stills=[1,25,44,60,90,114]
    visible=pi_objects+phone_objects
else:
    raise ValueError(kind)

scene.frame_start=1;scene.frame_end=n
scene['visual_revision']='v18 | complete launch preview / '+kind
scene['premium_shaders_rendered']=False
linear_keys()
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(kind+'-v18.blend')),compress=True)
frames=OUT/(kind+'-frames');frames.mkdir(exist_ok=True)
checks=[]
for frame in (shot_stills if stills else range(1,n+1)):
    scene.frame_set(frame);bpy.context.view_layer.update()
    if frame in shot_stills:
        points=[world_to_camera_view(scene,scene.camera,o.matrix_world@Vector(c))
                for o in visible for c in o.bound_box]
        checks.append({'frame':frame,'bounds':[min(v.x for v in points),min(v.y for v in points),max(v.x for v in points),max(v.y for v in points)]})
    dest=frames/f'{frame:04d}.png'
    if not dest.exists():
        scene.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
    if frame%24==0:print('V18_RENDER',kind,frame,n,flush=True)
(OUT/(kind+'-checks.json')).write_text(json.dumps({'frames':n,'engine':scene.render.engine,'stills_only':stills,'checks':checks},indent=2)+'\n')
print('V18_SHOT_READY',kind,n,flush=True)
