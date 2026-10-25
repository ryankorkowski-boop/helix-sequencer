"""Apply bounded fixes to the exact pinned xLights 2026.18 source.

No video postprocessing: repair native export dimensions and startup camera
initialization. Refuse unexpected source so a tag change cannot silently drift.
"""
from __future__ import annotations
import argparse
from pathlib import Path

SIZE_OLD = '    int width = housePreview->getWidth();\n    int height = housePreview->getHeight();'
SIZE_NEW = '''    // Helix: commit the viewport cache before frame zero. SetSize on wxGTK
    // queues the size event, while the export loop can render its first frames
    // before the next progress-dialog yield. Encoder dimensions alone do not
    // update xlGLCanvas::mWindowWidth/mWindowHeight used by ModelPreview.
    if (resizedForExport) {
        wxSize exportViewport((int)(desiredWidth / contentScaleFactor), (int)(desiredHeight / contentScaleFactor));
        wxSizeEvent exportSizeEvent(exportViewport, housePreview->GetId());
        exportSizeEvent.SetEventObject(housePreview);
        housePreview->GetEventHandler()->ProcessEvent(exportSizeEvent);
    }
    // Helix: use requested native dimensions before wxGTK's pending size event.
    int width = resizedForExport ? (int)(desiredWidth / contentScaleFactor) : housePreview->getWidth();
    int height = resizedForExport ? (int)(desiredHeight / contentScaleFactor) : housePreview->getHeight();'''
CAMERA_OLD = '''    modelPreview->Set3D(is_3d);
    _housePreviewPanel->Set3d(is_3d);
    layoutPanel->Set3d(is_3d);
'''
CAMERA_NEW = CAMERA_OLD + '''    // Helix: LoadEffectsFile restored cameras before selecting the show's
    // dimension mode. On a fresh profile that restores 2D and leaves the 3D
    // camera at its -2000 default instead of the authored close-up viewpoint.
    modelPreview->RestoreDefaultCameraPosition();
    _housePreviewPanel->GetModelPreview()->RestoreDefaultCameraPosition();
    spdlog::info("Helix native preview: restored saved camera after mode selection (3D={})", is_3d);
'''


def patched(source: str, before: str, after: str) -> str:
    if source.count(before) != 1 or after in source:
        raise ValueError('Pinned xLights patch site absent, ambiguous or already modified')
    return source.replace(before, after, 1)


def apply(root: Path) -> None:
    paths = {root / 'src-ui-wx/xLightsMain.cpp': (SIZE_OLD, SIZE_NEW),
             root / 'src-ui-wx/app-shell/TabSequence.cpp': (CAMERA_OLD, CAMERA_NEW)}
    # Validate both sites before modifying either file.
    updates = {path: patched(path.read_text(), *replacement)
               for path, replacement in paths.items()}
    for path, content in updates.items():
        path.write_text(content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    apply(parser.parse_args().source)
