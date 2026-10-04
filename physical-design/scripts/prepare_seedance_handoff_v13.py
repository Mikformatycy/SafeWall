"""Make a low-cost composition reference from the existing closed product.

Run with Blender's Product-keynote-v04.blend loaded. Saves a separate file;
the premium master is not changed. This is a framing reference, not a final
photorealistic station shot.
"""
from pathlib import Path
import json
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

root = Path(__file__).resolve().parents[1]
out = root / 'visualization' / 'seedance-byteplus-v13'
out.mkdir(exist_ok=True)
scene = bpy.context.scene
scene.frame_set(120)
for obj in bpy.data.objects:
    if obj.animation_data:
        obj.animation_data_clear()
    if obj.data and obj.data.animation_data:
        obj.data.animation_data_clear()
product = bpy.data.objects['SafeWall | product rotation']
product.rotation_euler.z = 0
camera = scene.camera
target = Vector((0, 0, .012))
camera.location = (0, -.22, .40)
camera.rotation_euler = (target-camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = .28
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 960
scene.render.resolution_y = 540
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.film_transparent = False
scene.use_nodes = False
scene.display.render_aa = '16'
sh = scene.display.shading
sh.light = 'STUDIO'
sh.studio_light = 'paint.sl'
sh.color_type = 'MATERIAL'
sh.show_shadows = True
sh.show_cavity = True
sh.cavity_type = 'BOTH'
sh.show_specular_highlight = False
sh.background_type = 'WORLD'
scene.world.color = (.12, .135, .15)
floor = bpy.data.objects.get('Seamless studio floor')
if floor:
    floor.hide_render = False
    floor.is_shadow_catcher = False
    for mat in floor.data.materials:
        mat.diffuse_color = (.12, .135, .15, 1)
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = 0
scene.frame_start = scene.frame_end = 120
scene['visual_revision'] = 'v13 | Seedance handoff composition reference only'
scene['purpose'] = 'Final centered device pose; appearance comes from premium product reference'
bpy.context.view_layer.update()
points = [world_to_camera_view(scene, camera, obj.matrix_world @ Vector(c))
          for obj in product.children_recursive
          if obj.type in {'MESH', 'CURVE', 'FONT'} and not obj.hide_render
          for c in obj.bound_box]
bounds = [min(p.x for p in points), min(p.y for p in points),
          max(p.x for p in points), max(p.y for p in points)]
assert min(bounds[:2]) > .03 and max(bounds[2:]) < .97, bounds
scene.render.filepath = str(out / '02-handoff-composition.png')
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'Handoff-composition-v13.blend'), compress=True)
bpy.ops.render.render(write_still=True)
(out / 'handoff-camera.json').write_text(json.dumps({
    'resolution': [960, 540], 'device_bounds_normalized': bounds,
    'camera_location': list(camera.location), 'camera_rotation': list(camera.rotation_euler),
    'ortho_scale': camera.data.ortho_scale, 'product_rotation': list(product.rotation_euler),
    'role': 'composition reference, not an exact last-frame constraint',
    'source_scene_unchanged': 'Product-keynote-v04.blend',
    'render_engine': scene.render.engine
}, indent=2))
print('HANDOFF_REFERENCE_READY', flush=True)
