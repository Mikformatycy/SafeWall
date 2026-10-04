"""Neutral, unbranded v04 product visualization with a gloss finish and upper OLED.

Run against the v03 scene. The existing five-second simultaneous motion is kept.
These are visualization materials and layout proposals, not production approvals.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_product_scene import rgba, look_at, softbox

OUT = Path(__file__).resolve().parents[1]/'visualization'
scene = bpy.context.scene
assert scene['visual_revision'].startswith('v03')
scene.frame_set(120)

# Remove visible project branding, including branding on the exposed assembly.
removed = []
for obj in list(bpy.data.objects):
    if obj.name == 'Cover wordmark' or (obj.type == 'FONT' and 'safewall' in obj.data.body.lower()):
        removed.append(obj.name)
        bpy.data.objects.remove(obj, do_unlink=True)
    elif obj.type == 'FONT' and obj.data.body.startswith('SW\n'):
        obj.data.body = obj.data.body.replace('SW\n', '')

# The perimeter is rotationally symmetric: rotating just the cover relocates its
# existing OLED aperture to the upper end without leaving a second opening.
cover = bpy.data.objects['12 Lid | rolled powerbank cover']
cover.rotation_euler.z += math.pi
display_parts = [o for o in bpy.data.objects if o.name.startswith('OLED |')]
for obj in display_parts:
    obj.location.y += .058
assert abs(bpy.data.objects['OLED | flush black glass'].location.y-.029) < 1e-7


def glossy(mat, color, roughness, coat_roughness):
    shader = mat.node_tree.nodes.get('Principled BSDF')
    mat.diffuse_color = rgba(color)
    for name in ('Normal', 'Coat Normal'):
        for link in list(shader.inputs[name].links): mat.node_tree.links.remove(link)
    shader.inputs['Base Color'].default_value = rgba(color)
    shader.inputs['Metallic'].default_value = 0
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['IOR'].default_value = 1.5
    shader.inputs['Coat Weight'].default_value = 1.0
    shader.inputs['Coat Roughness'].default_value = coat_roughness
    shader.inputs['Coat IOR'].default_value = 1.52


body = bpy.data.materials['CMF | graphite PC-ABS satin']
body.name = 'CMF | graphite polymer with polished clearcoat'
glossy(body, '#14171B', .20, .13)
top = body.copy(); top.name = 'CMF | piano black gloss cover'
glossy(top, '#080A0D', .12, .07)
cover.data.materials.clear(); cover.data.materials.append(top)
glass = bpy.data.materials['OLED | smoked polished glass']
glossy(glass, '#05070A', .065, .045)
glass_shader = glass.node_tree.nodes.get('Principled BSDF')
glass_shader.inputs['IOR'].default_value = 1.48
glass_shader.inputs['Specular IOR Level'].default_value = .25
glass_shader.inputs['Coat Weight'].default_value = .2
for name, roughness in [('Metal | satin nickel shield', .20), ('Metal | ENIG gold pads', .21),
                        ('Metal | solder fillets', .19), ('Thermal | brushed copper', .24)]:
    bpy.data.materials[name].node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value = roughness

# Long narrow softboxes provide shaped reflections on the coated shell.
lighting = [
    ('Key | broad silk', (-.18, -.12, .32), (0, 0, .04), .75, .26, .20),
    ('Rim | tall strip', (.17, .10, .20), (0, 0, .055), 1.15, .045, .30),
    ('Fill | front card', (.10, -.24, .12), (0, 0, .045), .20, .20, .24),
    ('Top | diffuse', (-.201, .249, .23), (0, 0, .025), .16, .018, .16),
]
for name, position, target, power, width, height in lighting:
    obj = bpy.data.objects[name]; obj.location = position; look_at(obj, target)
    obj.data.energy = power; obj.data.shape = 'RECTANGLE'
    obj.data.size = width; obj.data.size_y = height
# Parallel to the top surface: a narrow reflection down its left side, clear of OLED.
bpy.data.objects['Top | diffuse'].rotation_euler = (0, 0, math.radians(19))
softbox('Premium | front edge reflection', (-.12, -.18, .08), (0, 0, .015), .12, .025, .20)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .08
looks = scene.view_settings.bl_rna.properties['look'].enum_items
for look in looks:
    if 'Medium High Contrast' in look.identifier:
        scene.view_settings.look = look.identifier
        break
scene.view_settings.exposure = 0
scene.cycles.samples = 64
scene.cycles.use_denoising = True; scene.cycles.denoising_use_gpu = True
scene.render.use_persistent_data = True
scene.render.resolution_x = 1920; scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene['visual_revision'] = 'v04 | unbranded piano black / upper OLED / premium studio'
scene['render_stem'] = 'Product'
scene['review_width'] = 1920; scene['review_height'] = 1080; scene['review_samples'] = 24
scene['CMF_status'] = 'Gloss coating and OLED lens are appearance proposals; material grades not selected'
scene['brand_text_removed'] = True
scene['OLED_location'] = 'upper area of cover; lens center at local y=29 mm'

# Recheck every frame after moving the lid aperture and display geometry.
scene.frame_set(120); bpy.context.view_layer.update()
groups = [o for o in bpy.data.objects if o.name.endswith('| ANIMATE')]
local_boxes = {}
for group in groups:
    inverse = group.matrix_world.inverted()
    points = [inverse @ obj.matrix_world @ Vector(c) for obj in group.children_recursive
              if obj.type in {'MESH', 'CURVE', 'FONT'} for c in obj.bound_box]
    lower = [min(p[i] for p in points) for i in range(3)]
    upper = [max(p[i] for p in points) for i in range(3)]
    local_boxes[group] = [Vector((x, y, z)) for x in [lower[0], upper[0]]
                         for y in [lower[1], upper[1]] for z in [lower[2], upper[2]]]
rows = []
for frame in range(1, 121):
    scene.frame_set(frame); bpy.context.view_layer.update()
    points = [world_to_camera_view(scene, scene.camera, group.matrix_world @ corner)
              for group, corners in local_boxes.items() for corner in corners]
    bounds = [min(p.x for p in points), min(p.y for p in points), max(p.x for p in points), max(p.y for p in points)]
    rows.append({'frame': frame, 'bounds': bounds,
                 'inside': bounds[0] >= .01 and bounds[1] >= .01 and bounds[2] <= .99 and bounds[3] <= .99})
failed = [r['frame'] for r in rows if not r['inside']]
text_matches = [o.name for o in bpy.data.objects if o.type == 'FONT' and 'safewall' in o.data.body.lower()]
assert not failed and not text_matches and 'Cover wordmark' not in bpy.data.objects
assert all(g.location.length < 1e-7 for g in groups)
validation = json.loads((OUT/'scene-validation-v03.json').read_text())
validation.update({'frame_bounds': rows, 'failed_framing_frames': failed,
                   'remaining_project_brand_text_objects': text_matches, 'removed_brand_objects': removed,
                   'OLED_lens_center_y_mm': 29, 'geometry_revision': 'v04'})
(OUT/'scene-validation-v04.json').write_text(json.dumps(validation, indent=2))
scene.frame_set(120)
scene.render.filepath = str(OUT/'frames-v04'/'assembly_')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Product-keynote-v04.blend'), compress=True)
manifest = json.loads((OUT/'scene-manifest-v03.json').read_text())
manifest.pop('stills_unchanged_from', None)
manifest.update({'revision': 'v04', 'source_scene': 'SafeWall-keynote-v03.blend',
                 'editable_scene': 'Product-keynote-v04.blend', 'render_stem': 'Product',
                 'changes': ['remove visible project branding', 'OLED in upper cover',
                             'piano black and polished graphite materials', 'studio reflection lighting'],
                 'review_resolution': [1920, 1080], 'review_samples': 24,
                 'removed_brand_objects': removed, 'OLED_center_y_mm': 29})
(OUT/'scene-manifest-v04.json').write_text(json.dumps(manifest, indent=2))
print('V04_SCENE_READY', json.dumps({'removed_brand_objects': removed, 'framing_failures': failed}), flush=True)

prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'; prefs.get_devices()
for device in prefs.devices: device.use = device.type == 'METAL'
scene.cycles.device = 'GPU' if any(d.type == 'METAL' for d in prefs.devices) else 'CPU'
scene.cycles.samples = 64
for frame, name in [(120, 'assembled-preview-v04.png'), (1, 'exploded-preview-v04.png')]:
    scene.frame_set(frame); scene.render.filepath = str(OUT/name)
    bpy.ops.render.render(write_still=True)
print('V04_PREVIEWS_READY', flush=True)
