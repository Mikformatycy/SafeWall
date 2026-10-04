"""Render a 540p review movie from the saved, editable 1080p Cycles scene."""
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'visualization'
scene=bpy.context.scene
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='METAL';prefs.get_devices()
for device in prefs.devices:device.use=(device.type=='METAL')
scene.cycles.device='GPU' if any(d.type=='METAL' for d in prefs.devices) else 'CPU'
print('RENDER_DEVICE',scene.cycles.device,flush=True)
scene.render.engine='CYCLES'
scene.cycles.samples=8
scene.cycles.use_denoising=True
scene.render.use_persistent_data=True
scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGB'
scene.render.filepath=str(OUT/'frames'/'assembly_')
scene.frame_start=1;scene.frame_end=240
bpy.ops.render.render(animation=True)
print('ASSEMBLY_FRAMES_READY',flush=True)
