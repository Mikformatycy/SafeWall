"""Create v02 from the v01 Blender scene: softened shell, OLED and explicit easing.

blender --background visualization/SafeWall-keynote-v01.blend --python this_file
All new mechanical/display geometry is a visual concept, not a selected assembly.
"""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_product_scene import material, assign, cube, text, wire, look_at, MM

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'visualization'
scene = bpy.context.scene
scene.frame_set(240)
base = bpy.data.objects['01 Housing | ANIMATE']
lid = bpy.data.objects['06 Cover | ANIMATE']
product = bpy.data.objects['SafeWall | product rotation']


def remove_prefixes(prefixes):
    for obj in list(bpy.data.objects):
        if obj.name.startswith(prefixes):
            bpy.data.objects.remove(obj, do_unlink=True)


def outline(width, height, radius, steps=20):
    points = []
    for cx, cy, start in [(width/2-radius, height/2-radius, 0),
                          (-width/2+radius, height/2-radius, 90),
                          (-width/2+radius, -height/2+radius, 180),
                          (width/2-radius, -height/2+radius, 270)]:
        for i in range(steps+1):
            angle = math.radians(start+90*i/steps)
            points.append((cx+radius*math.cos(angle), cy+radius*math.sin(angle)))
    return points


def profile_mesh(name, profiles, mat, parent, inner=None):
    """Loft (z, width, height, corner radius) rings, optionally a hollow perimeter."""
    vertices, faces = [], []
    count = len(outline(*profiles[0][1:]))
    for z, width, height, radius in profiles:
        vertices += [(x*MM, y*MM, z*MM) for x, y in outline(width, height, radius)]
    for ring in range(len(profiles)-1):
        a, b = ring*count, (ring+1)*count
        faces += [(a+i, a+(i+1)%count, b+(i+1)%count, b+i) for i in range(count)]
    if inner:
        offset = len(vertices)
        for z in (profiles[0][0], profiles[-1][0]):
            vertices += [(x*MM, y*MM, z*MM) for x, y in outline(*inner)]
        faces += [(offset+i, offset+count+i, offset+count+(i+1)%count, offset+(i+1)%count) for i in range(count)]
        last = (len(profiles)-1)*count
        faces += [(i, offset+i, offset+(i+1)%count, (i+1)%count) for i in range(count)]
        faces += [(last+i, last+(i+1)%count, offset+count+(i+1)%count, offset+count+i) for i in range(count)]
    else:
        faces += [tuple(reversed(range(count))), tuple(range(len(vertices)-count, len(vertices)))]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(name, mesh)
    parent.users_collection[0].objects.link(obj); obj.parent = parent
    assign(obj, mat)
    for polygon in mesh.polygons:
        polygon.use_smooth = abs(polygon.normal.z) < .999
    return obj


def plate(name, center, size, radius, mat, parent, inner=None):
    width, height, depth = size
    obj = profile_mesh(name, [(-depth/2, width, height, radius),
                               (depth/2, width, height, radius)], mat, parent, inner)
    obj.location = Vector(center)*MM
    return obj


