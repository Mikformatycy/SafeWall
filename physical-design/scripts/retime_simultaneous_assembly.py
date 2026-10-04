"""Derive a five-second v03 from v02, preserving geometry/materials and end poses.

All five layers share one progress curve and start/end frames. The asymmetric
curve gives a soft launch followed by a long deceleration into the enclosure.
"""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

OUT = Path(__file__).resolve().parents[1]/'visualization'
scene = bpy.context.scene
assert scene['visual_revision'].startswith('v02')
START, END, LAST = 9, 94, 120
TRACKS = [
    ('02 Battery', (0, -3, 22)),
    ('03 Decorative carrier PCB', (0, 0, 51)),
    ('04 Official Raspberry Pi CM4', (0, 4, 72)),
    ('05 Thermal concept', (0, 8, 98)),
    ('06 Cover', (0, 12, 129)),
]


def ease(t):
    """Beta(3,6) CDF; derivative 168*t^2*(1-t)^5, no overshoot."""
    t = min(1.0, max(0.0, t))
    return min(1.0, max(0.0, t**3*(56+t*(-210+t*(336+t*(-280+t*(120-21*t)))))))


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t*t*t*(t*(6*t-15)+10)


def linear_keys(owner):
    action = owner.animation_data.action
    curves = list(action.fcurves) if action.is_action_legacy else [
        fc for layer in action.layers for strip in layer.strips
        for bag in strip.channelbags for fc in bag.fcurves]
    for curve in curves:
        for key in curve.keyframe_points: key.interpolation = 'LINEAR'


animated = [bpy.data.objects[name+' | ANIMATE'] for name, _ in TRACKS]
product = bpy.data.objects['SafeWall | product rotation']
camera = scene.camera
pixels = bpy.data.materials['OLED | cool white emissive pixels'].node_tree
fade = pixels.nodes.get('Mix Shader').inputs[0]
owners = animated+[product, camera, camera.data, pixels]
for owner in owners: owner.animation_data_clear()
for obj in animated:
    obj['motion_frames'] = [START, END]
    obj['easing'] = 'Shared Beta(3,6) easing; soft launch and long ease-out'

