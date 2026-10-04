"""Inspect the two official Apple USDZ phone instances and save a local reference."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'references'/'iphone'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.usd_import(filepath=str(OUT/'iphone-18-pro-e-sim.usdz'),
    import_materials=False, import_textures_mode='IMPORT_NONE', import_lights=False,
    import_cameras=False, import_skeletons=False, import_blendshapes=False,
    import_visible_only=False, set_frame_range=False, apply_unit_conversion_scale=True,
    create_collection=True)
bpy.context.view_layer.update()

def bounds(objects):
    points=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
    return [[min(v[i] for v in points) for i in range(3)],
            [max(v[i] for v in points) for i in range(3)]]

rows=[]
for name in ('UBGArkKGrAMRRnj','wUOhcMgiBmCgGaw'):
    obj=bpy.data.objects.get(name)
    if obj:
        meshes=[o for o in obj.children_recursive if o.type=='MESH']
        b=bounds(meshes)
        rows.append({'root':name,'mesh_count':len(meshes),'bounds':b,
                     'extent_mm':[(b[1][i]-b[0][i])*1000 for i in range(3)],
                     'root_transform':[list(row) for row in obj.matrix_world]})
report={'objects':len(bpy.data.objects),'phones':rows,
        'root_objects':[(o.name,o.type) for o in bpy.data.objects if not o.parent]}
(OUT/'import-inspection.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'apple-iphone-reference.blend'),compress=True)
print('IPHONE_IMPORT',json.dumps(report),flush=True)
