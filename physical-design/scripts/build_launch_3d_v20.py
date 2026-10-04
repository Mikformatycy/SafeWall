"""Spatial Workbench film shots, no raster titles or presentation panels.

Blender --background --python this.py -- tor|radios|closing|docking [--stills]
"""
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
V=ROOT/'visualization'
OUT=V/'launch-preview-v20'
OUT.mkdir(exist_ok=True)
args=sys.argv[sys.argv.index('--')+1:]
kind=args[0];stills='--stills' in args
FPS=24
BG=(.038,.049,.064,1)
GRAPHITE=(.075,.092,.115,1)
SILVER=(.42,.49,.56,1)
WHITE=(.79,.84,.88,1)
LAVENDER=(.47,.36,.78,1)
TEAL=(.20,.69,.64,1)

def ease(v):
    v=max(0.,min(1.,v));return v*v*v*(10+v*(-15+6*v))

def freeze():
    for o in bpy.data.objects:
        o.animation_data_clear()
        if o.data and hasattr(o.data,'animation_data_clear'):o.data.animation_data_clear()

def configure(scene):
    scene.render.engine='BLENDER_WORKBENCH'
    scene.render.resolution_x=960;scene.render.resolution_y=540
    scene.render.resolution_percentage=100
    scene.render.fps=24;scene.render.fps_base=1
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    scene.render.film_transparent=False;scene.use_nodes=False
    scene.display.render_aa='8'
    s=scene.display.shading
    s.light='STUDIO';s.studio_light='paint.sl';s.color_type='OBJECT'
    s.show_shadows=True;s.show_cavity=True;s.cavity_type='BOTH'
    s.curvature_ridge_factor=.75;s.curvature_valley_factor=.55
    s.show_specular_highlight=False;s.show_object_outline=False
    s.background_type='WORLD';scene.world.color=BG[:3]
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
    scene.view_settings.exposure=0
    for o in bpy.data.objects:
        if o.type in {'MESH','CURVE','FONT'} and o.data.materials:
            o.color=o.data.materials[0].diffuse_color
        if o.type=='CAMERA':
            o.data.clip_start=.01;o.data.clip_end=10

def empty(name):
    o=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(o);return o

def cube(name,loc,size,color,bevel=.003):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.color=color
    if bevel:
        m=o.modifiers.new('Soft machined edges','BEVEL');m.width=bevel;m.segments=4
        o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return o

def tube(name,coords,r,color,cyclic=False):
    d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=r;d.bevel_resolution=3
    sp=d.splines.new('POLY');sp.points.add(len(coords)-1)
    for p,co in zip(sp.points,coords):p.co=(*co,1)
    sp.use_cyclic_u=cyclic
    o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o);o.color=color
    return o

def sphere(name,loc,r,color):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=10,radius=r,location=loc)
    o=bpy.context.object;o.name=name;o.color=color
    for p in o.data.polygons:p.use_smooth=True
    return o

def catmull(points,u):
    n=len(points);q=max(0.,min(n-1.-1e-9,u*(n-1)));i=int(q);f=q-i
    p0=Vector(points[max(0,i-1)]);p1=Vector(points[i]);p2=Vector(points[min(n-1,i+1)]);p3=Vector(points[min(n-1,i+2)])
    return .5*((2*p1)+(-p0+p2)*f+(2*p0-5*p1+4*p2-p3)*f*f+(-p0+3*p1-3*p2+p3)*f*f*f)

def text3d(name,body,size,color,parent=None,loc=(0,0,0)):
    d=bpy.data.curves.new(name,'FONT');d.body=body;d.size=size
    d.font=bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Arial.ttf')
    d.extrude=.00035;d.bevel_depth=.00008;d.bevel_resolution=2
    o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o)
    o.color=color;o.parent=parent;o.location=loc
    return o

def look(camera,pos,target,lens=None):
    camera.location=pos
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    if lens is not None:camera.data.lens=lens

def key(o,prop,f):o.keyframe_insert(prop,frame=f)

