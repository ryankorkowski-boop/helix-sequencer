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


# OpenGL capture was a no-op upstream: requested encoder/cache dimensions do
# not resize the drawable. Use a real offscreen color/depth target per source
# frame, before clearing/drawing, and read that same target without a swap.
CAPTURE_OLD = '        void captureNextFrame(int w, int h) {}'
CAPTURE_NEW = '        void captureNextFrame(int w, int h);'
FIELDS_OLD = '        size_t m_exportReadbackBufferSize = 0;'
FIELDS_NEW = FIELDS_OLD + "\n        void releaseExportFramebuffer();"
PREPARE_OLD = '    float r = bg.red;'
PREPARE_NEW = """    // Helix: a wx size event changes the projection cache, not the GL
    // drawable allocation. Bind the requested real render target before clear.
    auto capture = helixExportTargets.find(this);
    if (capture != helixExportTargets.end()) {
        auto& exportTarget = capture->second;
        if (!hasOpenGL3FramebufferObjects() || !IsCoreProfile()) {
            throw std::runtime_error("Helix native export requires OpenGL framebuffer support");
        }
        auto checkFramebuffer = wxGLContext::GetProcAddress<PFNGLCHECKFRAMEBUFFERSTATUSPROC>("glCheckFramebufferStatus");
        if (checkFramebuffer == nullptr) {
            throw std::runtime_error("Helix native export cannot verify its framebuffer");
        }
        glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING, &exportTarget.previousDraw);
        glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING, &exportTarget.previousRead);
        GLint previousRenderbuffer = 0;
        glGetIntegerv(GL_RENDERBUFFER_BINDING, &previousRenderbuffer);
        glGenFramebuffers(1, &exportTarget.framebuffer);
        glBindFramebuffer(GL_FRAMEBUFFER, exportTarget.framebuffer);
        glGenRenderbuffers(1, &exportTarget.color);
        glBindRenderbuffer(GL_RENDERBUFFER, exportTarget.color);
        glRenderbufferStorage(GL_RENDERBUFFER, GL_RGBA8, exportTarget.width, exportTarget.height);
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, exportTarget.color);
        glGenRenderbuffers(1, &exportTarget.depth);
        glBindRenderbuffer(GL_RENDERBUFFER, exportTarget.depth);
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, exportTarget.width, exportTarget.height);
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, exportTarget.depth);
        glBindRenderbuffer(GL_RENDERBUFFER, previousRenderbuffer);
        if (checkFramebuffer(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE) {
            releaseExportFramebuffer();
            throw std::runtime_error("Helix native export framebuffer is incomplete");
        }
        // A pending GUI resize must not change this source frame's projection.
        mWindowWidth = (size_t)(exportTarget.width / GetContentScaleFactor());
        mWindowHeight = (size_t)(exportTarget.height / GetContentScaleFactor());
    }

    float r = bg.red;"""
READBACK_OLD = '    // OpenGL has no zero-copy native surface; always fill the CPU RGB buffer.'
READBACK_NEW = """    // Helix: reject a skipped draw or a read from the window's small buffer.
    auto capture = helixExportTargets.find(this);
    if (capture == helixExportTargets.end()) return false;
    auto& exportTarget = capture->second;
    if (exportTarget.framebuffer == 0 || frame.width != exportTarget.width || frame.height != exportTarget.height) {
        releaseExportFramebuffer();
        return false;
    }
    // OpenGL has no zero-copy native surface; always fill the CPU RGB buffer."""
RELEASE_OLD = '    return true;\n}\n\nbool xlGLCanvas::bindVertexArrayID'
RELEASE_NEW = """    releaseExportFramebuffer();
    return true;
}

void xlGLCanvas::captureNextFrame(int w, int h) {
    auto& exportTarget = helixExportTargets[this];
    if (w <= 0 || h <= 0 || exportTarget.framebuffer != 0) {
        throw std::runtime_error("Helix native export has invalid capture state");
    }
    exportTarget.width = w;
    exportTarget.height = h;
}

void xlGLCanvas::releaseExportFramebuffer() {
    auto capture = helixExportTargets.find(this);
    if (capture == helixExportTargets.end()) return;
    auto& exportTarget = capture->second;
    if (exportTarget.framebuffer != 0) {
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, exportTarget.previousDraw);
        glBindFramebuffer(GL_READ_FRAMEBUFFER, exportTarget.previousRead);
        glDeleteFramebuffers(1, &exportTarget.framebuffer);
        glDeleteRenderbuffers(1, &exportTarget.color);
        glDeleteRenderbuffers(1, &exportTarget.depth);
        exportTarget.framebuffer = exportTarget.color = exportTarget.depth = 0;
    }
    helixExportTargets.erase(capture);
}

bool xlGLCanvas::bindVertexArrayID"""
NULL_OLD = '    if (buffer == nullptr) {\n        return false;\n    }'
NULL_NEW = '    if (buffer == nullptr) {\n        releaseExportFramebuffer();\n        return false;\n    }'
BOUNDS_OLD = '    if ((size_t)bufferSize < reqSize) {\n        return false;\n    }'
BOUNDS_NEW = '    if ((size_t)bufferSize < reqSize) {\n        releaseExportFramebuffer();\n        return false;\n    }'
INCLUDE_OLD = '#include <wx/log.h>'
INCLUDE_NEW = INCLUDE_OLD + '\n#include <stdexcept>'
STATE_DECL_OLD = 'void xlGLCanvas::DisplayWarning(const wxString& msg)'
STATE_DECL_NEW = """// Helix export state lives outside the canvas: preserve its ABI for cached
// derived classes. Entries exist only between captureNextFrame and readback.
namespace {
struct HelixExportTarget {
    int width = 0, height = 0;
    GLuint framebuffer = 0, color = 0, depth = 0;
    GLint previousDraw = 0, previousRead = 0;
};
std::map<xlGLCanvas*, HelixExportTarget> helixExportTargets;
}

void xlGLCanvas::DisplayWarning(const wxString& msg)"""
PATCHES = {
    'src-ui-wx/xLightsMain.cpp': [(SIZE_OLD, SIZE_NEW)],
    'src-ui-wx/app-shell/TabSequence.cpp': [(CAMERA_OLD, CAMERA_NEW)],
    'src-ui-wx/graphics/opengl/xlGLCanvas.h': [(CAPTURE_OLD, CAPTURE_NEW), (FIELDS_OLD, FIELDS_NEW)],
    'src-ui-wx/graphics/opengl/xlGLCanvas.cpp': [(INCLUDE_OLD, INCLUDE_NEW), (STATE_DECL_OLD, STATE_DECL_NEW), (PREPARE_OLD, PREPARE_NEW),
        (READBACK_OLD, READBACK_NEW), (NULL_OLD, NULL_NEW),
        (BOUNDS_OLD, BOUNDS_NEW), (RELEASE_OLD, RELEASE_NEW)],
}


def patched(source: str, before: str, after: str) -> str:
    if source.count(before) != 1 or after in source:
        raise ValueError('Pinned xLights patch site absent, ambiguous or already modified')
    return source.replace(before, after, 1)


def apply(root: Path) -> None:
    # Validate every site before changing any source file.
    updates = {}
    for relative, replacements in PATCHES.items():
        path = root / relative
        content = path.read_text()
        for before, after in replacements:
            content = patched(content, before, after)
        updates[path] = content
    for path, content in updates.items():
        path.write_text(content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    apply(parser.parse_args().source)
