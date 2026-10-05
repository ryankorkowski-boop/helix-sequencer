from __future__ import annotations

import argparse
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import librosa
import numpy as np

from audio.drum_classification import DrumEvent as LegacyDrumEvent
from core.drummer_v3_analysis import DrumType, analyze_drummer_features
from mapping.drum_mapper import DRUMMER_COMPONENTS, map_events_to_drummer_components, resolve_drum_streams

DRUMMER_V3_MODEL = "HX_SNOWMAN_DRUMMER_V3"
DRUMMER_TARGETS = set(DRUMMER_COMPONENTS)

def _find_or_create_element_effects(root):
    return root.find("ElementEffects") or ET.SubElement(root, "ElementEffects")

def _element_map(container):
    return {e.get("name", ""): e for e in container.findall("Element") if e.get("name")}

def _layer_for(container, elements, name, layer_name):
    element = elements.get(name)
    if element is None:
        element = ET.SubElement(container, "Element", {"type": "model", "name": name}); elements[name] = element
    for layer in element.findall("EffectLayer"):
        if layer.get("name") == layer_name:return layer
    return ET.SubElement(element, "EffectLayer", {"name": layer_name, "visible": "1"})

def _clear_layer(layer):
    for child in list(layer):layer.remove(child)

def _add_on(layer, start_ms, end_ms, intensity, component, source_type):
    ET.SubElement(layer, "Effect", {"name":"On","startTime":str(max(0,int(start_ms))),"endTime":str(max(int(start_ms)+50,int(end_ms))),"settings":f"E_CHECKBOX_OverlayBkg=0,E_SLIDER_Brightness={max(.08,min(1.,float(intensity))):.3f}","palette":"C_BUTTON_Palette1=#FFFFFF,C_BUTTON_Palette2=#FFFFFF,C_BUTTON_Palette3=#FFFFFF","source":"HelixDrummerV3","sourceModel":DRUMMER_V3_MODEL,"sourceComponent":component,"sourceDrumType":source_type})

def _band_energy(magnitude, freqs, lo, hi):
    mask=(freqs>=lo)&(freqs<hi)
    if not np.any(mask):return np.zeros(magnitude.shape[1],dtype=float)
    return np.sqrt(np.mean(np.square(magnitude[mask]),axis=0))

def _analyze_real_audio(audio_path: Path):
    y,sr=librosa.load(str(audio_path),sr=None,mono=True); hop=max(128,int(round(sr*.01))); n_fft=max(1024,2**int(np.ceil(np.log2(max(1024,int(sr*.046))))))
    stft_complex=librosa.stft(y,n_fft=n_fft,hop_length=hop,center=True); stft=np.abs(stft_complex)
    harmonic,percussive=librosa.effects.hpss(y,margin=2.0); p_complex=librosa.stft(percussive,n_fft=n_fft,hop_length=hop,center=True); p_stft=np.abs(p_complex)
    h_rms=librosa.feature.rms(y=harmonic,frame_length=n_fft,hop_length=hop,center=True)[0]; p_rms=librosa.feature.rms(y=percussive,frame_length=n_fft,hop_length=hop,center=True)[0]
    n=min(stft.shape[1],p_stft.shape[1],len(h_rms),len(p_rms)); stft,p_stft=stft[:,:n],p_stft[:,:n]; h_rms,p_rms=h_rms[:n],p_rms[:n]
    freqs=librosa.fft_frequencies(sr=sr,n_fft=n_fft); low=_band_energy(stft,freqs,35,180); mid=_band_energy(stft,freqs,180,2400); high=_band_energy(stft,freqs,2400,min(sr/2,12000)); drum_low=_band_energy(p_stft,freqs,35,220); drum_mid=_band_energy(p_stft,freqs,220,2400); drum_high=_band_energy(p_stft,freqs,2400,min(sr/2,14000))
    drum_quality=p_rms/np.maximum(p_rms+h_rms,1e-9); flatness=librosa.feature.spectral_flatness(S=p_stft)[0][:n]
    rms=librosa.feature.rms(y=y,frame_length=n_fft,hop_length=hop,center=True)[0][:n]; times=librosa.frames_to_time(np.arange(n),sr=sr,hop_length=hop); tempo,beats=librosa.beat.beat_track(y=y,sr=sr,hop_length=hop,units="frames"); beats=np.asarray(beats,dtype=int)
    events=analyze_drummer_features(low=low,mid=mid,high=high,rms=rms,times=times,drum_low=drum_low,drum_mid=drum_mid,drum_high=drum_high,beat_indices=beats,frame_rate=sr/hop,drum_percussive_ratio=drum_quality,percussive_flatness=flatness,min_percussive_ratio=.30)
    legacy=[]
    for idx,event in enumerate(events):
        if event.kind==DrumType.KICK:drum_type="kick"
        elif event.kind==DrumType.SNARE:drum_type="snare"
        elif event.kind==DrumType.HI_HAT:drum_type="hihat"
        elif event.kind==DrumType.CYMBAL:drum_type="cymbal"
        elif event.kind in (DrumType.TOM_HIGH,DrumType.TOM_MID,DrumType.TOM_FLOOR):drum_type="tom"
        else:continue
        tom_class={DrumType.TOM_HIGH:"high",DrumType.TOM_MID:"mid",DrumType.TOM_FLOOR:"floor"}.get(event.kind); frame=min(n-1,max(0,int(round(event.time*sr/hop)))); quality=float(drum_quality[frame]); info={"analysis_engine":"v3_multi_detector","event_frame":float(round(event.time*sr/hop)),"percussive_ratio":round(quality,4),"percussive_flatness":round(float(flatness[frame]),4)}
        if tom_class:info["tom_class"]=tom_class
        legacy.append(LegacyDrumEvent(timestamp=float(event.time),velocity=float(max(.08,min(1.,event.confidence))),confidence=float(event.confidence),frequency_band_info=info,cluster_id=idx,drum_type=drum_type,source="v3_multi_detector"))
    diagnostics={"analysis_engine":"v3_multi_detector","sample_rate":int(sr),"frame_rate":round(sr/hop,3),"tempo_bpm":float(np.asarray(tempo).reshape(-1)[0]) if np.asarray(tempo).size else 0.,"beat_count":int(len(beats)),"typed_event_count":len(legacy),"event_types":{kind.value:sum(e.kind==kind for e in events) for kind in DrumType},"used_hpss_percussive_stem":True,"min_percussive_ratio":.30,"percussive_ratio_p10":round(float(np.percentile(drum_quality,10)),4) if len(drum_quality) else 0.,"percussive_ratio_median":round(float(np.median(drum_quality)),4) if len(drum_quality) else 0.,"percussive_flatness_median":round(float(np.median(flatness)),4) if len(flatness) else 0.}
    return legacy,diagnostics