def import_phone(location):
    with bpy.data.libraries.load(str(V/'launch-preview-v18/prototype-v18.blend'),link=False) as (src,dst):
        dst.objects=[n for n in src.objects if n.startswith('Phone |') or n=='v18 | actual video phone position']
    for o in dst.objects:
        if o:
            bpy.context.scene.collection.objects.link(o);o.animation_data_clear()
    root=next(o for o in dst.objects if o and o.name.startswith('v18 | actual video phone position'))
    root.name='v20 | phone spatial rig';root.location=location;root.scale=(1.03,1.03,1.03)
    for o in root.children_recursive:
        o.hide_render=False
        if o.data and hasattr(o.data,'materials') and o.data.materials:o.color=o.data.materials[0].diffuse_color
    return root

def base():
    bpy.ops.wm.open_mainfile(filepath=str(V/'launch-preview-v18/assembly-v18.blend'))
    scene=bpy.context.scene;scene.frame_set(168);freeze();configure(scene)
    root=bpy.data.objects['SafeWall | product rotation']
    root.rotation_mode='XYZ';root.rotation_euler=(0,0,0);root.location=(0,0,0)
    for o in root.children_recursive:
        if o.name.endswith('| ANIMATE'):o.location=(0,0,0)
        if 'shell' in o.name.lower() or 'cover' in o.name.lower():o.color=GRAPHITE
    floor=bpy.data.objects['Seamless studio floor'];floor.color=BG;floor.location.z=-.008;floor.is_shadow_catcher=False
    camera=scene.camera;camera.data.type='PERSP';camera.data.lens=44
    return scene,root,camera

def relay(pos,index):
    x,y,z=pos
    # Physical sculptural frame, with a large open aperture in the YZ plane.
    # Rounded superellipse gives substantial geometry without any UI circle.
    pts=[]
    for k in range(100):
        a=2*math.pi*k/100
        sy=math.copysign(abs(math.cos(a))**.45,math.cos(a))
        sz=math.copysign(abs(math.sin(a))**.45,math.sin(a))
        pts.append((x,y+.033*sy,z+.040*sz))
    tube(f'v20 | relay {index} sculptural aperture',pts,.006,SILVER,True)
    tube(f'v20 | relay {index} violet inner edge',[(xx-.006,yy,zz) for xx,yy,zz in pts],.0014,LAVENDER,True)
    cube(f'v20 | relay {index} foot',(x,y,.004),(.035,.065,.018),GRAPHITE,.005)
    cube(f'v20 | relay {index} support',(x,y,z/2-.012),(.010,.016,z-.028),GRAPHITE,.003)

def svg_logo(parent):
    # Read the approved vector source and tessellate its circular corner arcs.
    xml=ET.parse(ROOT.parent/'brand/svg/safewall-logo.svg')
    for layer,p in enumerate(xml.getroot().findall('{http://www.w3.org/2000/svg}path')):
        tokens=re.findall(r'[MHVAZ]|-?\d+(?:\.\d+)?',p.attrib['d']);i=0;pts=[];cur=(0.,0.)
        while i<len(tokens):
            cmd=tokens[i];i+=1
            if cmd=='M':cur=(float(tokens[i]),float(tokens[i+1]));i+=2;pts.append(cur)
            elif cmd=='H':cur=(float(tokens[i]),cur[1]);i+=1;pts.append(cur)
            elif cmd=='V':cur=(cur[0],float(tokens[i]));i+=1;pts.append(cur)
            elif cmd=='A':
                rx,ry,rot,large,sweep,x,y=map(float,tokens[i:i+7]);i+=7
                start=Vector(cur);end=Vector((x,y));delta=end-start;mid=(start+end)/2
                h=math.sqrt(max(0,rx*rx-delta.length_squared/4))
                normal=Vector((-delta.y,delta.x)).normalized()
                options=[]
                for sign in (1,-1):
                    c=mid+normal*h*sign;a0=math.atan2(start.y-c.y,start.x-c.x);a1=math.atan2(end.y-c.y,end.x-c.x)
                    da=(a1-a0)%(2*math.pi) if sweep else -((a0-a1)%(2*math.pi))
                    options.append((abs(da),c,a0,da))
                _,c,a0,da=min(options,key=lambda v:v[0])
                for k in range(1,9):
                    a=a0+da*k/8;pts.append((c.x+rx*math.cos(a),c.y+ry*math.sin(a)))
                cur=(x,y)
            elif cmd=='Z':pass
            else:raise ValueError(cmd)
        d=bpy.data.curves.new('SafeWall 4A SVG path '+str(layer),'CURVE');d.dimensions='2D';d.resolution_u=1
        d.fill_mode='BOTH';d.extrude=.0007
        s=d.splines.new('POLY');s.points.add(len(pts)-1)
        for q,(x,y) in zip(s.points,pts):q.co=((x-428)/856*.048,(442-y)/856*.048,0,1)
        s.use_cyclic_u=True
        o=bpy.data.objects.new('v20 | logo 4A exact source path '+str(layer),d)
        bpy.context.scene.collection.objects.link(o);o.parent=parent;o.location=(.052,.035,layer*.0016)
        hexcolor=p.attrib['fill'].lstrip('#');rgb=[int(hexcolor[k:k+2],16)/255 for k in (0,2,4)]
        o.color=tuple(((v+.055)/1.055)**2.4 if v>.04045 else v/12.92 for v in rgb)+(1,)

