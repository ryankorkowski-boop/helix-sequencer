"""Apply canonical pitched-note plans to explicitly addressable native props."""
from __future__ import annotations

import json,math,tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
from core.keyboard_rung_export import export_keyboard_rungs
from music.magic_keyboard import magic_keyboard_events
from music.note_events import NoteEvent
from music.unified_mallet import unified_mallet_schedule,bar_pitch


def apply_native_pitched_props(sequence, layout, band_plan):
    sequence,layout,band_plan=map(Path,(sequence,layout,band_plan))
    definitions={m.get('name'):m for m in ET.parse(layout).getroot().findall('models/model')}
    names=['HX_CENTER_KEYBOARD_HELIX','HX_BETA_STAGE_A_XYLOPHONE','HX_BETA_STAGE_B_XYLOPHONE']
    targets={n:definitions[n] for n in names if n in definitions}
    if not targets:return None
    if not band_plan.is_file():raise RuntimeError('Addressable pitched props require the engine band-note plan')
    root=ET.parse(sequence).getroot();duration=float(root.findtext('head/sequenceDuration','0'))
    plan=json.loads(band_plan.read_text());notes=[]
    for cue in plan.get('cues',{}).get('keyboardist',[]):
        if cue.get('pitch_source')!='helix_harmonic_polyphony':continue
        notes.append(NoteEvent(cue['start_ms']/1000,cue['end_ms']/1000,cue['pitch_midi'],
            cue.get('velocity',1),source=cue['pitch_source']))
    notes=magic_keyboard_events(notes,duration=duration)
    # These reserved authored props have dedicated note ownership. Retain the
    # raw generated XSQ for review, then remove broad model/part effects which
    # would otherwise illuminate every bar/rung underneath a selected note.
    sequence.with_suffix('.before_pitched.xml').write_bytes(sequence.read_bytes())
    replaced=0
    for parent in root.findall('ElementEffects/Element'):
        name=parent.get('name')
        if name not in targets:continue
        for layer in list(parent):
            if layer.tag=='EffectLayer' or (layer.tag=='SubModelEffectLayer' and
                (name!=names[0] or layer.get('name','') not in ('STRAND_A','STRAND_B'))):
                replaced+=len(layer);parent.remove(layer)
    report=dict(schema='helix.native_pitched_props.v1',events=len(notes),targets={},
        original_layout_preserved=True,native_playback_verified=False,
        instrument_identity_verified=False,source='canonical harmonic polyphony',
        replaced_broad_effects=replaced,audit_backup=sequence.with_suffix('.before_pitched.xml').name)
    with tempfile.NamedTemporaryFile(suffix='.xsq',prefix='.pitched-',dir=sequence.parent,delete=False) as stream:
        temporary=Path(stream.name)
    try:
        if names[0] in targets:
            ET.ElementTree(root).write(temporary,encoding='utf-8',xml_declaration=True)
            report['targets'][names[0]]=export_keyboard_rungs(temporary,layout,temporary,
                [dict(pitch=e.pitch,start=e.start,end=e.end) for e in notes],duration=duration)
            root=ET.parse(temporary).getroot()
        elements=root.find('ElementEffects');displays=root.find('DisplayElements')
        palettes=root.find('ColorPalettes');db=root.find('EffectDB')
        if any(v is None for v in (elements,displays,palettes,db)):raise ValueError('Incomplete native XSQ')
        identifier=max((int(e.get('id','0')) for e in root.findall('.//Effect') if e.get('id','0').isdigit()),default=0)+1
        for name in names[1:]:
            if name not in targets:continue
            model=targets[name]
            if model.get('StringType')!='RGB Nodes':raise ValueError('Mallet note output requires RGB Nodes')
            subs={s.get('name'):s for s in model.findall('subModel')}
            if any(not subs.get(f'NOTE_MIDI_{p}',ET.Element('empty')).get('line0') for p in range(48,97)):
                raise ValueError('Incomplete 49-bar native mallet mapping')
            reachable={side:{p for p in range(48,97) if f'ARM_{side.upper()}_NOTE_{p}' in subs} for side in ('left','right')}
            hits,omitted=unified_mallet_schedule(notes,duration=duration,reachable=reachable)
            parent=next((e for e in elements if e.get('name')==name),None)
            if parent is None:
                parent=ET.SubElement(elements,'Element',name=name,type='model')
                ET.SubElement(displays,'Element',name=name,type='model',visible='1',collapsed='1')
            layers={}
            palette_id=len(palettes)
            ET.SubElement(palettes,'ColorPalette').text='C_BUTTON_Palette1=#D4B98A,C_CHECKBOX_Palette1=1'
            def effect(part,start,end,level):
                nonlocal identifier
                a=round(start*1000);b=min(round(duration*1000),round(end*1000))
                if b<=a:return
                if part not in layers:
                    existing=[int(e.get('layer','0')) for e in parent.findall('SubModelEffectLayer') if e.get('name')==part]
                    layers[part]=ET.SubElement(parent,'SubModelEffectLayer',name=part,layer=str(max(existing,default=-1)+1))
                ref=len(db);bright=round(max(0,min(1,level))*100)
                ET.SubElement(db,'Effect').text=f'E_TEXTCTRL_Eff_On_Start={bright},E_TEXTCTRL_Eff_On_End={max(1,round(bright*.35))}'
                ET.SubElement(layers[part],'Effect',name='On',ref=str(ref),palette=str(palette_id),id=str(identifier),startTime=str(a),endTime=str(b));identifier+=1
            for e in notes:effect(f'NOTE_MIDI_{bar_pitch(e.pitch)}',e.start,e.end,e.velocity)
            for hit in hits:effect(f"ARM_{hit['side'].upper()}_NOTE_{hit['pitch']}",hit['time'],hit['time']+.05,hit['velocity'])
            if 'BODY' in subs:effect('BODY',0,duration,.30)
            for side in ('left','right'):
                cursor=0.
                for hit in [h for h in hits if h['side']==side]:
                    if hit['time']>cursor:effect(f'ARM_{side.upper()}_IDLE',cursor,hit['time'],.30)
                    cursor=max(cursor,hit['time']+.05)
                if cursor<duration:effect(f'ARM_{side.upper()}_IDLE',cursor,duration,.30)
            report['targets'][name]=dict(notes=len(notes),contacts=len(hits),motion_omissions=omitted)
        nextid=root.find('nextid')
        if nextid is None:nextid=ET.SubElement(root,'nextid')
        nextid.text=str(identifier);ET.indent(root)
        ET.ElementTree(root).write(temporary,encoding='utf-8',xml_declaration=True)
        temporary.replace(sequence)
    finally:temporary.unlink(missing_ok=True)
    sequence.with_suffix('.native_pitched_props.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