def cut(target, cutter):
    bpy.ops.object.select_all(action='DESELECT')
    target.select_set(True); bpy.context.view_layer.objects.active = target
    mod = target.modifiers.new('Manufactured visual recess', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'; mod.solver = 'EXACT'; mod.object = cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    mod = target.modifiers.new('Stable broad surface normals', 'WEIGHTED_NORMAL')
    mod.keep_sharp = True; mod.weight = 50


def smootherstep(t):
    t = min(1.0, max(0.0, t))
    return t*t*t*(t*(t*6-15)+10)


def progress(frame, start, end):
    return smootherstep((frame-start)/(end-start))


def linear_keys(owner):
    animation = owner.animation_data
    if not animation or not animation.action:
        return
    action = animation.action
    curves = list(action.fcurves) if action.is_action_legacy else [
        fc for layer in action.layers for strip in layer.strips
        for bag in strip.channelbags for fc in bag.fcurves]
    for curve in curves:
        for key in curve.keyframe_points:
            key.interpolation = 'LINEAR'


# Retain the established 70 x 110 x 24 mm packaging envelope.
shell_mat = bpy.data.materials['CMF | graphite PC-ABS satin']
shell_shader = shell_mat.node_tree.nodes.get('Principled BSDF')
shell_shader.inputs['Roughness'].default_value = .29
dark = material('Powerbank | recessed black polymer', '#101318', .39)
silver = bpy.data.materials['Metal | satin nickel shield']
gold = bpy.data.materials['Metal | ENIG gold pads']
ink = bpy.data.materials['Print | understated shell marking']
remove_prefixes(('Shell perimeter', '02 Rear panel', '12 Lid', 'USB-C ', 'Cover wordmark', 'Small status lens'))

# The broad edge roll replaces the hard vertical box profile.
bottom_profiles = []
for i in range(9):
    t = i/8*math.pi/2
    z = .6+2.4*(1-math.cos(t))
    inset = 2.4*(1-math.sin(t))
    bottom_profiles.append((z, 70-2*inset, 110-2*inset, 9-inset))
rear = profile_mesh('02 Rear panel | soft lower edge', bottom_profiles, shell_mat, base)
body = profile_mesh('Shell perimeter | powerbank profile', [
    (3, 70, 110, 9), (19.2, 70, 110, 9), (20.2, 69.84, 109.84, 8.92),
    (21.2, 69.32, 109.32, 8.66), (22.2, 68.35, 108.35, 8.175)],
    shell_mat, base, inner=(66.8, 106.8, 7.4))
cover = profile_mesh('12 Lid | rolled powerbank cover', [
    (22.4, 68.08, 108.08, 8.04), (22.8, 67.37, 107.37, 7.685),
    (23.2, 66.37, 106.37, 7.185), (23.6, 64.96, 104.96, 6.48),
    (23.88, 63.1, 103.1, 5.55), (24.0, 61.0, 101.0, 4.5)], shell_mat, lid)

# A real recessed connector aperture, shell lip, dark cavity and inset tongue.
port_cut = plate('Temporary port aperture', (0, -53.5, 11.6), (10.4, 4.4, 8), 2.05, dark, base)
port_cut.rotation_euler.x = math.pi/2
cut(body, port_cut)
port_rim = plate('USB-C | inset metal socket', (0, -54.63, 11.6), (9.25, 3.45, .5), 1.65,
                 silver, base, inner=(8.5, 2.7, 1.3))
port_rim.rotation_euler.x = math.pi/2
port_cavity = plate('USB-C | deep cavity', (0, -53.9, 11.6), (8.7, 2.9, .12), 1.35, dark, base)
port_cavity.rotation_euler.x = math.pi/2
port_tongue = plate('USB-C | polymer tongue', (0, -54.1, 11.6), (6.5, .72, .36), .32, dark, base)
port_tongue.rotation_euler.x = math.pi/2
for index in range(12):
    cube('USB-C | contact', (-2.8+index*.51, -54.29, 11.87), (.24, .06, .1), gold, base, .01)

# Discreet physical battery-check button beside the USB-C connector.
button_surround = plate('Battery button | seam', (20, -55.02, 11.6), (5.9, 2.8, .16), 1.35, dark, base)
button_surround.rotation_euler.x = math.pi/2
button = plate('Battery button | graphite cap', (20, -55.14, 11.6), (5.35, 2.25, .17), 1.1, shell_mat, base)
button.rotation_euler.x = math.pi/2

# A shallow display lens. All dimensions are a styling study pending part selection.
display_cut = plate('Temporary OLED recess', (0, -29, 24.0), (29, 17, 3.8), 3.2, dark, lid)
cut(cover, display_cut)
bezel = plate('OLED | elastomer perimeter gasket', (0, -29, 23.38), (28.75, 16.75, 1.1), 3.1, dark, lid)
glass_mat = material('OLED | smoked polished glass', '#070B10', .13, .08)
glass_shader = glass_mat.node_tree.nodes.get('Principled BSDF')
glass_shader.inputs['Coat Weight'].default_value = .8
glass_shader.inputs['Coat Roughness'].default_value = .08
glass_shader.inputs['IOR'].default_value = 1.48
glass = plate('OLED | flush black glass', (0, -29, 23.86), (28.35, 16.35, .21), 2.9, glass_mat, lid)
glass['visual_concept'] = 'Opaque smoked OLED cover lens; module and flex cable not selected'
display_back = plate('OLED | module backplate reference', (0, -29, 22.28), (26, 14, .6), 1.6, dark, lid)

pixels = bpy.data.materials.new('OLED | cool white emissive pixels')
pixels.use_nodes = True
nodes = pixels.node_tree.nodes; nodes.clear()
emission = nodes.new('ShaderNodeEmission'); emission.inputs['Color'].default_value = (.73, .91, 1.0, 1)
emission.inputs['Strength'].default_value = 2.2
transparent = nodes.new('ShaderNodeBsdfTransparent')
pixel_fade = nodes.new('ShaderNodeMixShader')
pixels.node_tree.links.new(transparent.outputs[0], pixel_fade.inputs[1])
pixels.node_tree.links.new(emission.outputs[0], pixel_fade.inputs[2])
out = nodes.new('ShaderNodeOutputMaterial'); pixels.node_tree.links.new(pixel_fade.outputs[0], out.inputs['Surface'])
font = bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Arial.ttf')
number = text('OLED | battery percentage demo', '87', (-1.2, -29.8, 23.98), 9.4, pixels, lid, align='CENTER')
number.data.font = font; number.data.space_character = 1.0
percent = text('OLED | percent unit', '%', (4.55, -29.15, 23.98), 3.3, pixels, lid)
percent.data.font = font
# Small battery glyph and five glowing charge bars, all inside the glass perimeter.
icon = plate('OLED | battery icon outline', (0, -33.7, 23.989), (7.5, 2.25, .012), .4, pixels, lid,
             inner=(6.93, 1.68, .2))
plate('OLED | battery terminal', (4.02, -33.7, 23.989), (.58, .92, .012), .12, pixels, lid)
for i in range(5):
    plate('OLED | charge bar', (-2.62+i*1.14, -33.7, 23.989), (.82, 1.17, .014), .09, pixels, lid)
wordmark = text('Cover wordmark', 'SAFEWALL', (0, 30, 24.02), 2.8, ink, lid, align='CENTER')
wordmark.data.font = font; wordmark.data.space_character = 1.18
# Embed letter geometry instead of creating a dependency on a system font.
for obj in (number, percent, wordmark):
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')

# Merge official parts without simplifying geometry. This lowers render setup cost.
official = bpy.data.collections['04 Official Raspberry Pi CM4']
cm4_meshes = [o for o in official.objects if o.type == 'MESH' and o.name.startswith('Body')]
if cm4_meshes:
    polygons_before = sum(len(o.data.polygons) for o in cm4_meshes)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in cm4_meshes: obj.select_set(True)
    bpy.context.view_layer.objects.active = cm4_meshes[0]
    bpy.ops.object.join()
    joined = bpy.context.object; joined.name = 'CM4 | official detailed geometry'
    assert len(joined.data.polygons) == polygons_before
    joined['source_part_count'] = len(cm4_meshes)
    joined['geometry_decimated'] = False

# Quintic ease-in-out: zero speed and zero acceleration at both ends, no overshoot.
# Bake per-frame values for a deterministic portable timeline.
tracks = [
    ('02 Battery', (0, -3, 22), 34, 81),
    ('03 Decorative carrier PCB', (0, 0, 51), 65, 116),
    ('04 Official Raspberry Pi CM4', (0, 4, 72), 98, 150),
    ('05 Thermal concept', (0, 8, 98), 130, 181),
    ('06 Cover', (0, 12, 129), 157, 211),
]
for name, offset, start, end in tracks:
    obj = bpy.data.objects[name+' | ANIMATE']; obj.animation_data_clear()
    obj['easing'] = 'quintic smootherstep: 6t^5 - 15t^4 + 10t^3'
    obj['motion_frames'] = [start, end]
    for frame in range(1, 241):
        obj.location = Vector(offset)*MM*(1-progress(frame, start, end))
        obj.keyframe_insert('location', frame=frame)
    linear_keys(obj)
product.animation_data_clear()
camera = scene.camera
camera.animation_data_clear(); camera.data.animation_data_clear()
for frame in range(1, 241):
    product.rotation_euler.z = math.radians(-9+9*progress(frame, 1, 150)+19*progress(frame, 158, 234))
    product.keyframe_insert('rotation_euler', frame=frame)
    # Zoom follows closure, so floating parts stay visible. End with a readable OLED hero.
    p = progress(frame, 162, 219)
    target = Vector((0, 0, .078)).lerp(Vector((0, 0, .016)), p)
    camera.location = Vector((.25, -.34, .26)).lerp(Vector((.215, -.31, .265)), p)
    look_at(camera, target)
    camera.data.ortho_scale = .38+(.182-.38)*p
    camera.keyframe_insert('location', frame=frame)
    camera.keyframe_insert('rotation_euler', frame=frame)
    camera.data.keyframe_insert('ortho_scale', frame=frame)
    pixel_fade.inputs[0].default_value = progress(frame, 211, 223)
    pixel_fade.inputs[0].keyframe_insert('default_value', frame=frame)
for owner in (product, camera, camera.data, pixels.node_tree): linear_keys(owner)
scene.timeline_markers.clear()
for frame, label in [(1, 'Exploded hold'), (34, 'Battery | ease in/out'), (65, 'Carrier | ease in/out'),
                     (98, 'CM4 | ease in/out'), (130, 'Thermal | ease in/out'), (157, 'Cover | ease in/out'),
                     (211, 'OLED wakes'), (234, 'Final hero hold')]:
    scene.timeline_markers.new(label, frame=frame)
scene['visual_revision'] = 'v02 | powerbank styling / OLED 87% / quintic easing'
scene['display_value'] = '87% is a demonstration state, not battery telemetry'
scene['display_engineering_status'] = 'Visual placeholder; part, electronics and thermal clearances unvalidated'

# Check conservative bounds for every moving group over all 240 output frames.
scene.frame_set(240); bpy.context.view_layer.update()
groups = [o for o in bpy.data.objects if o.name.endswith('| ANIMATE')]
local_boxes = {}
for group in groups:
    inverse = group.matrix_world.inverted()
    points = [inverse @ obj.matrix_world @ Vector(corner) for obj in group.children_recursive
              if obj.type in {'MESH', 'CURVE', 'FONT'} for corner in obj.bound_box]
    mins = [min(p[i] for p in points) for i in range(3)]
    maxs = [max(p[i] for p in points) for i in range(3)]
    local_boxes[group] = [Vector((x, y, z)) for x in [mins[0], maxs[0]]
                         for y in [mins[1], maxs[1]] for z in [mins[2], maxs[2]]]
rows = []
for frame in range(1, 241):
    scene.frame_set(frame); bpy.context.view_layer.update()
    points = [world_to_camera_view(scene, camera, group.matrix_world @ corner)
              for group, corners in local_boxes.items() for corner in corners]
    bounds = [min(p.x for p in points), min(p.y for p in points), max(p.x for p in points), max(p.y for p in points)]
    rows.append({'frame': frame, 'bounds': bounds,
                 'inside': bounds[0] >= .01 and bounds[1] >= .01 and bounds[2] <= .99 and bounds[3] <= .99})
failed = [r['frame'] for r in rows if not r['inside']]
validation = {'frames_checked': 240, 'failed_framing_frames': failed, 'frame_bounds': rows,
              'closed_groups_at_origin': all(g.location.length < 1e-7 for g in groups),
              'easing': 'quintic smootherstep with zero endpoint velocity and acceleration',
              'overshoot': False, 'display_demo_percent': 87, 'external_libraries': len(bpy.data.libraries)}
(OUT/'scene-validation-v02.json').write_text(json.dumps(validation, indent=2))
assert not failed, 'Camera framing failed: '+str(failed)
assert validation['closed_groups_at_origin']

scene.frame_set(240)
scene.render.resolution_x = 1920; scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100; scene.cycles.samples = 64
scene.render.filepath = str(OUT/'frames-v02'/'assembly_')
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'SafeWall-keynote-v02.blend'), compress=True)
manifest = {'revision': 'v02', 'source_scene': 'SafeWall-keynote-v01.blend',
            'editable_scene': 'SafeWall-keynote-v02.blend', 'envelope_mm': [70, 110, 24],
            'changes': ['rounded powerbank enclosure', 'recessed USB-C and status button',
                        'smoked OLED lens and animated 87% readout', 'quintic eased assembly and camera'],
            'OLED_window_mm': [28.35, 16.35], 'OLED_value_is_demo': True,
            'engineering_status': 'visual concept; no display part selection or revised Fusion production geometry',
            'fps': 24, 'frames': 240, 'source_resolution': [1920, 1080]}
(OUT/'scene-manifest-v02.json').write_text(json.dumps(manifest, indent=2))
print('V02_SCENE_READY', json.dumps({k:v for k,v in validation.items() if k != 'frame_bounds'}), flush=True)

prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'; prefs.get_devices()
for device in prefs.devices: device.use = device.type == 'METAL'
scene.cycles.device = 'GPU' if any(d.type == 'METAL' for d in prefs.devices) else 'CPU'
scene.cycles.samples = 32; scene.render.resolution_x = 1440; scene.render.resolution_y = 810
for frame, filename in [(240, 'assembled-preview-v02.png'), (1, 'exploded-preview-v02.png')]:
    scene.frame_set(frame); scene.render.filepath = str(OUT/filename)
    bpy.ops.render.render(write_still=True)
print('V02_PREVIEWS_READY', flush=True)