if kind=='docking':
    bpy.ops.wm.open_mainfile(filepath=str(V/'Phone-docking-preview-v05.blend'))
    scene=bpy.context.scene;configure(scene);n=96
    camera=scene.camera
    # Preserve the already approved phone and magnetic contact choreography.
    for o in bpy.data.objects:
        if o.type=='MESH' and max(o.dimensions)>2:
            o.color=BG;o.is_shadow_catcher=False
        if o.type in {'MESH','CURVE'} and o.data.materials:
            if any('graphite polymer' in m.name or 'piano black' in m.name for m in o.data.materials if m):o.color=GRAPHITE
    scene.world.color=BG[:3]
    checks=[1,24,48,72,96]
elif kind=='tor':
    scene,root,camera=base();n=456
    root.location=(-.075,0,.008)
    phone=import_phone((-.205,.006,.008))
    positions=[(.10,.070,.061),(.29,-.064,.078),(.47,.082,.067)]
    for i,p in enumerate(positions,1):relay(p,i)
    points=[(-.21,-.074,.02),(-.16,-.10,.029),(-.085,-.048,.028),(-.065,.058,.036),*positions,(.64,.02,.055)]
    route=tube('v20 | one routed connection in physical space',[catmull(points,k/300) for k in range(301)],.0014,(.075,.22,.25,1))
    cube('v20 | remote destination',(.66,.02,.040),(.045,.045,.08),GRAPHITE,.007)
    packets=[sphere(f'v20 | travelling data {i}',(0,0,0),.004,TEAL) for i in range(5)]
    poses=[(-.15,-.35,.27),(.25,-.50,.36),(.61,-.34,.31),(.09,-.43,.32),(-.11,-.31,.33)]
    targets=[(-.1,0,.035),(.19,.015,.052),(.35,.01,.060),(-.025,.008,.045),(-.13,.008,.035)]
    for f in range(1,n+1):
        t=(f-1)/FPS;u=t/(n/FPS)
        look(camera,catmull(poses,u),catmull(targets,u),42)
        key(camera,'location',f);key(camera,'rotation_euler',f)
        for i,p in enumerate(packets):
            p.location=catmull(points,(t*.135+i/len(packets))%1)
            key(p,'location',f)
    checks=[1,72,144,240,336,456]
