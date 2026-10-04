"""Blender 4.5: detailed concept visualization and a ten-second assembly animation.

Run: blender --background --python build_product_scene.py -- --preview
CM4 geometry is the official Raspberry Pi STEP, converted through Fusion MCP.
Carrier components, traces, battery finish and ports are visualization details only.
"""
import argparse
import json
import math
import random
import re
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'visualization'
MM=0.001
random.seed(16)


def linear(v):
    return v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4


def rgba(hexcode):
    return tuple(linear(int(hexcode[i:i+2],16)/255) for i in (1,3,5))+(1,)


def material(name,color,roughness=0.4,metallic=0,texture=0):
    mat=bpy.data.materials.new(name)
    mat.diffuse_color=rgba(color)
    mat.use_nodes=True
    shader=mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value=rgba(color)
    shader.inputs['Roughness'].default_value=roughness
    shader.inputs['Metallic'].default_value=metallic
    if texture:
        nodes=mat.node_tree.nodes
        tex=nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=420
        tex.inputs['Detail'].default_value=2
        bump=nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value=0.16
        bump.inputs['Distance'].default_value=texture*MM
        mat.node_tree.links.new(tex.outputs['Fac'],bump.inputs['Height'])
        mat.node_tree.links.new(bump.outputs['Normal'],shader.inputs['Normal'])
    return mat


def assign(obj,mat):
    obj.data.materials.clear();obj.data.materials.append(mat)


def empty(name,collection):
    obj=bpy.data.objects.new(name,None);collection.objects.link(obj)
    obj.empty_display_size=0.008
    return obj


def relocate(obj,collection):
    for col in list(obj.users_collection):col.objects.unlink(obj)
    collection.objects.link(obj)


def cube(name,center,size,mat,parent=None,bevel=0.15):
    bpy.ops.mesh.primitive_cube_add(size=1,location=tuple(v*MM for v in center))
    obj=bpy.context.object;obj.name=name;obj.dimensions=tuple(v*MM for v in size)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=obj.modifiers.new('Soft manufactured edges','BEVEL');mod.width=bevel*MM;mod.segments=3
        mod=obj.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    assign(obj,mat)
    if parent:obj.parent=parent;relocate(obj,parent.users_collection[0])
    return obj


def cylinder(name,center,radius,depth,mat,parent=None,vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius*MM,depth=depth*MM,location=tuple(v*MM for v in center))
    obj=bpy.context.object;obj.name=name;assign(obj,mat)
    mod=obj.modifiers.new('Small edge bevel','BEVEL');mod.width=min(depth/5,0.08)*MM;mod.segments=2
    mod=obj.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    if parent:obj.parent=parent;relocate(obj,parent.users_collection[0])
    return obj


def text(name,body,pos,size,mat,parent=None,align='LEFT',rotation=None):
    data=bpy.data.curves.new(name,'FONT');data.body=body;data.size=size*MM;data.align_x=align
    data.space_character=1.12;data.extrude=0
    obj=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(obj)
    obj.location=tuple(v*MM for v in pos)
    if rotation:obj.rotation_euler=rotation
    assign(obj,mat)
    if parent:obj.parent=parent;relocate(obj,parent.users_collection[0])
    return obj


def wire(name,points,radius,mat,parent):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D'
    data.resolution_u=8;data.bevel_depth=radius*MM;data.bevel_resolution=3
    spline=data.splines.new('POLY');spline.points.add(len(points)-1)
    for p,co in zip(spline.points,points):p.co=tuple(v*MM for v in co)+(1,)
    obj=bpy.data.objects.new(name,data);parent.users_collection[0].objects.link(obj);obj.parent=parent
    assign(obj,mat)
    return obj


def import_obj(path):
    before=set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=str(path),global_scale=MM,forward_axis='Y',up_axis='Z',use_split_objects=False,use_split_groups=True)
    return [o for o in bpy.data.objects if o not in before and o.type=='MESH']


def bounds(objects):
    points=[o.matrix_world@Vector(corner) for o in objects for corner in o.bound_box]
    return [[min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]]


