"""Import Raspberry Pi's official CM4 STEP as a separate reference document."""
import json
from pathlib import Path
import adsk.core
import adsk.fusion

ROOT=Path('/Users/piotrek/Desktop/RaspberryPi-Hackathon/physical-design')


def run(_context: str):
    app=adsk.core.Application.get()
    folder=ROOT/'references'/'cm4-official'
    options=app.importManager.createSTEPImportOptions(str(folder/'CM4.step'))
    document=app.importManager.importToNewDocument(options)
    document.name='SafeWall reference - official Raspberry Pi CM4'
    design=adsk.fusion.Design.cast(app.activeProduct)
    design.computeAll()
    root=design.rootComponent
    rows=[]
    bodies=list(root.bRepBodies)
    for occ in root.allOccurrences:
        bodies.extend(list(occ.bRepBodies))
    for body in bodies:
        box=body.boundingBox
        rows.append({'name':body.name,'appearance':body.appearance.name if body.appearance else None,
                     'box_mm':[[round(v*10,5) for v in box.minPoint.asArray()],
                               [round(v*10,5) for v in box.maxPoint.asArray()]]})
    bounds=[[min(r['box_mm'][0][i] for r in rows) for i in range(3)],
            [max(r['box_mm'][1][i] for r in rows) for i in range(3)]]
    obj=design.exportManager.createOBJExportOptions(root,str(folder/'CM4.obj'))
    obj.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
    obj.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    if not design.exportManager.execute(obj):raise RuntimeError('CM4 OBJ export failed')
    report={'body_count':len(rows),'bounds_mm':bounds,'bodies':rows}
    (folder/'geometry.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'body_count':len(rows),'bounds_mm':bounds,'sample_parts':rows[:12]},indent=2))