def inject_drummer_v3(base_xsq,output_xsq,audio_path,*,layer_name="AUTO_Drummer_V3"):
    base_xsq,output_xsq,audio_path=Path(base_xsq),Path(output_xsq),Path(audio_path)
    if not base_xsq.exists() or not audio_path.exists():raise FileNotFoundError("Missing XSQ or audio input")
    typed_events,diagnostics=_analyze_real_audio(audio_path); streams={"kick_events":[e for e in typed_events if e.drum_type=="kick"],"snare_events":[e for e in typed_events if e.drum_type=="snare"],"tom_events":[e for e in typed_events if e.drum_type=="tom"],"hihat_events":[e for e in typed_events if e.drum_type=="hihat"],"cymbal_events":[e for e in typed_events if e.drum_type=="cymbal"],"drum_bus_events":[]}; resolved=resolve_drum_streams(streams); component_events=map_events_to_drummer_components(resolved["events"])
    if output_xsq.resolve()!=base_xsq.resolve():output_xsq.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(base_xsq,output_xsq)
    tree=ET.parse(output_xsq);root=tree.getroot();container=_find_or_create_element_effects(root);elements=_element_map(container);layers={}
    for name in sorted(DRUMMER_TARGETS):layers[name]=_layer_for(container,elements,name,layer_name);_clear_layer(layers[name])
    placements=0
    for event in component_events:
        component=str(event["component"])
        if component not in DRUMMER_TARGETS:raise ValueError(f"Non-canonical drummer target emitted: {component}")
        _add_on(layers[component],event["timestamp_ms"],event["end_ms"],event["intensity"],component,event["drum_type"]);placements+=1
    if layer_name not in {n.get("name") for n in root.findall("timingtrack")}:ET.SubElement(root,"timingtrack",{"name":layer_name})
    ET.indent(tree,space="  ");tree.write(output_xsq,encoding="utf-8",xml_declaration=True);drum_type_counts={key.removesuffix("_events"):len(value) for key,value in streams.items()};component_counts={component:sum(1 for event in component_events if event["component"]==component) for component in sorted(DRUMMER_TARGETS)};typed_count=sum(drum_type_counts.get(k,0) for k in ("kick","snare","tom","hihat","cymbal"))
    return {"schema":"helix.drummer_v3_xsq_integration.v6","model":DRUMMER_V3_MODEL,"base_xsq":str(base_xsq),"output_xsq":str(output_xsq),"audio":str(audio_path),"layer":layer_name,"fallback_mode":"typed_detection","event_count":len(component_events),"placement_count":placements,"drum_type_counts":drum_type_counts,"typed_event_count":typed_count,"drum_bus_event_count":0,"drum_bus_ratio":0.,"component_counts":component_counts,"targets":sorted(DRUMMER_TARGETS),"target_count":len(DRUMMER_TARGETS),"analysis":diagnostics}

def main():
    p=argparse.ArgumentParser();p.add_argument("base_xsq",type=Path);p.add_argument("audio",type=Path);p.add_argument("--output",type=Path,required=True);p.add_argument("--layer",default="AUTO_Drummer_V3");p.add_argument("--report",type=Path);a=p.parse_args();report=inject_drummer_v3(a.base_xsq,a.output,a.audio,layer_name=a.layer);print(json.dumps(report,indent=2,sort_keys=True));
    if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2),encoding="utf-8")
    return 0
if __name__=="__main__":raise SystemExit(main())
