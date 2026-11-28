"""Validate authenticated V4 ZIP before native integration. Usage: python tools/validate_infinity_v4.py ZIP."""
import csv, hashlib, io, json, math, struct, sys, zipfile
from pathlib import Path

def validate(path):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == "8a4f994977c95543e6d726f3272f46634aec72ca764d2052961ef00e06a39427", "Unexpected asset hash"
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        m = json.loads(z.read("Infinity_V4_manifest.json"))
        rows = list(csv.DictReader(io.StringIO(z.read("Infinity_V4_Channel_Map.csv").decode())))
        glb = z.read("Infinity_V4_Double_Helix.glb")
    assert struct.unpack_from("<4sII", glb) == (b"glTF", 2, len(glb))
    assert len(rows) == m["pixels"] == 12472
    assert len({r["model"] for r in rows}) == m["models"] == 114
    assert len({(r["model"],r["node"]) for r in rows}) == len(rows)
    channels = [int(r[k]) for r in rows for k in ("red_channel","green_channel","blue_channel")]
    assert sorted(channels) == list(range(1,37417))
    assert all(math.isfinite(float(r[k])) for r in rows for k in ("x_m","y_m","z_m"))
    assert m["track_turns"] == 20 and m["track_rungs"] == 80
    return {"asset_intake":"pass","pixels":len(rows),"channels":len(channels),"native_verified":False,"owner_approved":False}

if __name__ == "__main__":
    print(json.dumps(validate(Path(sys.argv[1])),indent=2))
