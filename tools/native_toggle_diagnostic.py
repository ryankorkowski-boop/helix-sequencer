"""Compare actual native outputs; never silently replace a failed panel."""
from pathlib import Path
import json
import os
import subprocess
from tools.native_preview import preview_run
from tools.render_approval_collection import comparison
from tools.verify_recovery_media import verify

def main():
    root = Path("toggle-review").resolve()
    audio = root / "media/review.wav"
    manifest = root / "comparison.json"
    data = json.loads(manifest.read_text())
    titles = ["Current defaults", "Flow/Birdsong off", "Matrix intelligence off", "Both off"]
    movies = []
    for row in data["runs"]:
        folder = root / row["name"]
        receipt = preview_run(folder, xsq=folder / "review.xsq", audio=audio,
                              xlights=os.environ["HELIX_PATCHED_XLIGHTS"])
        row["native"] = receipt
        manifest.write_text(json.dumps(data, indent=2))
        if receipt["status"] != "success":
            raise RuntimeError(str(receipt["warnings"]))
        movies.append(Path(receipt["mp4"]))
    if len(movies) != 4:
        raise RuntimeError("Four actual native movies required")
    output = root / "Engine_Toggle_Diagnostic.mp4"
    comparison(movies, titles, output, audio, 2, 2, duration=20)
    subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(output),
                    "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"], check=True)
    data["media_verification"] = verify(output, audio, data["source_audio_sha256"])
    data["distinct_native_outputs"] = len({r["native"]["native_fseq_sha256"] for r in data["runs"]})
    data["status"] = "diagnostic_rendered_not_approved"
    manifest.write_text(json.dumps(data, indent=2))
if __name__ == "__main__":
    main()
