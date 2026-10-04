"""Reopen the exported presentation archive and inspect its actual geometry."""
import json
from pathlib import Path
import adsk.core
import adsk.fusion

ROOT=Path('/Users/piotrek/Desktop/RaspberryPi-Hackathon/physical-design')


def run(_context: str):
    app=adsk.core.Application.get()
    original=app.activeDocument
    manager=app.importManager
    options=manager.createFusionArchiveImportOptions(str(ROOT/'exports'/'SafeWall-B-exploded-v01.f3d'))
    document=manager.importToNewDocument(options)
    document.name='SafeWall B exploded - reopened export verification'
    design=adsk.fusion.Design.cast(app.activeProduct)
    design.computeAll()
    rows=[]
    for occurrence in design.rootComponent.allOccurrences:
        occurrence.isLightBulbOn=True
        for body in occurrence.bRepBodies:
            box=body.boundingBox
            rows.append({'name':body.name,'solid':body.isSolid,
                         'box_mm':[[round(v*10,4) for v in box.minPoint.asArray()],
                                   [round(v*10,4) for v in box.maxPoint.asArray()]]})
    extent=[round(max(r['box_mm'][1][i] for r in rows)-min(r['box_mm'][0][i] for r in rows),3) for i in range(3)]
    if len(rows)!=12 or not all(r['solid'] for r in rows) or extent!=[70.0,110.0,119.0]:
        original.activate()
        raise RuntimeError('Unexpected exploded archive geometry: '+json.dumps({'extent':extent,'bodies':rows}))
    viewport=app.activeViewport
    camera=viewport.camera
    camera.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation
    camera.isSmoothTransition=False
    camera.isFitView=True
    viewport.camera=camera
    viewport.fit()
    viewport.refresh()
    adsk.doEvents()
    (ROOT/'export-archive-validation.json').write_text(json.dumps({'reopened':True,'extent_mm':extent,'bodies':rows},indent=2))
    # Keep this document active. Capture on the next MCP request, after Fusion's
    # document activation and viewport redraw have completed.
    print(json.dumps({'reopened':True,'body_count':len(rows),'extent_mm':extent},indent=2))
