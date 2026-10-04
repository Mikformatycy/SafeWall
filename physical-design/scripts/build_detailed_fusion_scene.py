"""A separate visualization document with official CM4 geometry."""
import json
import math
import sys
from pathlib import Path
import adsk.core
import adsk.fusion

ROOT=Path('/Users/piotrek/Desktop/RaspberryPi-Hackathon/physical-design')


def run(_context: str):
    app=adsk.core.Application.get()
    manager=app.importManager
    doc=manager.importToNewDocument(manager.createFusionArchiveImportOptions(str(ROOT/'exports'/'SafeWall-B-concept-v01.f3d')))
    doc.name='SafeWall B - detailed visualization v02'
    design=adsk.fusion.Design.cast(app.activeProduct)
    root=design.rootComponent
    root.attributes.add('SafeWall','visual_only','Detailed CM4 reference. Decorative carrier visualization is authored in Blender; electrical PCB design is unresolved.')
    for occurrence in root.occurrences:
        occurrence.isLightBulbOn=not occurrence.component.name.startswith(('08 ','10 ','11 ','12 '))
    sys.path.insert(0,str(ROOT/'scripts'))
    from build_layout_study import component,block
    holder=component(root,'Official CM4 - Raspberry Pi STEP reference',7.5,36,16.9)
    if not manager.importToTarget(manager.createSTEPImportOptions(str(ROOT/'references'/'cm4-official'/'CM4.step')),holder.component):
        raise RuntimeError('Detailed CM4 import failed')
    print('Detailed CM4 imported. Run finish_detailed_fusion_scene.py after Fusion processes the document update.')


def finish(_context: str):
    app=adsk.core.Application.get()
    doc=app.activeDocument
    design=adsk.fusion.Design.cast(app.activeProduct)
    root=design.rootComponent
    if doc.name!='SafeWall B - detailed visualization v02':raise RuntimeError('Unexpected active document')
    sys.path.insert(0,str(ROOT/'scripts'))
    from build_layout_study import component,block
    holder=next(o for o in root.occurrences if o.component.name.startswith('Official CM4'))
    design.computeAll()
    boxes=[b.boundingBox for child in holder.childOccurrences for b in child.bRepBodies]
    report={'CM4_bounds_mm':[[round(min(b.minPoint.asArray()[i] for b in boxes)*10,4) for i in range(3)],
                             [round(max(b.maxPoint.asArray()[i] for b in boxes)*10,4) for i in range(3)]]}
    if any(abs(a-b)>0.01 for row,expected in zip(report['CM4_bounds_mm'],[[7.5,52,15.7654],[62.5,92,20.54966]]) for a,b in zip(row,expected)):
        raise RuntimeError('Unexpected CM4 positioning: '+json.dumps(report))
    design.computeAll()
    camera=app.activeViewport.camera
    camera.isSmoothTransition=False
    camera.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation
    camera.isFitView=True;app.activeViewport.camera=camera
    app.activeViewport.fit();app.activeViewport.refresh()
    output=ROOT/'exports'/'SafeWall-B-detailed-visual-v02.f3d'
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output))):raise RuntimeError('Visual F3D export failed')
    report.update({'document':doc.name,'export':str(output),'official_CM4_body_count':len(boxes),
                   'scope':'Official CM4 in enclosure; decorative carrier and final shaders are in the Blender scene'})
    (ROOT/'visualization'/'fusion-detailed-scene.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
