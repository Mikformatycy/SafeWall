"""Run through Fusion MCP. Creates a new, local packaging study, not a production enclosure.

Footprint sketches are generated from layout-study.json; key extrusion depths reference
Fusion user parameters. Re-run to generate a fresh document after changing the JSON.
All component blocks are explicitly labelled when they represent reserved space.
"""
import json
import math
from pathlib import Path
import adsk.core
import adsk.fusion

ROOT = Path('/Users/piotrek/Desktop/RaspberryPi-Hackathon/physical-design')


def pt(x, y, z=0):
    return adsk.core.Point3D.create(x / 10, y / 10, z / 10)


def value(expression):
    return adsk.core.ValueInput.createByString(str(expression))


def component(parent, name, x=0, y=0, z=0):
    transform = adsk.core.Matrix3D.create()
    transform.translation = adsk.core.Vector3D.create(x / 10, y / 10, z / 10)
    occurrence = parent.occurrences.addNewComponent(transform)
    occurrence.component.name = name
    return occurrence


def sketch(comp, name, z=0):
    plane = comp.xYConstructionPlane
    if z:
        inp = comp.constructionPlanes.createInput()
        inp.setByOffset(plane, value(f'{z} mm'))
        plane = comp.constructionPlanes.add(inp)
        plane.name = name + '_plane'
        plane.isLightBulbOn = False
    result = comp.sketches.add(plane)
    result.name = name
    return result


def rounded_rectangle(sk, x, y, width, length, radius):
    lines = sk.sketchCurves.sketchLines
    if radius == 0:
        lines.addTwoPointRectangle(pt(x, y), pt(x + width, y + length))
        return
    r = radius
    segments = [
        ((x+r, y), (x+width-r, y)),
        ((x+width, y+r), (x+width, y+length-r)),
        ((x+width-r, y+length), (x+r, y+length)),
        ((x, y+length-r), (x, y+r)),
    ]
    for a,b in segments:
        lines.addByTwoPoints(pt(*a), pt(*b))
    for center,start in [
        ((x+width-r,y+r),(x+width-r,y)),
        ((x+width-r,y+length-r),(x+width,y+length-r)),
        ((x+r,y+length-r),(x+r,y+length)),
        ((x+r,y+r),(x,y+r)),
    ]:
        sk.sketchCurves.sketchArcs.addByCenterStartSweep(pt(*center),pt(*start),math.pi/2)


def profile_with_loops(sk, loops=1):
    candidates = [p for p in sk.profiles if p.profileLoops.count == loops]
    if len(candidates) != 1:
        raise RuntimeError(f'{sk.name}: expected one profile with {loops} loops; got {len(candidates)}')
    return candidates[0]


def extrude(comp, sk, height, name, appearance, loops=1, cut=False):
    op = adsk.fusion.FeatureOperations.CutFeatureOperation if cut else adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    expression = height if isinstance(height, str) else f'{height} mm'
    feature = comp.features.extrudeFeatures.addSimple(profile_with_loops(sk, loops),value(expression),op)
    feature.name = name
    sk.isLightBulbOn = False
    if not cut:
        body = feature.bodies.item(0)
        body.name = name
        body.appearance = appearance
        return body
    return None


def block(parent, name, pos, size, appearance, radius=0.8, height_expression=None):
    occ = component(parent, name, *pos)
    sk = sketch(occ.component, name + '_outline')
    rounded_rectangle(sk,0,0,size[0],size[1],radius)
    body = extrude(occ.component,sk,height_expression or size[2],name,appearance)
    return occ, body


def ring(parent, name, center, outer, inner, height, appearance):
    occ = component(parent,name,center[0],center[1],center[2])
    sk = sketch(occ.component,name+'_outline')
    for diameter in [outer,inner]:
        sk.sketchCurves.sketchCircles.addByCenterRadius(pt(0,0),diameter/20)
    body = extrude(occ.component,sk,height,name,appearance,loops=2)
    return occ,body


def label(parent, name, text, x, y, width, size=3):
    occ=component(parent,name,x,y,0)
    sk=sketch(occ.component,name+'_text')
    inp=sk.sketchTexts.createInput3("'"+text+"'",value(f'{size} mm'))
    inp.setAsMultiLine(pt(0,0),pt(width,12),adsk.core.HorizontalAlignments.LeftHorizontalAlignment,
                       adsk.core.VerticalAlignments.TopVerticalAlignment,0)
    sk.sketchTexts.add(inp)
    return occ


