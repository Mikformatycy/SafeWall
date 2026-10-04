"""Save the finished image-sequence edit as an editable Blender VSE project."""
import json
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[1]
V=ROOT/'visualization';OUT=V/'launch-preview-v21'
edit=json.loads((OUT/'edit-timeline.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.name='SafeWall launch v21 | editable cut'
scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100
scene.render.fps=24;scene.render.fps_base=1;scene.frame_start=1;scene.frame_end=edit['frames']
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
editor=scene.sequence_editor_create()
for index,c in enumerate(edit['clips']):
    folder=V/('launch-preview-'+c['source'])/(c['name']+'-frames')
    start=round(c['start']*24)+1
    strip=editor.strips.new_image(c['name'],str(folder/'0001.png'),channel=index+1,frame_start=start)
    for n in range(2,c['frames']+1):strip.elements.append(f'{n:04d}.png')
    strip.frame_final_duration=c['frames'];strip.blend_type='ALPHA_OVER'
    if index:
        prev=edit['clips'][index-1]
        overlap=round((prev['end']-c['start'])*24)
        if overlap>0:
            for k in range(overlap+1):
                u=k/overlap;strip.blend_alpha=u*u*u*(10+u*(-15+6*u))
                strip.keyframe_insert('blend_alpha',frame=start+k)
    scene.timeline_markers.new(c['name'],frame=start)
editor.strips.new_sound('Daniel + original ambience + SFX',str(OUT/'final-mix.wav'),channel=10,frame_start=1)
scene.render.image_settings.file_format='FFMPEG'
scene.render.ffmpeg.format='MPEG4';scene.render.ffmpeg.codec='H264';scene.render.ffmpeg.audio_codec='AAC'
scene.render.filepath=str(OUT/'SafeWall-v21-export-from-Blender.mp4')
scene['canonical_voiceover']='../VOICEOVER-APPROVED-v20.txt'
scene['native_scene_files']='tor-v21.blend; radios-v21.blend; ../launch-preview-v20/docking-v20.blend'
scene['source_scene_files']='../launch-preview-v18/assembly-v18.blend; ../launch-preview-v18/prototype-v18.blend'
scene['note']='Image sequences reference project folders. Re-render a source 3D scene to update the corresponding shot. No flat explanatory slides; ending uses the existing marketing/outro MP4 as requested.'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.type='SEQUENCE_EDITOR'
            for space in area.spaces:
                if space.type=='SEQUENCE_EDITOR':space.view_type='SEQUENCER_PREVIEW'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'SafeWall-edit-v21.blend'),compress=True)
print('V21_BLENDER_EDIT_READY',len(editor.strips),'strips',scene.frame_end,'frames')
