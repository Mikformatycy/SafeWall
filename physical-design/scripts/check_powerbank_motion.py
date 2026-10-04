"""Verify the saved motion, display fade, and closed shell surfaces without rendering."""
import json
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parents[1]/'visualization'
scene = bpy.context.scene
objects = [o for o in bpy.data.objects if o.get('easing')]
positions = {o.name: [] for o in objects}
display = bpy.data.materials['OLED | cool white emissive pixels'].node_tree.nodes.get('Mix Shader')
display_values = []
for frame in range(1, 241):
    scene.frame_set(frame)
    for obj in objects: positions[obj.name].append(obj.location.copy())
    display_values.append(display.inputs[0].default_value)
motion = {}
for obj in objects:
    samples = positions[obj.name]
    initial = samples[0].length
    remaining = [p.length/initial for p in samples]
    start, end = obj['motion_frames']
    speeds = [(samples[i+1]-samples[i]).length for i in range(start-1, end-1)]
    assert all(-1e-7 <= p <= 1+1e-7 for p in remaining)
    assert all(b <= a+1e-7 for a, b in zip(remaining, remaining[1:]))
    assert all((p-samples[0]).length < 1e-7 for p in samples[:start])
    assert all(p.length < 1e-7 for p in samples[end-1:])
    assert speeds[0] < max(speeds)*.02 and speeds[-1] < max(speeds)*.02
    motion[obj.name] = {'start': start, 'end': end, 'monotonic_without_overshoot': True,
                        'start_speed_fraction_of_peak': speeds[0]/max(speeds),
                        'stop_speed_fraction_of_peak': speeds[-1]/max(speeds)}
assert all(v == 0 for v in display_values[:211])
assert all(abs(v-1) < 1e-6 for v in display_values[222:])
assert all(b >= a for a, b in zip(display_values, display_values[1:]))
topology = {}
for name in ['02 Rear panel | soft lower edge', 'Shell perimeter | powerbank profile',
             '12 Lid | rolled powerbank cover', 'OLED | flush black glass']:
    bm = bmesh.new(); bm.from_mesh(bpy.data.objects[name].data)
    bad_edges = sum(not e.is_manifold for e in bm.edges)
    topology[name] = {'non_manifold_edges': bad_edges}
    bm.free()
    assert bad_edges == 0, name
external_images = [i.filepath for i in bpy.data.images if i.source == 'FILE' and not i.packed_file]
assert not external_images and not bpy.data.libraries
report = {'saved_scene': Path(bpy.data.filepath).name, 'checked_frames': 240,
          'motion': motion, 'OLED_off_until_cover_seated': True, 'OLED_fade_monotonic': True,
          'shell_meshes': topology, 'external_images': external_images, 'external_libraries': 0}
(OUT/'motion-validation-v02.json').write_text(json.dumps(report, indent=2))
print('MOTION_CHECK_PASSED', json.dumps(report), flush=True)
