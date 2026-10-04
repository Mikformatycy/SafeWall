"""Create a 540p Workbench blocking preview using Apple's official Pro Max mesh.

Run against Product-keynote-v04.blend. All premium materials are retained; the
original v04 file is never overwritten. Phone placement is a visualization study.
"""
import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'visualization'
REF = ROOT/'references'/'iphone'
scene = bpy.context.scene
assert scene['visual_revision'].startswith('v04')
scene.frame_set(120)


def serial(value):
    if isinstance(value, (str, int, float, bool)) or value is None: return value
    try: return list(value)
    except TypeError: return str(value)


# Snapshot actual shader values and lights before changing the preview scene.
materials = []
for mat in bpy.data.materials:
    if not mat.use_nodes: continue
    materials.append({'name': mat.name, 'diffuse_color_linear': list(mat.diffuse_color),
        'nodes': [{'name': n.name, 'type': n.bl_idname,
                   'inputs': {i.name: serial(i.default_value) for i in n.inputs if hasattr(i, 'default_value')}}
                  for n in mat.node_tree.nodes],
        'links': [[l.from_node.name, l.from_socket.name, l.to_node.name, l.to_socket.name]
                  for l in mat.node_tree.links]})
checkpoint = {'master_scene': 'Product-keynote-v04.blend',
    'master_sha256': hashlib.sha256((OUT/'Product-keynote-v04.blend').read_bytes()).hexdigest(),
    'builder': 'scripts/style_premium_scene.py', 'material_parameters': materials,
    'lighting': [{'name': o.name, 'position_m': list(o.location), 'rotation_rad': list(o.rotation_euler),
                 'power_W': o.data.energy, 'size_m': o.data.size, 'size_y_m': o.data.size_y}
                 for o in bpy.data.objects if o.type == 'LIGHT'],
    'color_management': {'view_transform': scene.view_settings.view_transform,
                        'look': scene.view_settings.look, 'exposure': scene.view_settings.exposure},
    'world_background': {i.name: serial(i.default_value) for i in scene.world.node_tree.nodes['Background'].inputs},
    'restore_exact_previous_look': 'Open Product-keynote-v04.blend and render with Cycles/Metal.',
    'reuse_in_docking_scene': 'Materials stay assigned. Switch Workbench to Cycles; relight for the upright phone and side camera.'}
(OUT/'premium-materials-v04.json').write_text(json.dumps(checkpoint, indent=2))
(OUT/'RESTORE-PREMIUM.txt').write_text('''MATERIAŁY PREMIUM — ZAPIS WERSJI v04

Dokładny poprzedni wygląd: otwórz Product-keynote-v04.blend.
Scena zawiera komplet shaderów, światła studyjne i animację 5 s.
Ten plik pozostaje niezmieniony podczas tworzenia podglądu z telefonem.

Pokrywa: piano black #080A0D, roughness 0.12, clearcoat 1.0 / roughness 0.07.
Boki: grafit #14171B, roughness 0.20, clearcoat 1.0 / roughness 0.13.
OLED: szkło #05070A, roughness 0.065, clearcoat 0.2 / roughness 0.045.
Ekran: chłodne białe piksele, przykładowe 87%.
Pełne parametry węzłów, kolory liniowe i światła: premium-materials-v04.json.
Skrypt odtwarzający wariant na bazie v03: ../scripts/style_premium_scene.py.

Podgląd telefonu: Phone-docking-preview-v05.blend, Workbench, 960 x 540.
Workbench pokazuje proste kolory obiektów i pomija shadery oraz lampy sceny.
Materiały premium pozostają przypisane do urządzenia; nie są kasowane.
Aby użyć ich w ujęciu telefonu, wybierz Cycles i dopasuj oświetlenie do nowej
orientacji urządzenia i kamery. Sama zmiana silnika nie odtworzy starego kadru.
Kolekcje wnętrza są ukryte tylko w tej scenie podglądowej.
''')

# Freeze the assembled device and retain its original geometry/material slots.
for obj in list(bpy.data.objects):
    obj.animation_data_clear()
    if obj.data and hasattr(obj.data, 'animation_data_clear'): obj.data.animation_data_clear()
for mat in bpy.data.materials:
    if mat.node_tree: mat.node_tree.animation_data_clear()
product = bpy.data.objects['SafeWall | product rotation']
product.name = 'Accessory | docking motion'
for col in bpy.data.collections:
    if col.name.startswith(('02 Battery', '03 Decorative', '04 Official', '05 Thermal')):
        col.hide_render = True; col.hide_viewport = True
bpy.data.objects['Seamless studio floor'].hide_render = True
bpy.data.objects['Seamless studio floor'].hide_viewport = True


def empty(name):
    obj = bpy.data.objects.new(name, None); scene.collection.objects.link(obj)
    obj.empty_display_size = .01
    return obj


