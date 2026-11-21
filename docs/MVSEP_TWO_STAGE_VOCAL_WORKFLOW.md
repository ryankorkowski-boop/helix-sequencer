# Two-stage vocal separation for Helix Beta 1.4

## Why

MVSep's karaoke approach separates the combined vocal material from instruments
before separating lead from backing vocals. This is a useful architectural
pattern, **not** evidence that a particular voice has been identified. Helix
continues to run offline and never uploads audio automatically.

Reference: https://www.mvsep.com/en/algorithms
API reference (optional future cloud adapter): https://www.mvsep.com/en/full_api

## Current implemented integration

An upstream tool (local or separately authorized cloud service) may produce
lead and backing **mono 16-bit PCM WAV** stems. For the two-stage route,
produce a JSON manifest beside the stem files:

```json
{
  "schema": "helix.vocal-separation.v1",
  "method": "vocals_first_then_lead_backing",
  "source_sha256": "<SHA256 of original audio bytes>",
  "lead": {"path": "lead.wav", "sha256": "<SHA256>"},
  "backing": {"path": "backing.wav", "sha256": "<SHA256>"}
}
```

Set `HELIX_VOCAL_SEPARATION_MANIFEST=/path/to/stems.json` for the Helix
audio-analysis process. This is mutually exclusive with the existing
`HELIX_LEAD_VOCAL_STEM` and `HELIX_HARMONY_VOCAL_STEM` overrides.

Helix verifies original-audio and stem hashes, prevents path traversal,
rejects duplicate, gain-scaled, silent or duration-mismatched stems through
`analyze_independent_vocals`, and routes separate activity to lead and
harmony performers. **Neither a manifest nor a separation model alone
authenticates singer identity, phonemes, or visual acceptance.**

## Future benchmark and production gates

- Compare vocals-first separation against current Demucs plus Helix on
  consented original excerpts with independently labeled singer activity.
- Quantify bleed, false harmony activations, singer timing, phoneme accuracy,
  processing cost, and real native band motion.
- Consider MVSep only as an explicit opt-in cloud provider; discover algorithm
  IDs/options dynamically from `/api/app/algorithms` rather than hardcoding.
  The documented API submits to `/api/separation/create` and polls
  `/api/separation/get`; it is **not yet wired into Helix**.
- Never put API tokens in logs or the repository; require upload consent and
  account for service licensing, data retention, and provider availability.
- Preserve local fallback, native xLights acceptance and owner review gates.

## Prepare the manifest locally

After obtaining separate mono 16-bit PCM WAV singer stems using a two-stage
separator, put them in the same directory as the manifest and run:

```bash
python -m tools.prepare_vocal_separation_manifest original.wav stems/lead.wav stems/backing.wav --output stems/separation.json
HELIX_VOCAL_SEPARATION_MANIFEST=stems/separation.json python -m pytest tests/test_vocal_separation_manifest.py -q
```

The second command is a smoke test for the manifest integration, **not** a
render or singer-identity acceptance test. The preparation tool validates
stem independence before publishing the manifest and rejects out-of-directory
paths. No provider is called and no original media is uploaded.
