"""Mapped AC dual export for newly generated XSQs; never infer LOR wiring."""
from __future__ import annotations
import json
import hashlib
from pathlib import Path
import shutil
import tempfile

from tools.ac_on_export import inventory_layout
from tools.legacy_lms_export import export_legacy_lms, read_lor_map

DUAL_MAP_FLAG = '--helix-dual-channel-map'


def validate_mapping(layout: Path, mapping_csv: Path) -> str:
    models, _groups, _rejected = inventory_layout(layout)
    mapping_bytes = Path(mapping_csv).read_bytes()
    with tempfile.TemporaryDirectory(prefix='helix-map-check-') as directory:
        snapshot = Path(directory) / 'mapping.csv'
        snapshot.write_bytes(mapping_bytes)
        mapping = read_lor_map(snapshot)
    if set(mapping) != set(models):
        raise ValueError('Dual export CSV must map every eligible AC layout model exactly once')
    for name, model in models.items():
        if any(mapping[name][key] != model[key] for key in ('color', 'start_channel')):
            raise ValueError(f'Dual export CSV differs from layout color/StartChannel for {name}')
    return hashlib.sha256(mapping_bytes).hexdigest()


def export_lms_siblings(sequences: list[Path], mapping_csv: Path, *,
                        expected_mapping_sha256: str | None = None) -> list[Path]:
    """Keep generated XSQs and atomically publish their mapped LMS siblings.

    Stage every conversion first, then use exclusive creates. On any failure,
    remove only files created here; never delete or overwrite preexisting data.
    """
    sources = [Path(p) for p in sequences]
    if not sources or len({p.resolve() for p in sources}) != len(sources):
        raise ValueError('Dual export requires distinct newly generated XSQs')
    targets = [(p.with_suffix('.lms'), p.with_suffix('.lms_validation.json')) for p in sources]
    for pair in targets:
        for path in pair:
            if path.exists():
                raise FileExistsError(f'Dual export output already exists: {path}')
    mapping_bytes = Path(mapping_csv).read_bytes()
    mapping_digest = hashlib.sha256(mapping_bytes).hexdigest()
    if expected_mapping_sha256 is not None and mapping_digest != expected_mapping_sha256:
        raise ValueError('Controller mapping changed since preflight; verify it and start a new run')
    created: list[Path] = []
    try:
        with tempfile.TemporaryDirectory(prefix='helix-dual-') as directory:
            frozen_map = Path(directory) / 'mapping.csv'
            frozen_map.write_bytes(mapping_bytes)
            read_lor_map(frozen_map)
            staged = []
            for index, (source, pair) in enumerate(zip(sources, targets)):
                temporary = Path(directory) / f'{index}.lms'
                report = export_legacy_lms(source, frozen_map, temporary)
                report['output'] = str(pair[0])
                report['mapping_csv'] = str(mapping_csv)
                report['mapping_sha256'] = mapping_digest
                report['input_xsq_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
                sidecar = temporary.with_suffix('.lms_validation.json')
                sidecar.write_text(json.dumps(report, indent=2) + '\n')
                staged.extend(zip((temporary, sidecar), pair))
            for temporary, target in staged:
                with target.open('xb') as output:
                    created.append(target)
                    with temporary.open('rb') as source:
                        shutil.copyfileobj(source, output)
    except Exception:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        raise
    return created