scene.frame_start = 1; scene.frame_end = LAST
scene.render.fps = 24; scene.render.fps_base = 1
for frame in range(1, LAST+1):
    p = ease((frame-START)/(END-START))
    for obj, (_, offset) in zip(animated, TRACKS):
        obj.location = Vector(offset)*.001*(1-p)
        obj.keyframe_insert('location', frame=frame)
    product.rotation_euler.z = math.radians(-9+28*p)
    product.keyframe_insert('rotation_euler', frame=frame)
    target = Vector((0, 0, .078)).lerp(Vector((0, 0, .016)), p)
    camera.location = Vector((.25, -.34, .26)).lerp(Vector((.215, -.31, .265)), p)
    camera.rotation_euler = (target-camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.ortho_scale = .38+(.182-.38)*p
    camera.keyframe_insert('location', frame=frame)
    camera.keyframe_insert('rotation_euler', frame=frame)
    camera.data.keyframe_insert('ortho_scale', frame=frame)
    fade.default_value = smooth((frame-END)/10)
    fade.keyframe_insert('default_value', frame=frame)
for owner in owners: linear_keys(owner)
scene.timeline_markers.clear()
for frame, label in [(1, 'Exploded hold'), (START, 'All layers move together'),
                     (51, 'Long soft settling'), (END, 'All layers seated / OLED wakes'),
                     (104, 'Final hero hold')]:
    scene.timeline_markers.new(label, frame=frame)
scene['visual_revision'] = 'v03 | simultaneous assembly / stronger ease-out / five seconds'
scene['assembly_progress'] = 'One shared Beta(3,6) curve for all five moving layers'
scene['assembly_start_frame'] = START; scene['assembly_end_frame'] = END
scene['display_wake_frames'] = [END, 104]

# Conservative group bounds include every detail, even the display and connector.
scene.frame_set(LAST); bpy.context.view_layer.update()
groups = [o for o in bpy.data.objects if o.name.endswith('| ANIMATE')]
local_boxes = {}
for group in groups:
    inverse = group.matrix_world.inverted()
    points = [inverse @ obj.matrix_world @ Vector(c) for obj in group.children_recursive
              if obj.type in {'MESH', 'CURVE', 'FONT'} for c in obj.bound_box]
    lower = [min(p[i] for p in points) for i in range(3)]
    upper = [max(p[i] for p in points) for i in range(3)]
    local_boxes[group] = [Vector((x, y, z)) for x in [lower[0], upper[0]]
                         for y in [lower[1], upper[1]] for z in [lower[2], upper[2]]]
rows, samples, display = [], {obj.name: [] for obj in animated}, []
for frame in range(1, LAST+1):
    scene.frame_set(frame); bpy.context.view_layer.update()
    points = [world_to_camera_view(scene, camera, group.matrix_world @ corner)
              for group, corners in local_boxes.items() for corner in corners]
    bounds = [min(p.x for p in points), min(p.y for p in points), max(p.x for p in points), max(p.y for p in points)]
    rows.append({'frame': frame, 'bounds': bounds,
                 'inside': bounds[0] >= .01 and bounds[1] >= .01 and bounds[2] <= .99 and bounds[3] <= .99})
    for obj in animated: samples[obj.name].append(obj.location.copy())
    display.append(fade.default_value)
failed = [r['frame'] for r in rows if not r['inside']]
motion = {}
fractions = []
for obj in animated:
    track = samples[obj.name]; initial = track[0].length
    remaining = [v.length/initial for v in track]; fractions.append(remaining)
    speeds = [(track[i+1]-track[i]).length for i in range(START-1, END-1)]
    assert all(-1e-7 <= x <= 1+1e-7 for x in remaining)
    assert all(b <= a+1e-7 for a, b in zip(remaining, remaining[1:]))
    assert all((v-track[0]).length < 1e-7 for v in track[:START])
    assert all(v.length < 1e-7 for v in track[END-1:])
    assert speeds[0] < max(speeds)*.02 and speeds[-1] < max(speeds)*.002
    motion[obj.name] = {'motion_frames': [START, END], 'monotonic': True,
                        'first_speed_fraction_of_peak': speeds[0]/max(speeds),
                        'last_speed_fraction_of_peak': speeds[-1]/max(speeds)}
sync_error = max(max(values)-min(values) for values in zip(*fractions))
assert sync_error < 1e-6
assert all(v == 0 for v in display[:END]) and all(v == 1 for v in display[103:])
assert not failed, 'Camera framing failed: '+str(failed)
assert all(g.location.length < 1e-7 for g in groups)
validation = {'frames_checked': LAST, 'fps': 24, 'duration_seconds': 5,
              'failed_framing_frames': failed, 'frame_bounds': rows, 'closed_groups_at_origin': True,
              'simultaneous_motion': True, 'normalized_sync_error': sync_error,
              'shared_motion_frames': [START, END], 'easing': 'Beta(3,6) CDF',
              'progress_at_half_motion_time': ease(.5), 'motion': motion,
              'OLED_off_until_seated': True}
(OUT/'scene-validation-v03.json').write_text(json.dumps(validation, indent=2))
scene.frame_set(LAST)
scene.cycles.denoising_use_gpu = True
scene.render.filepath = str(OUT/'frames-v03'/'assembly_')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'SafeWall-keynote-v03.blend'), compress=True)
manifest = json.loads((OUT/'scene-manifest-v02.json').read_text())
manifest.update({'revision': 'v03', 'source_scene': 'SafeWall-keynote-v02.blend',
                 'editable_scene': 'SafeWall-keynote-v03.blend', 'frames': LAST, 'duration_seconds': 5,
                 'changes': ['all five layers close simultaneously', 'strong asymmetric ease-out',
                             'five-second runtime', 'OLED wakes after shared assembly endpoint'],
                 'shared_motion_frames': [START, END], 'easing': 'Beta(3,6) CDF',
                 'stills_unchanged_from': 'v02; identical geometry, materials and endpoint poses'})
(OUT/'scene-manifest-v03.json').write_text(json.dumps(manifest, indent=2))
print('V03_SCENE_READY', json.dumps({k:v for k,v in validation.items() if k not in {'frame_bounds','motion'}}), flush=True)
