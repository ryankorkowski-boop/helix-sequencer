# Birdsong Engine Mode

Birdsong Engine Mode is a dedicated analysis/export path that turns a song into a 3D motion sculpture first, then emits dynamic prop/effect scoring data.

## Run

```powershell
python main.py --birdsong-mode --birdsong-audio path/to/song.wav
```

Optional flags:

```powershell
python main.py --birdsong-mode --birdsong-audio path/to/song.wav --birdsong-use-umap --birdsong-use-basic-pitch --birdsong-output-dir outputs/birdsong --birdsong-no-preview
```

## Outputs

For `song.wav`, Birdsong Mode writes:

- `song.birdsong.json`
- `song.birdsong.features.csv`
- `song.birdsong.mapping.json`
- `song.birdsong.trajectory.ply` (unless `--birdsong-no-ply`)
- `song.birdsong.preview.html` (unless `--birdsong-no-preview`)

## What Is Computed

- MFCC + MFCC delta features
- Spectral centroid, bandwidth, and contrast
- Pitch contour + confidence (librosa, optional Spotify Basic Pitch if installed)
- Onset strength + onset timing
- Tempo + beat grid
- Rhythm density, rhythm stability, syncopation estimate
- PCA (required), optional UMAP if installed
- 2D and 3D embeddings
- 3D trajectory point cloud
- Rule-based dynamic prop/effect candidate scoring for:
  - megatrees
  - matrices
  - arches
  - singing faces
  - AC channels
  - snowman band
  - camera-path behavior

## Design Notes

- Core Birdsong path is open-source and local-audio only.
- Optional dependencies are soft-fail:
  - Basic Pitch (`basic_pitch.inference`)
  - UMAP (`umap`)
- Existing sequencing flow is unchanged; Birdsong Mode is an additive path.
