"""Re-render the existing 3D phone shot with only AirDrop in its context label."""
import json
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[1];V=ROOT/'visualization';OUT=V/'launch-preview-v22'
OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(V/'launch-preview-v21/radios-v21.blend'))
o=bpy.data.objects['v21 | AirDrop discovery context']
assert o.data.body=='AirDrop · Wszyscy'
o.data.body='AirDrop'
scene=bpy.context.scene;scene['visual_revision']='v22 | AirDrop label only'
scene['visible_discovery_context']='AirDrop'
scene['discovery_context_note']='Everyone qualifier removed at user request; repeated names remain an illustrative nearby discovery effect.'
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'radios-v22.blend'),compress=True)
frames=OUT/'radios-frames';frames.mkdir(exist_ok=True)
for f in range(1,235):
    scene.frame_set(f);scene.render.filepath=str(frames/f'{f:04d}.png')
    bpy.ops.render.render(write_still=True)
    if f%48==0:print('V22_RADIO_RENDER',f,234,flush=True)
(OUT/'radios-checks.json').write_text(json.dumps({'frames':234,'engine':scene.render.engine,'visible_label':o.data.body,'emitted_name_instances':23},indent=2)+'\n')
print('V22_RADIOS_READY',flush=True)
