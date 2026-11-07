"""Build a standalone artistic Helix Aurora show and portable review bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from models.ultimate_showcase import build_ultimate_garden
from tools.build_helpers.ultimate_showcase import write_layout
from tools.build_helpers.ultimate_showcase_preview import write_previews


def package_showcase(output: Path) -> Path:
    """Package only portable deliverables, excluding xLights caches/backups."""
    slug=json.loads((output/"showcase_manifest.json").read_text()).get("file_prefix","Helix_Aurora")
    required = ["xlights_rgbeffects.xml", "xlights_networks.xml", slug+"_Showcase.xsq",
                "README.txt", "showcase_manifest.json", "model_inventory.csv"]
    optional = [slug+"_Night.png", slug+"_Perspective.png", slug+"_3D.html",
                slug+"_Showcase.mp4", slug+"_Showcase.fseq", "preview_geometry.json",
                "BUILD_SUMMARY.json", "native_verification.json", "native_model_attributes.json",
                "VALIDATION.md", "native_gui_layout.png"]
    paths = [output / name for name in required]
    for p in paths:
        if not p.is_file() or not p.stat().st_size:
            raise ValueError(f"Missing showcase deliverable: {p.name}")
    paths += [output / name for name in optional if (output / name).is_file()]
    for folder in ("assets", "models", "review_frames"):
        paths += [p for p in (output / folder).rglob("*") if p.is_file()]
    paths = sorted(paths)
    checksums = output / "bundle_checksums.json"
    checksums.write_text(json.dumps({p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in paths}, indent=2) + "\n", encoding="utf-8")
    bundle = output.parent / (slug+"_Ultimate_Showcase.zip")
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(paths + [checksums]):
            archive.write(p, Path(slug) / p.relative_to(output))
    return bundle


def build_showcase(output: Path, *, video: bool = True, fseq: Path | None = None,
                   zip_bundle: bool = True) -> dict:
    g=build_ultimate_garden()
    manifest=write_layout(g,output)
    preview=write_previews(g,output,video=video,fseq=fseq)
    summary={"models":manifest["model_count"],"groups":manifest["group_count"],"native_families":len(manifest["native_families"]),
             "spiral_trees":manifest["spiral_trees"],"double_helices":manifest["double_helices"],"rgb_pixels":manifest["rgb_pixels"],
             "channels":manifest["channel_count"],**preview}
    (output/"BUILD_SUMMARY.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    if zip_bundle:
        summary["bundle"]=str(package_showcase(output))
    return summary


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=Path("outputs/ultimate_showcase/Helix_Aurora"))
    parser.add_argument("--no-video",action="store_true",help="Build XML, models, PNGs and interactive viewer only")
    parser.add_argument("--native-fseq",type=Path,help="Use actual xLights rendered channel values for the MP4")
    parser.add_argument("--no-zip",action="store_true")
    parser.add_argument("--package-only",action="store_true",help="Refresh checksums and ZIP after native validation; do not rebuild previews")
    args=parser.parse_args()
    if args.package_only:
        print(json.dumps({"bundle":str(package_showcase(args.output))},indent=2))
    else:
        print(json.dumps(build_showcase(args.output,video=not args.no_video,fseq=args.native_fseq,zip_bundle=not args.no_zip),indent=2))


if __name__=="__main__":main()
