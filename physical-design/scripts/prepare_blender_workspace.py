"""Open the editable asset on its product camera, with a clean material preview."""
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[1]
scene=bpy.context.scene
scene.frame_set(1)
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
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'visualization'/'SafeWall-keynote-v01.blend'),compress=True)
print('Product camera workspace saved',flush=True)
