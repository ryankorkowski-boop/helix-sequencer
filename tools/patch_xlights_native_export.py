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
FIELDS_NEW = FIELDS_OLD + """
        int m_exportWidth = 0;
        int m_exportHeight = 0;
        GLuint m_exportFramebuffer = 0;
        GLuint m_exportColor = 0;
        GLuint m_exportDepth = 0;
        GLint m_exportPreviousDraw = 0;
        GLint m_exportPreviousRead = 0;
        void releaseExportFramebuffer();"""
PREPARE_OLD = '    float r = bg.red;'
PREPARE_NEW = """    // Helix: a wx size event changes the projection cache, not the GL
    // drawable allocation. Bind the requested real render target before clear.
    if (m_exportWidth > 0 && m_exportHeight > 0) {
        if (!hasOpenGL3FramebufferObjects() || !IsCoreProfile()) {
            throw std::runtime_error("Helix native export requires OpenGL framebuffer support");
        }
        auto checkFramebuffer = wxGLCanvas::GetProcAddress<PFNGLCHECKFRAMEBUFFERSTATUSPROC>("glCheckFramebufferStatus");
        if (checkFramebuffer == nullptr) {
            throw std::runtime_error("Helix native export cannot verify its framebuffer");
        }
        glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING, &m_exportPreviousDraw);
        glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING, &m_exportPreviousRead);
        GLint previousRenderbuffer = 0;
        glGetIntegerv(GL_RENDERBUFFER_BINDING, &previousRenderbuffer);
        glGenFramebuffers(1, &m_exportFramebuffer);
        glBindFramebuffer(GL_FRAMEBUFFER, m_exportFramebuffer);
        glGenRenderbuffers(1, &m_exportColor);
        glBindRenderbuffer(GL_RENDERBUFFER, m_exportColor);
        glRenderbufferStorage(GL_RENDERBUFFER, GL_RGBA8, m_exportWidth, m_exportHeight);
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, m_exportColor);
        glGenRenderbuffers(1, &m_exportDepth);
        glBindRenderbuffer(GL_RENDERBUFFER, m_exportDepth);
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, m_exportWidth, m_exportHeight);
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, m_exportDepth);
        glBindRenderbuffer(GL_RENDERBUFFER, previousRenderbuffer);
        if (checkFramebuffer(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE) {
            releaseExportFramebuffer();
            throw std::runtime_error("Helix native export framebuffer is incomplete");
        }
        // A pending GUI resize must not change this source frame's projection.
        mWindowWidth = (size_t)(m_exportWidth / GetContentScaleFactor());
        mWindowHeight = (size_t)(m_exportHeight / GetContentScaleFactor());
    }

    float r = bg.red;"""
READBACK_OLD = '    // OpenGL has no zero-copy native surface; always fill the CPU RGB buffer.'
READBACK_NEW = """    // Helix: reject a skipped draw or a read from the window's small buffer.
    if (m_exportFramebuffer == 0 || frame.width != m_exportWidth || frame.height != m_exportHeight) {
        releaseExportFramebuffer();
        return false;
    }
    // OpenGL has no zero-copy native surface; always fill the CPU RGB buffer."""
RELEASE_OLD = '    return true;\n}\n\nbool xlGLCanvas::bindVertexArrayID'
RELEASE_NEW = """    releaseExportFramebuffer();
    return true;
}

void xlGLCanvas::captureNextFrame(int w, int h) {
    if (w <= 0 || h <= 0 || m_exportFramebuffer != 0) {
        throw std::runtime_error("Helix native export has invalid capture state");
    }
    m_exportWidth = w;
    m_exportHeight = h;
}

void xlGLCanvas::releaseExportFramebuffer() {
    if (m_exportFramebuffer != 0) {
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, m_exportPreviousDraw);
        glBindFramebuffer(GL_READ_FRAMEBUFFER, m_exportPreviousRead);
        glDeleteFramebuffers(1, &m_exportFramebuffer);
        glDeleteRenderbuffers(1, &m_exportColor);
        glDeleteRenderbuffers(1, &m_exportDepth);
        m_exportFramebuffer = m_exportColor = m_exportDepth = 0;
    }
    m_exportWidth = m_exportHeight = 0;
}

bool xlGLCanvas::bindVertexArrayID"""
NULL_OLD = '    if (buffer == nullptr) {\n        return false;\n    }'
NULL_NEW = '    if (buffer == nullptr) {\n        releaseExportFramebuffer();\n        return false;\n    }'
BOUNDS_OLD = '    if ((size_t)bufferSize < reqSize) {\n        return false;\n    }'
BOUNDS_NEW = '    if ((size_t)bufferSize < reqSize) {\n        releaseExportFramebuffer();\n        return false;\n    }'
INCLUDE_OLD = '#include <wx/log.h>'
INCLUDE_NEW = INCLUDE_OLD + '\n#include <stdexcept>'
PATCHES = {
    'src-ui-wx/xLightsMain.cpp': [(SIZE_OLD, SIZE_NEW)],
    'src-ui-wx/app-shell/TabSequence.cpp': [(CAMERA_OLD, CAMERA_NEW)],
    'src-ui-wx/graphics/opengl/xlGLCanvas.h': [(CAPTURE_OLD, CAPTURE_NEW), (FIELDS_OLD, FIELDS_NEW)],
    'src-ui-wx/graphics/opengl/xlGLCanvas.cpp': [(INCLUDE_OLD, INCLUDE_NEW), (PREPARE_OLD, PREPARE_NEW),
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
