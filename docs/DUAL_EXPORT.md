# XSQ and legacy Light-O-Rama output from one build

Choose **Both** in the desktop GUI, select your audio, xLights layout and template, then run the build. Select a controller mapping CSV when prompted. Both uses the explicit red/green/white AC On-only export path. Each generated XSQ keeps its own name and receives a matching `.lms` plus `.lms_validation.json` in the same folder. The selected layout and audio are packaged alongside the files.

For a source checkout:

```bash
python main.py --profile master -- --audio song.wav --template template.xsq --layout-file layout.xml --output-dir outputs --helix-dual-channel-map verified_mapping.csv --no-prompt
```

The CSV columns are:

```csv
model,color,controller_unit,controller_circuit,xlights_start_channel
```

Use the exact eligible single-color model names, colors (`red`, `green`, `white`) and numeric xLights start channels from the selected layout. Enter the actual controller Unit ID and circuit from your wiring. Unit IDs accept decimal or `0x` hexadecimal values from 1 to 255; circuits are 1 through 16. Every eligible AC model must appear exactly once. The build checks names, colors, start channels and duplicate controller addresses before analysis. It does not infer controller wiring.

The LMS converter preserves the On event intervals at legacy centisecond resolution. It exports constant full-intensity AC effects, not RGB pixels, fades or modern `.loredit` files. Normal XSQ output remains available for pixel and mixed layouts. This integration does not establish that a particular LOR application or physical controller has accepted the file; those checks remain release gates.

Conversion stages every new LMS before publishing any. Existing LMS files or validation sidecars cause a failure. On conversion or publication failure, files created by this conversion are rolled back and existing files are preserved; the generated XSQ remains available and the run is reported unsuccessful.

Desktop portable builds use the normal bundled CLI for this path. The separate **Export existing AC XSQ + LMS** action remains a source-checkout utility; use **Both** in Run Sequence Build for the packaged workflow. Android's current interface still offers separate xLights and LOR modes; this desktop selector does not add an Android Both control.
