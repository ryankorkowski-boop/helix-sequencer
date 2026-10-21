"""Sequence AC and progressive native layouts from fresh source-bound analysis."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
import numpy as np
import soundfile as sf
from models.progressive_showcase import build_progressive
from models.ultimate_showcase import Garden
from models.native_review_band import add_band, ac_variant, allocate
from tools.native_source_pose_band import select_cast
from tools.render_approval_revision import setup
from tools.build_spatial_review import score, band_curves
from tools.build_snowman_ensemble import NativeSequence
from tools.build_helpers.ultimate_showcase import write_layout
from models.review_3d_scene import Review3DScene
from music.review_score import spatial_score


def write_show(g, cues, folder, audio, duration, camera):
    folder.mkdir(parents=True)
    (folder / 'media').mkdir()
    shutil.copy2(audio, folder / 'media/audio.wav')
    write_layout(g, folder, include_demo=False, export_all_custom=True)
    tree = ET.parse(folder / 'xlights_rgbeffects.xml')
    for point in tree.findall('./Viewpoints/*'):
        for key, value in camera.items():
            point.set(key, str(value))
    tree.write(folder / 'xlights_rgbeffects.xml', encoding='utf-8', xml_declaration=True)
    seq = NativeSequence(g, duration, 'media/audio.wav', g.title)
    active = {}
    for m in g.models:
        active[m.name] = 0
        for part, curve in cues.get(m.name, {}).items():
            if not m.submodels.get(part):
                continue
            values = np.rint(np.clip(curve, 0, 1) * 20).astype(int) * 5
            active[m.name] += int(np.count_nonzero(values))
            node = m.submodels[part][0] - 1
            color = m.colors[node] if m.kind == 'pixel' else m.colors[0]
            cuts = np.r_[0, np.flatnonzero(np.diff(values)) + 1, len(values)]
            for a, b in zip(cuts[:-1], cuts[1:]):
                if values[a]:
                    seq.effect(m, part, int(a) * 50, int(b) * 50, color, int(values[a]))
    seq.write(folder / 'Performance.xsq')
    result = dict(title=g.title, models=len(g.models), channels=sum(m.channels for m in g.models),
        ac_circuits=sum(m.channels for m in g.models if m.kind == 'ac'),
        pixel_nodes=sum(len(m.points) for m in g.models if m.kind == 'pixel'),
        effects=seq.identifier - 1, lit_curve_frames=active, duration_seconds=duration,
        native_movie_verified=False, native_render_required=True)
    (folder / 'generation.json').write_text(json.dumps(result, indent=2))
    return result


def build(root, *, levels=None, include_ac_band=True):
    root = root.resolve()
    _, audio, _, p = setup(root, 'sampler', scene_factory=Review3DScene)
    p.row = {'drummer_xsq': str(root / 'sources/sampler/drummer.xsq')}
    duration = sf.info(audio).duration
    result = []
    if include_ac_band:
        g = Garden(title='Helix AC16 six-snowman band')
        add_band(g)
        g.models = [ac_variant(m) for m in select_cast(g.models)]
        positions=dict(drummer=(0,26,65),bass=(-24,9,80),guitar=(24,9,80),
                       piano=(-30,28,65),lead=(-8,9,80),harmony=(8,9,80))
        for m in g.models:
            delta=np.array(positions[m.details['review_role']])-np.array([float(m.attrs['WorldPos'+a]) for a in 'XYZ'])
            m.points+=delta
            for i,axis in enumerate('XYZ'):
                m.attrs['WorldPos'+axis]=str(float(m.attrs['WorldPos'+axis])+delta[i])
            m.attrs['PixelSize']='8'
        allocate(g)
        cues = {m.name: band_curves(m, p, body_level=.6) for m in g.models}
        result.append(write_show(g, cues, root / 'shows/01_AC_Band', audio, duration,
            dict(angleX=8, angleY=0, distance=-65, pany=-18, panz=-75)))
    for level in (range(6) if levels is None else levels):
        g = build_progressive(level)
        cues, proof = score(g, p, level, body_level=.6)
        ac_parts = [(m, part) for m in g.models if m.kind == 'ac' for part in m.submodels]
        if ac_parts:
            positions = [m.points.mean(axis=0) + (j * .7, 0, 0) for j, (m, _) in enumerate(ac_parts)]
            lanes, _ = spatial_score(p, positions, np.arange(len(ac_parts)) % 6, level)
            for i, (m, part) in enumerate(ac_parts):
                # A separately documented standby level keeps the physical
                # strings identifiable during sparse passages. Only source
                # activity raises them above standby; no new attacks/times.
                cues.setdefault(m.name, {})[part] = np.where(
                    lanes[i] > .025, .35 + .65 * np.sqrt(lanes[i]), .12)
        for m in g.models:
            if m.kind != 'pixel':
                continue
            m.attrs['PixelSize']='6'
            parts=cues[m.name]
            source_peak=np.maximum.reduce(list(parts.values())) if parts else np.zeros(p.n)
            for part,values in list(parts.items()):
                values=np.asarray(values)
                parts[part]=np.where(values>0, .30+.70*np.sqrt(values), 0)
            # Separate nonmusical structure visibility from the actual scored
            # parts. It is off whenever this model has a source cue, so native
            # submodel compositing cannot overwrite an active note or chase.
            m.submodels['STRUCTURE_STANDBY']=list(range(1,len(m.points)+1))
            parts['STRUCTURE_STANDBY']=np.where(source_peak>0,0,.12)
        row = write_show(g, cues, root / f'shows/{level + 3:02d}_{g.slug}', audio, duration,
            dict(angleX=16, angleY=0 if level < 3 else 7,
                 distance=-170 if level < 3 else -460 if level < 5 else -590,
                 pany=-20 if level < 3 else -35, panz=0 if level < 3 else 15))
        row['spatial_score'] = proof
        row['pixel_structure_standby_level'] = .12
        row['pixel_activity_transfer'] = 'nonzero source cue -> .30 + .70 sqrt(level); original on/off intervals retained'
        if ac_parts:
            row['ac_standby_level'] = .12
            row['ac_visibility'] = 'native 6px bulb footprint; source activity above documented static standby'
        result.append(row)
        (root / 'progressive_generation.json').write_text(json.dumps(result, indent=2))
        print(row['title'], row['models'], row['channels'], row['effects'], flush=True)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    build(p.parse_args().root)