elif kind=='radios':
    scene,root,camera=base();n=234
    for o in root.children_recursive:o.hide_render=True
    phone=import_phone((-.065,0,.008))
    rig=empty('v20 | identity text in scene space')
    name=text3d('v20 | exact discovered device name','iPhone (Piotrek)',.019,WHITE,rig)
    context=text3d('v20 | discovery context','AirDrop · Wszyscy',.0075,LAVENDER,rig,(.001,-.019,0))
    ripples=[]
    for i in range(4):
        # Open arcs emerge into nearby space, not rings printed on a panel.
        arc=[(.10*math.cos(a),.10*math.sin(a),0) for a in [(-1.2+k/70*2.4) for k in range(71)]]
        o=tube('v20 | nearby discovery wave '+str(i),arc,.0006,TEAL)
        ripples.append(o)
    for f in range(1,n+1):
        t=(f-1)/FPS;u=t/(n/FPS)
        look(camera,(-.015+.035*u,-.35+.035*u,.43+.035*u),(.010,.010,.028),44)
        key(camera,'location',f);key(camera,'rotation_euler',f)
        rig.location=(.005+.010*math.sin(t*.3),.005,.040)
        rig.rotation_euler=camera.rotation_euler
        a=ease((t-3.65)/.65)
        rig.scale=(max(.0001,a),)*3
        key(rig,'location',f);key(rig,'rotation_euler',f);key(rig,'scale',f)
        for i,o in enumerate(ripples):
            p=(t*.29+i/4)%1
            o.location=(-.065,0,.031+p*.035)
            o.scale=(.45+p*2.3,)*3
            strength=(1-p)*.78
            o.color=tuple(BG[j]+(TEAL[j]-BG[j])*strength for j in range(3))+(1,)
            key(o,'location',f);key(o,'scale',f);key(o,'color',f)
    checks=[1,60,106,144,192,234]
elif kind=='closing':
    scene,root,camera=base();n=109
    root.location=(-.062,0,.008)
    rig=empty('v20 | brand sculpture beside product')
    text3d('v20 | SafeWall brand lettering','SafeWall',.032,WHITE,rig,(0,0,0))
    svg_logo(rig)
    for f in range(1,n+1):
        t=(f-1)/FPS;u=t/(n/FPS)
        root.rotation_euler.z=math.radians(-13+12*u);key(root,'rotation_euler',f)
        look(camera,(.01+.020*u,-.30+.015*u,.31),(.008,.005,.023),48)
        key(camera,'location',f);key(camera,'rotation_euler',f)
        rig.location=(.008,.014,.042);rig.rotation_euler=camera.rotation_euler
        a=ease(t/.75);rig.scale=(max(.0001,a),)*3
        key(rig,'rotation_euler',f);key(rig,'scale',f)
    checks=[1,24,55,85,109]
else:raise ValueError(kind)

if kind!='docking':
    for o in bpy.data.objects:
        if not o.animation_data or not o.animation_data.action:continue
        action=o.animation_data.action
        curves=list(action.fcurves) if action.is_action_legacy else [fc for l in action.layers for s in l.strips for b in s.channelbags for fc in b.fcurves]
        for c in curves:
            for p in c.keyframe_points:p.interpolation='LINEAR'
    scene.frame_start=1;scene.frame_end=n
scene['visual_revision']='v20 spatial Blender '+kind
scene['flat_slides']=False;scene['premium_shaders_rendered']=False
scene.frame_set(1)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(kind+'-v20.blend')),compress=True)
dest=OUT/(kind+'-frames');dest.mkdir(exist_ok=True)
for f in (checks if stills else range(1,n+1)):
    if kind=='docking':
        src=1+(f-1)*119/95
        scene.frame_set(int(src),subframe=src-int(src))
    else:scene.frame_set(f)
    file=dest/f'{f:04d}.png'
    if not file.exists():
        scene.render.filepath=str(file);bpy.ops.render.render(write_still=True)
    if f%48==0:print('V20_RENDER',kind,f,n,flush=True)
(OUT/(kind+'-checks.json')).write_text(json.dumps({'frames':n,'engine':'BLENDER_WORKBENCH','sample_frames':checks,'stills_only':stills,'flat_slides':False},indent=2)+'\n')
if kind=='docking':
    # The rendered 96 frames sample the approved 120-frame motion. Bake that
    # time mapping into the saved scene as well, so its playback matches the cut.
    for action in bpy.data.actions:
        curves=list(action.fcurves) if action.is_action_legacy else [fc for l in action.layers for s in l.strips for b in s.channelbags for fc in b.fcurves]
        for curve in curves:
            for p in curve.keyframe_points:
                x,left,right=p.co.x,p.handle_left.x,p.handle_right.x
                p.co.x=1+(x-1)*95/119
                p.handle_left.x=1+(left-1)*95/119;p.handle_right.x=1+(right-1)*95/119
    scene.frame_end=96;scene.frame_set(1)
    scene['retimed_from_frames']=120
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'docking-v20.blend'),compress=True)
print('V20_SHOT_READY',kind,n,flush=True)