rig = empty('Phone and accessory | shared contact response')
phone = empty('iPhone 18 Pro Max | official Apple reference')
phone.parent = rig; product.parent = rig
phone_col = bpy.data.collections.new('07 Official iPhone 18 Pro Max')
scene.collection.children.link(phone_col)
with bpy.data.libraries.load(str(REF/'apple-iphone-reference.blend'), link=False) as (source, target):
    target.objects = list(source.objects)
imported = [o for o in target.objects if o]
for obj in imported: phone_col.objects.link(obj)
bpy.context.view_layer.update()
max_root = next(o for o in imported if o.name == 'wUOhcMgiBmCgGaw')
meshes = [o for o in max_root.children_recursive if o.type == 'MESH']
frame_mesh = next(o for o in meshes if o.name == 'pcVAluKjKHsSebA')
frame_points = [frame_mesh.matrix_world@Vector(c) for c in frame_mesh.bound_box]
center = Vector(((min(p.x for p in frame_points)+max(p.x for p in frame_points))/2, 0,
                 (min(p.z for p in frame_points)+max(p.z for p in frame_points))/2))
for obj in meshes:
    transform = Matrix.Translation(-center) @ obj.matrix_world
    obj.data = obj.data.copy(); obj.data.transform(transform)
    obj.parent = phone; obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_basis = Matrix.Identity(4)
    obj.hide_render = False; obj.hide_viewport = False
for obj in imported:
    if obj not in meshes: bpy.data.objects.remove(obj, do_unlink=True)

# Find the real rear surface at the published wireless charging center.
vertices, faces = [], []
for obj in meshes:
    start = len(vertices); vertices += [v.co.copy() for v in obj.data.vertices]
    faces += [tuple(start+i for i in p.vertices) for p in obj.data.polygons]
phone_bvh = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
z_top = max(v.z for v in vertices); z_bottom = min(v.z for v in vertices)
coil_z = z_top-.08171  # Apple drawing sheet 4: 81.71 mm from top edge.
hit, normal, _, _ = phone_bvh.ray_cast(Vector((0, .1, coil_z)), Vector((0, -1, 0)))
assert hit is not None
back_y = hit.y
assert .0040 < back_y < .0047
contact_y = back_y+.00002  # 0.02 mm numerical clearance; not a manufactured tolerance.
device_z = coil_z-.025  # Existing magnet reservation is 25 mm above device center.
product.rotation_mode = 'QUATERNION'
product.rotation_quaternion = Matrix(((-1,0,0),(0,0,1),(0,1,0))).to_quaternion()
product.location = (0, contact_y+.068, device_z)

# Flat object colors: no PBR materials, textures or scene lights in this preview.
for obj in meshes:
    points = [v.co for v in obj.data.vertices]
    lo = [min(v[i] for v in points) for i in range(3)]
    hi = [max(v[i] for v in points) for i in range(3)]
    obj.color = (.61, .65, .71, 1)
    if hi[1] < -.0037: obj.color = (.12, .15, .20, 1)
    if lo[1] > .0078: obj.color = (.10, .13, .18, 1)
for obj in product.children_recursive:
    obj.color = (.24, .28, .34, 1)
    if obj.name.startswith('12 Lid'): obj.color = (.31, .35, .41, 1)
    if obj.name.startswith(('01 Contact', 'OLED | flush', 'OLED | elastomer', 'USB-C | deep')):
        obj.color = (.07, .09, .12, 1)
    if obj.name.startswith(('OLED | battery percentage', 'OLED | percent', 'OLED | battery icon',
                            'OLED | battery terminal', 'OLED | charge bar')):
        obj.color = (.84, .88, .92, 1)

scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 960; scene.render.resolution_y = 540
scene.render.resolution_percentage = 100
scene.render.fps = 24; scene.render.fps_base = 1
scene.frame_start = 1; scene.frame_end = 120
scene.render.film_transparent = False; scene.use_nodes = False
scene.display.render_aa = '16'
shading = scene.display.shading
shading.light = 'STUDIO'; shading.color_type = 'OBJECT'
shading.studio_light = 'paint.sl'
shading.background_type = 'WORLD'; scene.world.color = (.82, .85, .89)
shading.show_shadows = True; shading.show_cavity = True; shading.cavity_type = 'BOTH'
shading.curvature_ridge_factor = 1.1; shading.curvature_valley_factor = .8
shading.show_specular_highlight = False
shading.show_object_outline = False
scene.view_settings.view_transform = 'Standard'; scene.view_settings.look = 'None'
scene.view_settings.exposure = 0

camera = scene.camera
camera.data.type = 'ORTHO'; camera.data.ortho_scale = .35
camera.data.clip_start = .0001; camera.data.clip_end = 10
camera.location = (.32, .135, .021)
target = Vector((0, .042, -.001))
camera.rotation_euler = (target-camera.location).to_track_quat('-Z','Y').to_euler()