def look_at(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()


def softbox(name,pos,target,power,size,size_y=None):
    data=bpy.data.lights.new(name,'AREA');data.energy=power
    data.shape='RECTANGLE';data.size=size;data.size_y=size_y or size
    obj=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(obj)
    obj.location=pos;look_at(obj,target)
    return obj


def animate_group(obj,offset,start,end):
    obj.location=Vector(offset)*MM
    obj.keyframe_insert('location',frame=1)
    obj.keyframe_insert('location',frame=start)
    obj.location=(0,0,0)
    obj.keyframe_insert('location',frame=end)
    obj.keyframe_insert('location',frame=240)


def main():
    args=argparse.ArgumentParser();args.add_argument('--preview',action='store_true');args.add_argument('--animation',action='store_true')
    opts=args.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    OUT.mkdir(exist_ok=True)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for collection in list(bpy.data.collections):
        if collection.name=='Collection':bpy.data.collections.remove(collection)
    scene=bpy.context.scene
    scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='MILLIMETERS'
    scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True
    scene.cycles.max_bounces=8
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='METAL';prefs.get_devices()
    for device in prefs.devices:device.use=(device.type=='METAL')
    if any(d.type=='METAL' for d in prefs.devices):scene.cycles.device='GPU'
    scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.fps=24
    scene.frame_start=1;scene.frame_end=240
    scene.view_settings.view_transform='AgX'
    scene.render.film_transparent=False
    scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.72,0.77,0.84,1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0.18
    scene['purpose']='Visual design study. Decorative carrier electronics are not an electrical PCB design.'
    scene['phone_target']='iPhone 16; phone and case fit not validated'
    scene['CM4_source']='https://pip.raspberrypi.com/categories/1204-design-files'

    mats={
        'shell':material('CMF | graphite PC-ABS satin','#333941',0.31,0,0.018),
        'silicone':material('CMF | soft dark silicone','#202329',0.72,0,0.025),
        'pcb':material('PCB | dark forest solder mask','#124C38',0.34,0,0.006),
        'trace':material('PCB | traces beneath solder mask','#246D4C',0.38,0.15),
        'chip':material('IC | black epoxy package','#26282B',0.54,0,0.005),
        'silver':material('Metal | satin nickel shield','#A7AFB5',0.27,0.93,0.003),
        'solder':material('Metal | solder fillets','#BBC5CE',0.22,0.92),
        'gold':material('Metal | ENIG gold pads','#D1AB5C',0.26,0.82),
        'copper':material('Thermal | brushed copper','#BF784B',0.3,0.9),
        'battery':material('Battery | laminated pouch foil','#B4BAC3',0.33,0.8,0.018),
        'battery_label':material('Battery | charcoal label','#32373F',0.5),
        'ink':material('Print | warm silkscreen','#C9D3C9',0.56),
        'dark_ink':material('Print | understated shell marking','#77808A',0.5),
        'ceramic':material('SMD | ceramic capacitor','#B4A382',0.52),
        'red':material('Wire | positive insulation','#A34839',0.5),
        'magnet':material('Magnet | plated reserved array','#454F59',0.34,0.75),
    }
    collections={}
    groups={}
    for key,label in [('base','01 Housing'),('battery','02 Battery'),('carrier','03 Decorative carrier PCB'),('cm4','04 Official Raspberry Pi CM4'),('thermal','05 Thermal concept'),('lid','06 Cover')]:
        col=bpy.data.collections.new(label);scene.collection.children.link(col);collections[key]=col
        groups[key]=empty(label+' | ANIMATE',col)
    product=empty('SafeWall | product rotation',scene.collection)
    for group in groups.values():group.parent=product

    imported=import_obj(ROOT/'exports'/'SafeWall-B-concept-v01.obj')
    bpy.context.view_layer.update()
    box=bounds(imported);extent=[round((box[1][i]-box[0][i])/MM,4) for i in range(3)]
    if extent!=[70.0,110.0,24.0]:raise RuntimeError('Unexpected enclosure mesh orientation/scale: '+str(extent))
    for obj in imported:
        name=obj.name
        if name.startswith(('08','10')):
            bpy.data.objects.remove(obj,do_unlink=True);continue
        key='base';mat=mats['shell']
        if name.startswith('01'):mat=mats['silicone']
        elif name.startswith(('03','04')):mat=mats['magnet']
        elif name.startswith('06'):key='battery';mat=mats['battery']
        elif name.startswith('07'):key='carrier';mat=mats['pcb']
        elif name.startswith('09'):key='carrier';mat=mats['silver']
        elif name.startswith('11'):key='thermal';mat=mats['copper']
        elif name.startswith('12'):key='lid'
        obj.location+=Vector((-35*MM,-55*MM,0));obj.parent=groups[key]
        relocate(obj,collections[key]);assign(obj,mat)
        if name.startswith(('06','07','09','11')):
            mod=obj.modifiers.new('Tiny manufactured edge highlights','BEVEL');mod.width=0.09*MM;mod.segments=2
            mod=obj.modifiers.new('Weighted normals','WEIGHTED_NORMAL')

    print('Loading detailed official CM4 mesh',flush=True)
    cm4=import_obj(ROOT/'references'/'cm4-official'/'CM4.obj')
    bpy.context.view_layer.update()
    cm4box=bounds(cm4)
    cm4extent=[round((cm4box[1][i]-cm4box[0][i])/MM,3) for i in range(3)]
    if cm4extent[:2]!=[55.0,40.0]:raise RuntimeError('Unexpected official CM4 orientation: '+str(cm4extent))
    # Source board datum z=0, XY=(0,16). Align PCB bottom to 3 mm above carrier top.
    shift=Vector((-27.5*MM,-19*MM,16.9*MM))
    official_materials=set()
    for obj in cm4:
        obj.location+=shift;obj.parent=groups['cm4'];relocate(obj,collections['cm4'])
        for slot in obj.material_slots:
            if slot.material:official_materials.add(slot.material)
    for mat in official_materials:
        match=re.search(r'Opaque\((\d+),(\d+),(\d+)\)',mat.name)
        if not match:continue
        rgb=tuple(int(v) for v in match.groups())
        mat.use_nodes=True;shader=mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value=tuple(linear(v/255) for v in rgb)+(1,)
        shader.inputs['Roughness'].default_value=0.48
        if max(rgb)-min(rgb)<35 and sum(rgb)/3>125:
            shader.inputs['Metallic'].default_value=0.85;shader.inputs['Roughness'].default_value=0.3
        if rgb==(26,89,36):
            shader.inputs['Base Color'].default_value=rgba('#216B43');shader.inputs['Roughness'].default_value=0.32
        if rgb==(64,64,64):shader.inputs['Base Color'].default_value=rgba('#2B2E33')
        if rgb==(255,255,255):shader.inputs['Metallic'].default_value=0;shader.inputs['Roughness'].default_value=0.6
        if rgb in [(222,161,44),(184,115,51)]:shader.inputs['Metallic'].default_value=0.8

    carrier=groups['carrier'];battery=groups['battery'];lid=groups['lid'];base=groups['base']
    # Layered pouch construction, label and short illustrative leads.
    cube('Battery printed label - visualization',(-0.2,-4,10.35),(40,63,0.08),mats['battery_label'],battery,1)
    text('Battery label','SAFEWALL\nRECHARGEABLE\n3.7 V  /  12.6 Wh',(-16,10,10.41),2.4,mats['ink'],battery)
    text('Battery reference note','CELL REFERENCE  /  3400 mAh',(-16,-17,10.41),1.2,mats['ink'],battery)
    for x in [-26.2,26.2]:cube('Pouch crimp edge',(x,-2,10.25),(1.8,84,0.22),mats['silver'],battery,0.1)
    wire('Battery red lead',[(19,-42,9),(23,-44,9),(26,-43,10),(26,-39,11)],0.42,mats['red'],battery)
    wire('Battery black lead',[(17,-42,9),(20,-46,9),(25,-46,10),(27,-40,11)],0.42,mats['chip'],battery)
    cube('Battery harness plug',(26,-38,11),(4,3,2),mats['ink'],battery,0.2)

    # Original decorative carrier population: realistic scale, no claimed routing.
    text('Carrier identity','SAFEWALL  /  CM4',(-26,-41,13.94),1.7,mats['ink'],carrier)
    text('Carrier revision','CARRIER 01',(-26,38,13.94),1.15,mats['ink'],carrier)
    text('LTE shield identity','LTE\nMODULE',(-22,-29,16.34),2.5,mats['dark_ink'],carrier)
    text('CM4 processor marking','BCM2711',(-.5,13,20.56),1.1,mats['ink'],groups['cm4'])
    for cx,cy,w,h in [(20,-32,7,7),(20,-18,6,6),(-16,-6,8,5),(-3,-6,6,5)]:
        cube('Decorative QFN controller',(cx,cy,14.55),(w,h,1.2),mats['chip'],carrier,0.14)
        text('IC laser marking','SW\n16A',(cx-w*.30,cy,15.17),0.85,mats['ink'],carrier)
        for j in range(7):
            for sign in [-1,1]:cube('QFN solder lead',(cx-w/2+(j+1)*w/8,cy+sign*(h/2+0.2),14.14),(0.4,0.75,0.3),mats['solder'],carrier,0.04)
    for x,y in [(20,-8),(12,-40),(23,-42)]:
        cube('Shielded power inductor',(x,y,15),(4.6,4.6,2.1),mats['chip'],carrier,0.35)
        text('Inductor marking','2R2',(x-1.4,y-.6,16.08),1,mats['ink'],carrier)
    for index in range(58):
        if index<30:
            x=-26+(index%15)*3.6;y=-10-(index//15)*2.4
        else:
            x=13+(index%4)*3.5;y=-35+(index//4-7)*2.7
        if 16<x<24 and -36<y<-27:continue
        width=1.4 if index%3 else 1.9
        mat=mats['ceramic'] if index%2 else mats['chip']
        cube('Decorative SMD passive',(x,y,14.22),(width,0.75,0.6),mat,carrier,0.06)
        for side in [-1,1]:cube('Solder termination',(x+side*width*.48,y,14.17),(0.45,0.85,0.42),mats['solder'],carrier,0.045)
    for y in [-42,-36,-30,-24,-18]:
        for x in [-28.0,28.0]:
            cylinder('Gold test pad',(x,y,13.94),0.5,0.04,mats['gold'],carrier,20)
            cylinder('Plated via center',(x,y,13.97),0.16,0.05,mats['chip'],carrier,16)
    for index in range(19):
        x=-25+index*2.5
        wire('Decorative masked trace',[(x,-39,13.93),(x,-36,13.93),(x+2,-34,13.93),(x+2,-13,13.93)],0.07,mats['trace'],carrier)
    for x,y in [(-26,-41),(26,-41),(-26,39),(26,39)]:
        cylinder('Carrier plated mounting land',(x,y,13.94),1.8,0.07,mats['gold'],carrier)
        cylinder('Carrier mounting hole visualization',(x,y,14),1,0.09,mats['chip'],carrier)
    for y in [0,34]:
        cube('CM4 mating connector',(0,y,15.35),(22,3.2,2.8),mats['chip'],carrier,0.1)
        for i in range(40):
            cube('Connector contact',(-10.4+i*0.53,y-1.55,16.3),(0.2,0.2,0.6),mats['gold'],carrier,0.02)

    # Rendering-only port indication and restrained cover mark.
    port=cube('USB-C dark opening - visual proposal',(0,-55.035,11.6),(9.4,0.18,3.5),mats['chip'],base,0.75)
    cube('USB-C tongue - visual proposal',(0,-55.15,11.6),(6.2,0.15,0.65),mats['silver'],base,0.12)
    for x in [-2.2,-1.5,-.8,0,.8,1.5,2.2]:cube('USB-C contact - visual proposal',(x,-55.25,11.78),(0.25,0.1,0.12),mats['gold'],base,0.01)
    text('Cover wordmark','SAFEWALL',(-23,-37,24.015),3.2,mats['dark_ink'],lid)
    cylinder('Small status lens',(23,-39,24.015),0.52,0.05,mats['silicone'],lid)
    for x,y in [(-29,-46),(29,-46),(-29,46),(29,46)]:
        cylinder('Cover fastener detail',(x,y,22.5),1.3,1.9,mats['silver'],lid)

    animate_group(groups['battery'],(0,-3,22),42,78)
    animate_group(groups['carrier'],(0,0,51),70,113)
    animate_group(groups['cm4'],(0,4,72),102,144)
    animate_group(groups['thermal'],(0,8,98),131,173)
    animate_group(groups['lid'],(0,12,129),160,210)
    product.rotation_euler.z=math.radians(-9);product.keyframe_insert('rotation_euler',frame=1)
    product.rotation_euler.z=0;product.keyframe_insert('rotation_euler',frame=150)
    product.rotation_euler.z=math.radians(14);product.keyframe_insert('rotation_euler',frame=240)

    floor=material('Studio | soft warm white','#E8E9EC',0.58)
    floor_obj=cube('Seamless studio floor',(0,0,-2),(2000,2000,2),floor,bevel=0)
    floor_obj.is_shadow_catcher=True
    scene.render.film_transparent=True
    scene.use_nodes=True
    nodes=scene.node_tree.nodes;nodes.clear()
    layer=nodes.new('CompositorNodeRLayers')
    over=nodes.new('CompositorNodeAlphaOver');over.inputs[1].default_value=(4,4,4,1)
    output=nodes.new('CompositorNodeComposite')
    scene.node_tree.links.new(layer.outputs['Image'],over.inputs[2])
    scene.node_tree.links.new(over.outputs['Image'],output.inputs['Image'])
    softbox('Key | broad silk',(-0.2,-0.19,0.38),(0,0,0.04),1.225,0.28,0.22)
    softbox('Rim | tall strip',(0.18,0.1,0.28),(0,0,0.08),1.575,0.07,0.3)
    softbox('Fill | front card',(0.10,-0.24,0.12),(0,0,0.06),0.28,0.18,0.25)
    softbox('Top | diffuse',(0,0.03,0.45),(0,0,0),0.525,0.25)
    camera_data=bpy.data.cameras.new('Product camera | 70 mm')
    camera=bpy.data.objects.new('Product camera',camera_data);scene.collection.objects.link(camera);scene.camera=camera
    camera_data.type='ORTHO';camera_data.lens=70;camera_data.clip_start=0.001;camera_data.clip_end=20
    for frame,target,pos,scale in [(1,(0,0,0.078),(0.25,-0.34,0.26),0.38),
                                   (160,(0,0,0.078),(0.25,-0.34,0.26),0.38),
                                   (185,(0,0,0.045),(0.24,-0.33,0.255),0.29),
                                   (210,(0,0,0.017),(0.23,-0.32,0.25),0.19),
                                   (240,(0,0,0.016),(0.21,-0.31,0.24),0.18)]:
        camera.location=pos;look_at(camera,target);camera_data.ortho_scale=scale
        camera.keyframe_insert('location',frame=frame);camera.keyframe_insert('rotation_euler',frame=frame)
        camera_data.keyframe_insert('ortho_scale',frame=frame)
    for frame,label in [(1,'Exploded hero'),(42,'Battery seats'),(70,'Carrier seats'),(102,'CM4 seats'),(131,'Thermal concept seats'),(160,'Cover closes'),(210,'Assembled hero')]:
        marker=scene.timeline_markers.new(label,frame=frame)
    scene.frame_set(1)
    bpy.context.view_layer.update()
    for obj in bpy.context.selected_objects:obj.select_set(False)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active
                space.region_3d.view_perspective='CAMERA'
                space.region_3d.view_camera_zoom=0
                space.clip_start=.0001
                space.shading.type='MATERIAL'
                space.shading.use_scene_lights=True
                space.shading.use_scene_world=True
                space.overlay.show_overlays=False
    scene.render.filepath=str(OUT/'frames'/'assembly_')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'SafeWall-keynote-v01.blend'),compress=True)
    report={'status':'editable_visual_concept_scene','phone':'iPhone 16','frames':240,'fps':24,'duration_seconds':10,
            'CM4_source':'official Raspberry Pi STEP converted in Fusion','CM4_imported_mesh_objects':len(cm4),
            'CM4_bounds_mm':cm4extent,'enclosure_extent_mm':extent,'objects':len(bpy.data.objects),
            'decorative_only':['carrier components and traces','battery finish and label','port appearance','cover fasteners'],
            'animation_parts':list(groups),'renderer':'Cycles Metal if available','GPU_devices':[d.name for d in prefs.devices if d.use]}
    (OUT/'scene-manifest.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)
    if opts.preview:
        scene.render.resolution_percentage=65;scene.cycles.samples=32
        for frame,name in [(1,'exploded-preview.png'),(240,'assembled-preview.png')]:
            scene.frame_set(frame);scene.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True)
    if opts.animation:
        scene.render.engine='CYCLES';scene.cycles.samples=16
        scene.render.resolution_percentage=50
        scene.render.filepath=str(OUT/'frames'/'assembly_')
        bpy.ops.render.render(animation=True)


if __name__ == '__main__':
    main()
