# Nine-panel v5 recovery check

Baseline evidence: integration commit `17980eb3b84d831dfda4c66d6499447fedd8c0dd` and `artifact_manifest.json`. Run on the existing render host with FFmpeg installed; pass the recovered full-length MP4 as argument 1 to the following shell block (save it as a script and invoke with Bash).

```bash
set -euo pipefail
video=${1:?Pass the recovered full-length v5 MP4}
printf '%s  %s\n' d3091e7553190f2d7eeb9f6e86319d62943732684c065dafffeff6ae58f03bf0 "$video" | sha256sum --check --strict -
ffprobe -v error -show_entries stream=codec_name,codec_type,width,height,avg_frame_rate,duration:format=duration,size -of json "$video"
ffmpeg -nostdin -v error -xerror -i "$video" -map 0:v:0 -map 0:a:0 -f null -
```

Expected probe: 1920x1080 H.264 at 30 fps, AAC audio, approximately 205.76 seconds, 88428458 bytes. Preserve the probe output and decode exit status. A missing artifact, digest mismatch, or decode failure blocks delivery. Success establishes file identity and decodability only: compare original audio synchronization, inspect all nine panel identities and the canonical six-member stage, and attach native XSQ/FSEQ provenance before requesting review. No check was run against the v5 bytes when drafting this checkpoint. No owner approval, device pass, batch authorization, or release is implied.