def gap_mm(frame):
    if frame <= 12: return 68.
    if frame <= 65:
        t = (frame-12)/53
        return 68-62*t**3
    if frame < 69:
        t = (frame-65)/4
        # Cubic Hermite catch: match incoming velocity, finish at zero velocity.
        return (2*t**3-3*t*t+1)*6+(t**3-2*t*t+t)*(-3*62/53)*4
    return 0.


for frame in range(1, 121):
    product.location = (0, contact_y+gap_mm(frame)*.001, device_z)
    product.keyframe_insert('location', frame=frame)
    # Pan with the midpoint of the pair while retaining the fixed side angle.
    camera.location = (.32, .101+gap_mm(frame)*.0005, .021)
    camera.keyframe_insert('location', frame=frame)
    seconds = max(0, (frame-69)/24)
    angle = 0 if frame >= 89 else math.radians(.8)*math.exp(-seconds/.18)*math.sin(seconds*2*math.pi/.34)
    rig.rotation_euler.x = angle
    rig.keyframe_insert('rotation_euler', frame=frame)
for obj in (product, rig, camera):
    action = obj.animation_data.action
    curves = list(action.fcurves) if action.is_action_legacy else [
        fc for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
    for curve in curves:
        for key in curve.keyframe_points: key.interpolation = 'LINEAR'
scene.timeline_markers.clear()
for frame, label in [(1,'Side view'),(12,'Slow departure'),(48,'Magnetic approach accelerates'),
                     (65,'Short eased catch'),(69,'Attached'),(89,'Settled hold')]:
    scene.timeline_markers.new(label, frame=frame)
scene['visual_revision'] = 'v05 | iPhone 18 Pro Max docking / fast Workbench preview'
scene['preview_kind'] = 'Kinematic motion and proportions study; not a magnet force simulation or case qualification'
scene['premium_master'] = 'Product-keynote-v04.blend'
scene['phone_reference'] = 'Official Apple iPhone 18 Pro / Pro Max USDZ; larger instance isolated'

# Validate the contact gap, camera framing and stationary final relative pose.
visible = [o for o in list(product.children_recursive)+meshes if o.type == 'MESH'
           and not o.hide_render and not any(c.hide_render for c in o.users_collection)]
frames = []
for frame in range(1,121):
    scene.frame_set(frame); bpy.context.view_layer.update()
    corners = [world_to_camera_view(scene,camera,o.matrix_world@Vector(c)) for o in visible for c in o.bound_box]
    bounds = [min(v.x for v in corners),min(v.y for v in corners),max(v.x for v in corners),max(v.y for v in corners)]
    assert bounds[0] > .01 and bounds[1] > .01 and bounds[2] < .99 and bounds[3] < .99, (frame,bounds)
    assert gap_mm(frame) >= -1e-8
    frames.append({'frame':frame,'gap_mm':gap_mm(frame),'frame_bounds':bounds})
scene.frame_set(120); bpy.context.view_layer.update()
camera_points = [v for v in vertices if v.y > back_y+.0008]
camera_clearance = min(v.z for v in camera_points)-(device_z+.055)
assert camera_clearance > 0, 'Camera geometry overlaps the accessory footprint'
report = {'status':'preview_scene_ready','phone':'iPhone 18 Pro Max','phone_source':'https://www.apple.com/iphone-18-pro/',
          'dimensional_reference':'https://developer.apple.com/download/files/accessories/dimensional-drawings/iphone-18-pro-max.pdf',
          'phone_mesh_parts':len(meshes),'phone_mesh_height_mm':(z_top-z_bottom)*1000,
          'phone_body_thickness_reference_mm':8.75,'accessory_envelope_mm':[70,110,24],
          'phone_back_surface_y_mm':back_y*1000,'contact_clearance_mm':.02,'magnet_axis_aligned':True,
          'camera_plateau_clearance_mm':camera_clearance*1000,'accessory_bottom_margin_mm':(device_z-.055-z_bottom)*1000,
          'duration_seconds':5,'fps':24,'frames_checked':120,'resolution':[960,540],
          'engine':'Workbench; object colors, no PBR shading','shaders_preserved':True,'frame_checks':frames}
(OUT/'docking-preview-v05.json').write_text(json.dumps(report,indent=2))
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.shading.type = 'SOLID'
            area.spaces.active.shading.color_type = 'OBJECT'
            area.spaces.active.overlay.show_overlays = False
scene.render.filepath = str(OUT/'docking-frames-v05'/'docking_')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Phone-docking-preview-v05.blend'),compress=True)
print('DOCKING_SCENE_READY',json.dumps({k:v for k,v in report.items() if k!='frame_checks'}),flush=True)
for frame,name in [(1,'phone-docking-open-v05.png'),(120,'phone-docking-attached-v05.png')]:
    scene.frame_set(frame); scene.render.filepath = str(OUT/name)
    bpy.ops.render.render(write_still=True)
print('DOCKING_STILLS_READY',flush=True)
