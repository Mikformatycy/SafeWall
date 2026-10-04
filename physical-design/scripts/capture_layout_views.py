"""Capture CAD views through Fusion itself; OS screen-recording permission is unnecessary."""
import json
from pathlib import Path
import adsk.core
import adsk.fusion

ROOT=Path('/Users/piotrek/Desktop/RaspberryPi-Hackathon/physical-design')


def capture(app,name,width=1800,height=1300):
    view=app.activeViewport
    camera=view.camera
    camera.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation
    camera.isSmoothTransition=False
    camera.isFitView=True
    view.camera=camera
    view.fit()
    view.refresh()
    adsk.doEvents()
    if not view.saveAsImageFile(str(ROOT/name),width,height):
        raise RuntimeError('Viewport export failed: '+name)


def run(_context: str):
    app=adsk.core.Application.get()
    design=adsk.fusion.Design.cast(app.activeProduct)
    root=design.rootComponent
    if not root.attributes.itemByName('SafeWall','status'):
        raise RuntimeError('Active document is not the generated SafeWall study')
    variants=[o for o in root.occurrences if o.component.name.startswith(('A PLANAR','B LAYERED'))]
    other=[o for o in root.occurrences if o not in variants]
    for occ in other:occ.isLightBulbOn=False
    for parent in variants:
        parent.isLightBulbOn=True
        for occ in parent.component.occurrences:
            occ.isLightBulbOn=not occ.component.name.startswith(('11 ','12 '))
    capture(app,'fusion-layout-open.png')
    for parent in variants:
        for occ in parent.component.occurrences:occ.isLightBulbOn=True
    capture(app,'fusion-layout-closed.png')
    preferred=next(o for o in variants if o.component.name.startswith('B '))
    for parent in variants:parent.isLightBulbOn=(parent==preferred)
    capture(app,'fusion-B-closed.png',1400,1400)
    # Preserve assembled geometry for downstream import. Blender shading will be rebuilt.
    obj=design.exportManager.createOBJExportOptions(preferred.component,str(ROOT/'exports'/'SafeWall-B-concept-v01.obj'))
    obj.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
    obj.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    if not design.exportManager.execute(obj):raise RuntimeError('OBJ export failed')
    scene=next((o for o in root.occurrences if o.component.name=='B EXPLODED - presentation only'),None)
    if scene is not None:
        other=[o for o in other if o!=scene]
        scene.deleteMe()
    # The exploded presentation is built in a separate imported document by
    # build_exploded_presentation.py, avoiding shared occurrence transforms.
    for parent in variants:
        parent.isLightBulbOn=True
        for occ in parent.component.occurrences:
            occ.isLightBulbOn=not occ.component.name.startswith(('11 ','12 '))
    for occ in other:
        if 'caption' in occ.component.name:occ.isLightBulbOn=True
    capture(app,'fusion-layout-open.png')
    design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(ROOT/'exports'/'SafeWall-layout-comparison-v01.f3d')))
    print(json.dumps({'captures':['fusion-layout-open.png','fusion-layout-closed.png','fusion-B-closed.png'],
                      'mesh':'exports/SafeWall-B-concept-v01.obj','mesh_note':'OBJ vertices are millimeters. Import into Blender at scale 0.001 for meters; recreate final shaders.'},indent=2))
