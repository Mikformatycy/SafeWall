"""Keep the open cover in frame until it begins descending."""
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
scene=bpy.context.scene;camera=scene.camera
camera.animation_data_clear();camera.data.animation_data_clear()
poses=[(1,(0,0,.078),(.25,-.34,.26),.38),
       (160,(0,0,.078),(.25,-.34,.26),.38),
       (185,(0,0,.045),(.24,-.33,.255),.29),
       (210,(0,0,.017),(.23,-.32,.25),.19),
       (240,(0,0,.016),(.21,-.31,.24),.18)]
for frame,target,position,scale in poses:
    scene.frame_set(frame);camera.location=position
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=scale
    camera.keyframe_insert('location',frame=frame);camera.keyframe_insert('rotation_euler',frame=frame)
    camera.data.keyframe_insert('ortho_scale',frame=frame)
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'visualization'/'SafeWall-keynote-v01.blend'),compress=True)
exec((ROOT/'scripts'/'check_product_scene.py').read_text())
