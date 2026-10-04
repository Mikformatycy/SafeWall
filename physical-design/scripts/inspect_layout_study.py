"""Inspect the active SafeWall study without changing geometry."""
import json
from pathlib import Path
import adsk.core
import adsk.fusion


def run(_context: str):
    app=adsk.core.Application.get()
    design=adsk.fusion.Design.cast(app.activeProduct)
    root=design.rootComponent
    results={'document':app.activeDocument.name,'variants':[],'material_candidates':[]}
    for occurrence in root.occurrences:
        if not occurrence.component.name.startswith(('A PLANAR','B LAYERED')):
            continue
        entities=adsk.core.ObjectCollection.create()
        bodies=[]
        for child in occurrence.childOccurrences:
            for body in child.bRepBodies:
                entities.add(body)
                box=body.boundingBox
                bodies.append({'name':body.name,'solid':body.isSolid,'volume_cm3':body.volume,
                    'box_mm':[[round(v*10,4) for v in box.minPoint.asArray()],[round(v*10,4) for v in box.maxPoint.asArray()]]})
        inp=design.createInterferenceInput(entities)
        inp.areCoincidentFacesIncluded=False
        found=design.analyzeInterference(inp)
        collisions=[]
        for item in found:
            collisions.append({'a':item.entityOne.name,'b':item.entityTwo.name,'volume_cm3':item.interferenceBody.volume})
        health=[]
        for child in occurrence.childOccurrences:
            for feature in child.component.features:
                if feature.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:
                    health.append({'name':feature.name,'message':feature.errorOrWarningMessage})
        results['variants'].append({'name':occurrence.component.name,'bodies':bodies,'interferences':collisions,'feature_issues':health})
    for library in app.materialLibraries:
        for material in library.materials:
            if any(t in material.name.lower() for t in ['pc/abs','pc-abs','polycarbonate','silicone']):
                results['material_candidates'].append({'library':library.name,'id':material.id,'name':material.name})
    target=Path('/Users/piotrek/Desktop/RaspberryPi-Hackathon/physical-design/fusion-validation.json')
    target.write_text(json.dumps(results,indent=2))
    print(json.dumps({'document':results['document'],'variants':[
        {'name':v['name'],'body_count':len(v['bodies']),
         'all_solid':all(b['solid'] for b in v['bodies']),
         'interferences':v['interferences'],'feature_issues':v['feature_issues']}
        for v in results['variants']]},indent=2))
