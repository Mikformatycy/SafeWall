"""Check animation endpoints, framing, and embedded assets in the saved scene."""
import json
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parents[1]
scene=bpy.context.scene
parts=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('01 ','02 ','03 ','04 ','Shell perimeter','06 ','07 ','09 ','11 ','12 '))]
rows=[]
for frame in range(1,241):
    scene.frame_set(frame);bpy.context.view_layer.update()
    points=[world_to_camera_view(scene,scene.camera,o.matrix_world@Vector(c)) for o in parts for c in o.bound_box]
    box=[min(p.x for p in points),min(p.y for p in points),max(p.x for p in points),max(p.y for p in points)]
    rows.append({'frame':frame,'normalized_frame_bounds':box,'inside_frame':box[0]>=0.01 and box[1]>=0.01 and box[2]<=0.99 and box[3]<=0.99})
scene.frame_set(240)
groups=[o for o in bpy.data.objects if o.name.endswith('| ANIMATE')]
closed=all(o.location.length<1e-7 for o in groups)
result={'framing':rows,'closed_groups_at_origin':closed,'fps':scene.render.fps,'frame_count':scene.frame_end-scene.frame_start+1,
        'external_libraries':len(bpy.data.libraries),'external_images':[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file],
        'objects':len(bpy.data.objects),'camera_animated':bool(scene.camera.animation_data)}
(ROOT/'visualization'/'scene-validation.json').write_text(json.dumps(result,indent=2))
print('SCENE_CHECK',json.dumps({'closed_groups_at_origin':closed,'failed_frames':[r['frame'] for r in rows if not r['inside_frame']],
                             'fps':scene.render.fps,'frames_checked':len(rows),'external_libraries':len(bpy.data.libraries)}),flush=True)
