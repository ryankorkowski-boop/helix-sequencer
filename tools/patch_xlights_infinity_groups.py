"""Load dense model groups in one batch on pinned xLights 2026.18."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

from tools.native_renderer_bundle import UPSTREAM_COMMIT
from tools.patch_xlights_native_export import patched


SOURCE = 'src-core/XmlSerializer/XmlDeserializingModelFactory.cpp'
ORIGINAL = '''        for (const auto& modelName : modelNames) {
            if (!modelName.empty()) {
                model->AddModel(modelName);
            }
        }
'''
BATCH = '''        // Preserve AddModel's trimmed, first-occurrence member order, but
        // populate and resolve the complete group once instead of once per member.
        std::set<std::string> seen;
        std::vector<std::string> orderedNames;
        orderedNames.reserve(modelNames.size());
        for (const auto& modelName : modelNames) {
            if (!modelName.empty()) {
                auto name = Trim(modelName);
                if (seen.insert(name).second) {
                    orderedNames.push_back(std::move(name));
                }
            }
        }
        model->SetModels(orderedNames);
'''


def apply(source: Path) -> None:
    commit = subprocess.check_output(
        ['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if commit != UPSTREAM_COMMIT:
        raise ValueError('Dense group patch requires the pinned upstream xLights source')
    path = source / SOURCE
    path.write_text(patched(path.read_text(), ORIGINAL, BATCH))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    apply(parser.parse_args().source)
