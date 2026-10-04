"""Make an independent presentation from the actual assembled export."""
import json
from pathlib import Path
import adsk.core
import adsk.fusion

ROOT=Path('/Users/piotrek/Desktop/RaspberryPi-Hackathon/physical-design')


def extent(design):
    boxes=[b.boundingBox for o in design.rootComponent.allOccurrences for b in o.bRepBodies]
    return [round(10*(max(b.maxPoint.asArray()[i] for b in boxes)-min(b.minPoint.asArray()[i] for b in boxes)),3) for i in range(3)]


def run(_context: str):
    app=adsk.core.Application.get()
    original=app.activeDocument
    manager=app.importManager
    document=manager.importToNewDocument(manager.createFusionArchiveImportOptions(str(ROOT/'exports'/'SafeWall-B-concept-v01.f3d')))
    document.name='SafeWall B - independent exploded presentation'
    design=adsk.fusion.Design.cast(app.activeProduct)
    assembled=extent(design)
    if assembled!=[70.0,110.0,24.0]:
        original.activate()
        raise RuntimeError('Unexpected assembled archive dimensions: '+str(assembled))
    offsets={'01':0,'02':0,'03':0,'04':0,'05':0,'06':25,'07':45,'08':50,'09':50,'10':50,'11':75,'12':95}
    for occurrence in design.rootComponent.allOccurrences:
        occurrence.isLightBulbOn=True
        offset=offsets[occurrence.component.name[:2]]
        if offset:
            entities=adsk.core.ObjectCollection.create()
            for body in occurrence.component.bRepBodies:entities.add(body)
            inp=occurrence.component.features.moveFeatures.createInput2(entities)
            transform=adsk.core.Matrix3D.create()
            transform.translation=adsk.core.Vector3D.create(0,0,offset/10)
            inp.defineAsFreeMove(transform)
            feature=occurrence.component.features.moveFeatures.add(inp)
            feature.name='Presentation separation only - '+str(offset)+' mm'
    design.computeAll()
    exploded=extent(design)
    if exploded!=[70.0,110.0,119.0]:
        original.activate()
        raise RuntimeError('Unexpected presentation dimensions: '+str(exploded))
    filename=str(ROOT/'exports'/'SafeWall-B-exploded-v01.f3d')
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(filename)):
        raise RuntimeError('Presentation archive export failed')
    original.activate()
    print(json.dumps({'assembled_archive_extent_mm':assembled,'exploded_extent_mm':exploded,'export':filename},indent=2))
