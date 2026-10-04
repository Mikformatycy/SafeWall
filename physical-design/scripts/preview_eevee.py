"""Compare the fast animation renderer with the Cycles review stills."""
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[1]
s=bpy.context.scene
s.render.engine='CYCLES'
s.render.engine='BLENDER_EEVEE_NEXT'
s.eevee.taa_render_samples=32
s.eevee.use_raytracing=True
s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100
s.render.use_persistent_data=True
for f in [1,120,240]:
    s.frame_set(f)
    s.render.filepath=str(ROOT/'visualization'/f'eevee-check-{f:03}.png')
    bpy.ops.render.render(write_still=True)
print('EEVEE_COMPARISON_READY',flush=True)
