"""Refine only the generated SafeWall concept, assign proposed shell materials and export."""
import json
from pathlib import Path
import adsk.core
import adsk.fusion

ROOT=Path('/Users/piotrek/Desktop/RaspberryPi-Hackathon/physical-design')


def run(_context: str):
    app=adsk.core.Application.get()
    design=adsk.fusion.Design.cast(app.activeProduct)
    root=design.rootComponent
    if not root.attributes.itemByName('SafeWall','status'):
        raise RuntimeError('Active document is not the generated SafeWall study')
    data=json.loads((ROOT/'layout-study.json').read_text())
    library=app.materialLibraries.itemByName('Fusion Material Library')
    materials={}
    for key,name,source_id in [('shell','SafeWall PC-ABS reference - grade TBD','PrismMaterial-278'),
                               ('pad','SafeWall Silicone reference - grade TBD','PrismMaterial-029')]:
        materials[key]=design.materials.itemByName(name) or design.materials.addByCopy(library.materials.itemById(source_id),name)
    results=[]
    for assembly in root.occurrences:
        if not assembly.component.name.startswith(('A PLANAR','B LAYERED')):
            continue
        ident=assembly.component.name[0]
        params=next(v for v in data['variants'] if v['id']==ident)
        shell_mass=0;pad_mass=0;shell_volume=0
        for occ in assembly.childOccurrences:
            name=occ.component.name
            for body in occ.component.bRepBodies:
                if name.startswith(('02 ','05 ','12 ')):
                    body.material=materials['shell']
                    body.appearance=design.appearances.itemByName('Graphite_Satin')
                elif name.startswith('01 '):
                    body.material=materials['pad']
                    body.appearance=design.appearances.itemByName('Contact_Silicone')
                if name.startswith('12 ') and not body.attributes.itemByName('SafeWall','top_edge_finished'):
                    top=body.boundingBox.maxPoint.z
                    edges=adsk.core.ObjectCollection.create()
                    for edge in body.edges:
                        box=edge.boundingBox
                        if abs(box.minPoint.z-top)<1e-7 and abs(box.maxPoint.z-top)<1e-7:
                            edges.add(edge)
                    inp=occ.component.features.filletFeatures.createInput()
                    inp.edgeSetInputs.addConstantRadiusEdgeSet(edges,adsk.core.ValueInput.createByString('0.5 mm'),True)
                    feature=occ.component.features.filletFeatures.add(inp)
                    feature.name='Lid top edge - 0.5 mm comfort radius'
                    body.attributes.add('SafeWall','top_edge_finished','v01')
                if name.startswith(('02 ','05 ','12 ')):
                    shell_mass+=body.physicalProperties.mass*1000
                    shell_volume+=body.volume
                elif name.startswith('01 '):
                    pad_mass+=body.physicalProperties.mass*1000
            if name.startswith('11 '):
                current=occ.bRepBodies.item(0).boundingBox.minPoint.z
                delta=(params['height']-2.6)/10-current
                if abs(delta)>1e-7:
                    entities=adsk.core.ObjectCollection.create()
                    entities.add(occ.component.bRepBodies.item(0))
                    inp=occ.component.features.moveFeatures.createInput2(entities)
                    transform=adsk.core.Matrix3D.create()
                    transform.translation=adsk.core.Vector3D.create(0,0,delta)
                    inp.defineAsFreeMove(transform)
                    feature=occ.component.features.moveFeatures.add(inp)
                    feature.name='Thermal envelope clearance correction'
            occ.isLightBulbOn=True
        if design.snapshots.hasPendingSnapshot:
            design.snapshots.add()
        for extension,creator in [('f3d',design.exportManager.createFusionArchiveExportOptions),('step',design.exportManager.createSTEPExportOptions)]:
            filename=str(ROOT/'exports'/f'SafeWall-{ident}-concept-v01.{extension}')
            if not design.exportManager.execute(creator(filename,assembly.component)):
                raise RuntimeError('Export failed: '+filename)
        for occ in assembly.component.occurrences:
            if occ.component.name.startswith(('11 ','12 ')):
                occ.isLightBulbOn=False
        results.append({'id':ident,'shell_solid_volume_cm3':shell_volume,'shell_mass_g_using_Fusion_reference_PC_ABS':shell_mass,
                        'contact_pad_mass_g_using_Fusion_reference_silicone':pad_mass,
                        'total_device_mass_not_estimated':True,
                        'material_grades_not_selected':True})
    app.activeViewport.refresh()
    design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(ROOT/'exports'/'SafeWall-layout-comparison-v01.f3d')))
    (ROOT/'fusion-materials.json').write_text(json.dumps(results,indent=2))
    report_path=ROOT/'layout-study-results.json'
    if report_path.exists():
        report=json.loads(report_path.read_text())
        for item in report['variants']:
            finished=next(r for r in results if r['id']==item['id'])
            item.pop('estimated_shell_mass_g_at_assumed_density_1_15',None)
            item.update(finished)
        report_path.write_text(json.dumps(report,indent=2))
    print(json.dumps({'finishing':'complete','materials':results},indent=2))
