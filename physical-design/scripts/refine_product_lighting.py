"""Calibrate lights at actual product scale and export review stills."""
import json
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'visualization'
scene=bpy.context.scene
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='METAL';prefs.get_devices()
for device in prefs.devices:device.use=(device.type=='METAL')
scene.cycles.device='GPU' if any(d.type=='METAL' for d in prefs.devices) else 'CPU'
for name,power in [('Key | broad silk',1.225),('Rim | tall strip',1.575),('Fill | front card',.28),('Top | diffuse',.525)]:
    bpy.data.lights[name].energy=power
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.18
scene.frame_set(1)
scene.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'SafeWall-keynote-v01.blend'),compress=True)
scene.render.resolution_percentage=65;scene.cycles.samples=32
for frame,name in [(1,'exploded-preview.png'),(240,'assembled-preview.png')]:
    scene.frame_set(frame);scene.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True)
print('REFINED_PREVIEWS_READY',flush=True)