def run(_context: str):
    data=json.loads((ROOT/'layout-study.json').read_text())
    common=data['common']; battery=data['battery_reference']
    app=adsk.core.Application.get()
    title='SafeWall - A-B packaging study v01 - CONCEPT'
    document=app.activeDocument
    design=adsk.fusion.Design.cast(app.activeProduct)
    reuse_empty_study=(document and document.name==title and design
                       and design.rootComponent.occurrences.count==0
                       and design.rootComponent.bRepBodies.count==0
                       and design.userParameters.count==0)
    if not reuse_empty_study:
        document=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        document.name=title
        design=adsk.fusion.Design.cast(app.activeProduct)
    design.designType=adsk.fusion.DesignTypes.ParametricDesignType
    design.unitsManager.distanceDisplayUnits=adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    root=design.rootComponent
    root.attributes.add('SafeWall','status','Concept only; dimensions and electronics arrangement unvalidated; no radio or runtime claim')
    root.attributes.add('SafeWall','source','physical-design/layout-study.json')
    for name,number in [('wall',common['shell_wall']),('rear',common['rear_panel_thickness']),('pad',common['contact_pad_thickness']),
                        ('pcb',common['carrier_thickness']),('cm4Mounted',common['cm4_mounted_height']),('batteryT',battery['pack_max_thickness'])]:
        design.userParameters.add(name,value(f'{number} mm'),'mm','Packaging study value; XY outlines are regenerated from layout-study.json')
    palettes={
        'Graphite_Satin':('#282C30',0.5), 'Contact_Silicone':('#17191C',0.85),
        'PCB_Green':('#175E48',0.5),'CM4_Envelope_Green':('#348868',0.5),
        'Battery_Pouch_Silver':('#ADB6C0',0.32),'LTE_Shield_Silver':('#7E8B99',0.25),
        'Magnet_Reservation':('#3A4658',0.3),'Power_IO_Reservation':('#D39B58',0.5),
        'Thermal_Concept':('#B97750',0.3),'Label':('#D9DFE5',0.6),
    }
    appearances={}
    for name,(hexcolor,roughness) in palettes.items():
        appearance=design.appearances.add(name)
        appearance.color=adsk.core.Color.create(*(int(hexcolor[i:i+2],16) for i in (1,3,5)),255)
        appearance.roughness=roughness
        appearances[name]=appearance
    export_dir=ROOT/'exports';export_dir.mkdir(exist_ok=True)
    report={'status':'packaging_concept_only','variants':[],'notes':data['unresolved_before_fit_or_production_claims']}
    for item in data['variants']:
        ident=item['id']; w=item['width'];l=item['length'];h=item['height'];r=item['corner_radius']
        parent_occ=component(root,ident+' '+item['name'],item['display_x'],0,0)
        parent=parent_occ.component
        parent.attributes.add('SafeWall','envelope_mm',json.dumps([w,l,h]))
        parent.attributes.add('SafeWall','battery_reference',battery['model'])
        pad, _=block(parent,'01 Contact pad - silicone proposal',(0,0,0),(w,l,0.6),appearances['Contact_Silicone'],r,'pad')
        rear_occ,rear_body=block(parent,'02 Rear panel - magnet pockets',(0,0,0.6),(w,l,2.4),appearances['Graphite_Satin'],r,'rear')
        rear_comp=rear_occ.component
        pocket=sketch(rear_comp,'Magnet_ring_pocket',2.4)
        for diameter in [55.1,45.0]:
            pocket.sketchCurves.sketchCircles.addByCenterRadius(pt(w/2,80),diameter/20)
        extrude(rear_comp,pocket,-2.0,'Ring pocket - depth provisional',None,loops=2,cut=True)
        slot=sketch(rear_comp,'Orientation_pocket',2.4)
        rounded_rectangle(slot,w/2-3.5,80-50.99,7,20.31,0.5)
        extrude(rear_comp,slot,-2.0,'Orientation pocket - depth provisional',None,cut=True)
        ring(parent,'03 Magnet ring SPACE ONLY - not magnet specification',(w/2,80,1.1),54.1,46,1.2,appearances['Magnet_Reservation'])
        block(parent,'04 Orientation magnet SPACE ONLY',(w/2-3,80-50.49,1.1),(6,19.31,1.2),appearances['Magnet_Reservation'],0)
        wall_occ=component(parent,'05 Perimeter walls - ports and fasteners unresolved',0,0,3)
        wall_sk=sketch(wall_occ.component,'Wall_ring')
        rounded_rectangle(wall_sk,0,0,w,l,r)
        rounded_rectangle(wall_sk,1.6,1.6,w-3.2,l-3.2,r-1.6)
        wall_body=extrude(wall_occ.component,wall_sk,h-4.8,'Shell perimeter',appearances['Graphite_Satin'],loops=2)
        battery_occ,_=block(parent,'06 Battery reference - EEMB 3400mAh - not selected',
            (item['battery_x'],item['battery_y'],item['battery_z']),
            (55.5,92,6.3),appearances['Battery_Pouch_Silver'],1.2,'batteryT')
        battery_occ.component.attributes.add('SafeWall','expansion_allowance','Not approved; dimensional study only. Validate against selected pack supplier.')
        cx=item['carrier_x'];cy=item['carrier_y'];cz=item['carrier_z']
        block(parent,'07 Custom carrier PCB ENVELOPE - no routing',(cx,cy,cz),(60,88,1.6),appearances['PCB_Green'],2,'pcb')
        block(parent,'08 CM4 installed ENVELOPE incl connectors',(cx+2.5,cy+42,cz+1.6),(55,40,6.578),appearances['CM4_Envelope_Green'],1,'cm4Mounted')
        block(parent,'09 LTE module size reference 32x29 - model undecided',(cx+5,cy+5,cz+1.6),(32,29,2.4),appearances['LTE_Shield_Silver'],1)
        block(parent,'10 Power and IO SPACE RESERVATION',(cx+42,cy+5,cz+1.6),(15,29,4),appearances['Power_IO_Reservation'],1)
        block(parent,'11 Thermal spreader CONCEPT - path unverified',(cx+3,cy+4,h-2.6),(54,78,0.6),appearances['Thermal_Concept'],2)
        lid_occ,lid_body=block(parent,'12 Lid - graphite proposal',(0,0,h-1.6),(w,l,1.6),appearances['Graphite_Satin'],r,'wall')
        label(root,ident+' study caption',f'{ident}   {w} x {l} x {h} mm',item['display_x'],-19,w,3.5)
        shell_volume=rear_body.volume+wall_body.volume+lid_body.volume
        entry={
            'id':ident,'envelope_mm':[w,l,h],'bounding_box_volume_cm3':w*l*h/1000,
            'shell_solid_volume_cm3':shell_volume,
            'estimated_shell_mass_g_at_assumed_density_1_15':shell_volume*1.15,
            'mass_is_not_total_device_mass':True,
            'battery_to_carrier_vertical_gap_mm':cz-(item['battery_z']+6.3) if ident=='B' else None,
            'assembly_component_count':parent.occurrences.count,
            'finding':item['finding'],
        }
        report['variants'].append(entry)
        for extension,method in [('step',design.exportManager.createSTEPExportOptions),('f3d',design.exportManager.createFusionArchiveExportOptions)]:
            filename=str(export_dir/f'SafeWall-{ident}-concept-v01.{extension}')
            if not design.exportManager.execute(method(filename,parent)):
                raise RuntimeError('Export failed: '+filename)
        # Open-cover presentation. Exports above retain assembled positions.
        lid_occ.isLightBulbOn=False
        for occ in parent.occurrences:
            if occ.component.name.startswith('11 '):occ.isLightBulbOn=False
    energy=data['energy_assumptions_not_measurements']
    factor=energy['average_conversion_efficiency']*energy['usable_energy_fraction']
    nominal=battery['nominal_voltage_v']*battery['capacity_typical_mah']/1000
    minimum=battery['nominal_voltage_v']*battery['capacity_minimum_mah']/1000
    report['energy_estimate']={
        'nominal_wh':nominal,'minimum_capacity_based_wh':minimum,
        'assumed_efficiency_times_usable_fraction':factor,
        'max_average_load_for_2h_typical_w':nominal*factor/2,
        'max_average_load_for_2h_minimum_capacity_w':minimum*factor/2,
        'runtime_scenarios_h':{str(p):nominal*factor/p for p in energy['load_scenarios_w']},
        'measurement_status':'no_power_or_runtime_measurement_performed',
    }
    (ROOT/'layout-study-results.json').write_text(json.dumps(report,indent=2))
    camera=app.activeViewport.camera
    camera.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation
    camera.isFitView=True
    camera.isSmoothTransition=False
    app.activeViewport.camera=camera
    app.activeViewport.fit()
    app.activeViewport.refresh()
    design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(export_dir/'SafeWall-layout-comparison-v01.f3d')))
    import sys
    sys.path.insert(0,str(ROOT/'scripts'))
    from finish_layout_study import run as finish
    finish(_context)
    print(json.dumps(report,indent=2))
