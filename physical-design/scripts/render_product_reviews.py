"""Finish the white studio backdrop, save the scene, and render review views."""
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'visualization'
scene=bpy.context.scene
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='METAL';prefs.get_devices()
for device in prefs.devices:device.use=(device.type=='METAL')
scene.cycles.device='GPU' if any(d.type=='METAL' for d in prefs.devices) else 'CPU'
bpy.data.objects['Seamless studio floor'].is_shadow_catcher=True
scene.render.film_transparent=True
scene.use_nodes=True
nodes=scene.node_tree.nodes;nodes.clear()
layer=nodes.new('CompositorNodeRLayers')
over=nodes.new('CompositorNodeAlphaOver');over.inputs[1].default_value=(4,4,4,1)
output=nodes.new('CompositorNodeComposite')
scene.node_tree.links.new(layer.outputs['Image'],over.inputs[2])
scene.node_tree.links.new(over.outputs['Image'],output.inputs['Image'])
scene.render.use_persistent_data=True
scene.frame_set(1);scene.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'SafeWall-keynote-v01.blend'),compress=True)
scene.render.resolution_percentage=75;scene.cycles.samples=32
for frame,name in [(1,'exploded-preview.png'),(240,'assembled-preview.png')]:
    scene.frame_set(frame);scene.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True)
scene.frame_set(1)
for collection in bpy.data.collections:
    if collection.name.startswith(('01 ','02 ','03 ','05 ','06 ')):collection.hide_render=True
camera=scene.camera
camera.animation_data_clear();camera.data.animation_data_clear()
camera.location=(.050,-.040,.205)
camera.rotation_euler=(Vector((0,.020,.091))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.ortho_scale=.084
scene.render.filepath=str(OUT/'cm4-detail.png');bpy.ops.render.render(write_still=True)
print('PRODUCT_REVIEWS_READY',flush=True)
