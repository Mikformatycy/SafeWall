"""Replace three relay sculptures with downloaded servers and emit name instances.

Blender --background --python this.py -- tor|radios [--stills]
"""
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector, Matrix

ROOT=Path(__file__).resolve().parents[1]
V=ROOT/'visualization';OUT=V/'launch-preview-v21';OUT.mkdir(exist_ok=True)
args=sys.argv[sys.argv.index('--')+1:];kind=args[0];stills='--stills' in args
BG=(.038,.049,.064,1);WHITE=(.79,.84,.88,1);LAVENDER=(.47,.36,.78,1);TEAL=(.20,.69,.64,1)

def ease(t):
    t=max(0,min(1,t));return t*t*t*(10+t*(-15+6*t))

def key(o,prop,f):o.keyframe_insert(prop,frame=f)

def empty(name):
    o=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(o);return o

def lettering(name,text,size):
    d=bpy.data.curves.new(name,'FONT');d.body=text;d.size=size
    d.font=bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Arial.ttf')
    d.extrude=.00022;d.bevel_depth=.00005;d.bevel_resolution=1
    o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o);o.color=WHITE
    return o

bpy.ops.wm.open_mainfile(filepath=str(V/'launch-preview-v20'/(kind+'-v20.blend')))
scene=bpy.context.scene;scene.frame_set(1)
camera=scene.camera
if kind=='tor':
    n=456
    camera.data.lens=37
    for o in list(bpy.data.objects):
        if o.name.startswith('v20 | relay '):bpy.data.objects.remove(o,do_unlink=True)
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/'references/server-rack-v21/compute-rack.glb'))
    imported=[o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    meshes=[o for o in imported if o.type=='MESH']
    corners=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
    low=Vector(tuple(min(p[i] for p in corners) for i in range(3)))
    high=Vector(tuple(max(p[i] for p in corners) for i in range(3)))
    centre=Vector(((low.x+high.x)/2,(low.y+high.y)/2,low.z))
    factor=.125/(high.z-low.z)
    normalized=[]
    for o in meshes:
        # Freeze the imported glTF hierarchy into metres, then place three linked copies.
        mw=o.matrix_world.copy();o.parent=None;o.matrix_world=mw
        mesh=o.data.copy();mesh.transform(Matrix.Scale(factor,4)@Matrix.Translation(-centre)@mw)
        o.data=mesh;o.matrix_world=Matrix.Identity(4)
        o.color=o.data.materials[0].diffuse_color if o.data.materials else WHITE
        normalized.append(o)
    for o in imported:
        if o.type!='MESH':bpy.data.objects.remove(o,do_unlink=True)
    positions=[(.10,.070,-.006),(.29,-.064,-.006),(.47,.082,-.006)]
    for i,pos in enumerate(positions):
        rig=empty(f'v21 | relay server {i+1}')
        rig.location=pos;rig.rotation_euler.z=math.radians([-10,5,-14][i])
        for j,original in enumerate(normalized):
            o=original if i==0 else original.copy()
            if i:scene.collection.objects.link(o)
            o.parent=rig;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=Matrix.Identity(4)
            o.name=f'v21 | server {i+1} component {j+1}'
    scene['server_model']='Compute Rack / 3DAssets.dev / CC0-1.0'
    scene['server_model_source']='https://3dassets.dev/assets/data-centre-infiltration-kit-data-centre-infiltration--49b6521a'
    scene['server_count']=3
    checks=[1,72,144,240,336,456]
elif kind=='radios':
    n=234
    for o in list(bpy.data.objects):
        if o.name.startswith(('v20 | identity text','v20 | exact discovered','v20 | discovery context')):
            bpy.data.objects.remove(o,do_unlink=True)
    # Many airborne letters should remain readable; avoid repeated cast text shadows.
    scene.display.shading.show_shadows=False
    context=lettering('v21 | AirDrop discovery context','AirDrop · Wszyscy',.0075)
    context.color=LAVENDER
    names=[lettering(f'v21 | emitted name {i+1:02}','iPhone (Piotrek)',.011) for i in range(23)]
    lanes=[-.100,.065,-.042,.116,.014]
    for f in range(1,n+1):
        scene.frame_set(f);t=(f-1)/24
        orientation=camera.rotation_euler.to_quaternion()
        right=orientation@Vector((1,0,0));up=orientation@Vector((0,1,0))
        context.location=Vector((-.103,-.091,.025))
        context.rotation_euler=camera.rotation_euler
        key(context,'location',f);key(context,'rotation_euler',f)
        for i,o in enumerate(names):
            start=.20+i*.43;life=4.5+(i%3)*.12
            age=t-start;u=age/life;visible=0<=u<1
            o.hide_render=not visible;key(o,'hide_render',f)
            p=max(0.,min(1.,u));reveal=ease(age/.38)
            # A fan of spatial trajectories, all originating at the same phone edge.
            origin=Vector((-.017,.001,.040))
            travel=.31*p
            lateral=lanes[i%5]*ease(p*2.0)
            o.location=origin+right*travel+up*lateral+Vector((0,0,.018*math.sin(p*math.pi)))
            o.rotation_euler=camera.rotation_euler
            o.rotation_euler.rotate_axis('Z',math.radians([-5,3,-2,5,0][i%5])*ease(p*3))
            scale=max(.0001,reveal*(1-.23*p)*(1-ease((p-.88)/.12)))
            o.scale=(scale,)*3
            tint=WHITE if i%3==0 else (TEAL if i%3==1 else (.66,.58,.88,1))
            strength=(1-ease((p-.64)/.36))*.95
            o.color=tuple(BG[j]+(tint[j]-BG[j])*strength for j in range(3))+(1,)
            for prop in ['location','rotation_euler','scale','color']:key(o,prop,f)
    scene['exact_emitted_text']='iPhone (Piotrek)'
    scene['name_instances']=len(names)
    scene['discovery_context']='AirDrop Everyone; repeated names illustrate discovery, not literal contents of every network packet'
    checks=[1,24,60,106,144,192,234]
else:raise ValueError(kind)

for o in bpy.data.objects:
    if not o.animation_data or not o.animation_data.action:continue
    a=o.animation_data.action
    curves=list(a.fcurves) if a.is_action_legacy else [fc for l in a.layers for s in l.strips for b in s.channelbags for fc in b.fcurves]
    for c in curves:
        for p in c.keyframe_points:p.interpolation='CONSTANT' if c.data_path=='hide_render' else 'LINEAR'
scene.frame_start=1;scene.frame_end=n;scene.frame_set(1)
scene['visual_revision']='v21 '+kind
scene['premium_shaders_rendered']=False
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(kind+'-v21.blend')),compress=True)
frames=OUT/(kind+'-frames');frames.mkdir(exist_ok=True)
for f in (checks if stills else range(1,n+1)):
    file=frames/f'{f:04d}.png'
    if file.exists():continue
    scene.frame_set(f);scene.render.filepath=str(file);bpy.ops.render.render(write_still=True)
    if f%48==0:print('V21_RENDER',kind,f,n,flush=True)
(OUT/(kind+'-checks.json')).write_text(json.dumps({'frames':n,'engine':scene.render.engine,'sample_frames':checks,'stills_only':stills},indent=2)+'\n')
print('V21_SHOT_READY',kind,n,flush=True)
