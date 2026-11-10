# Wadena Video Frame Calibration — 2026-09-01

## Source

Local supplied recording: `XRecorder_20260901_06.mp4`

Measured media properties:

- Video duration: ~230.514 s
- Audio duration: ~230.644 s
- Video: 720×1568 portrait H.264, ~31.174 fps
- Audio: mono AAC, 44.1 kHz
- Video frames: 7,186
- The recording ends with the Android screen/recorder UI; the usable exterior-light scene ends before the final UI frames.

This is direct frame evidence from the supplied recording. It is stronger than the previously available YouTube URL for timing/visual calibration.

## What is directly observable

### 1. The show has long-lived infrastructure layers

Across the recording, major architectural/perimeter elements remain present while their color/intensity state changes. The display does not behave like independent random model selection. This supports the existing calibration rule that global infrastructure should be coherent while smaller elements provide phrase-level punctuation.

### 2. Large spatial color fields change as groups

Representative transitions are visible around approximately 37–38 s, 56–60 s, 78–85 s, and 154–162 s. These are camera-level observations of large visual-state changes, not claims about individual channel timing.

The 56–60 s transition is particularly useful: the visible scene changes from a mostly cool/white state into a stronger green/red mixed state across multiple physical regions. That is evidence for treating color as a compositional layer over an existing spatial gesture rather than selecting color independently for every prop.

### 3. There are deliberate low-activity / reset states

Around 79–82 s the visible display becomes substantially quieter/darker before activity returns. This is important: the renderer must be able to create negative space. A continuously active baseline is not an adequate model of the observed show language.

### 4. Hero/perimeter elements remain structurally important

The large circular/central element, large tree structures, roof/house outline, and repeated vertical tree/candy-cane-like elements remain visually legible even as their states change. The spatial graph should therefore distinguish hero, infrastructure, impact, and punctuation roles rather than flattening every model into one pool.

### 5. The recording is not the same clock length as the supplied professional LMS

The supplied recording is ~230.5 s. The professional Nutrocker LMS previously measured ~246.93 s. Therefore there is no defensible 1:1 timestamp mapping without finding a synchronization point and determining whether the recording is a different edit, cropped sequence, or a different performance/version.

Do not apply a simple duration-based time stretch to align them.

## Candidate synchronization methodology

When a matching audio/edit is established, use multiple anchors rather than one global stretch:

1. detect strong visual transitions in the recording;
2. detect corresponding musical onsets/section boundaries in the video audio;
3. compare against the LMS's persistent/sectional channel families;
4. accept a mapping only when several independent landmarks agree;
5. record uncertainty intervals when the visual recording cannot identify a specific prop/channel.

## Engineering consequences

The video evidence strengthens the following Helix architecture:

```text
acoustic feature
    -> event / phrase
    -> spatial gesture
    -> named physical landmark route
    -> role-aware participation
    -> AC-safe effect intent
    -> existing channel/effect compiler
    -> XSQ
```

The spatial layer should support at least:

- `left_to_right`
- `right_to_left`
- `center_out`
- `out_to_center`
- `bottom_up`
- `impact_propagation`
- `quiet/reset`

and should support persistent background fields independently of transient gesture events.

## Evidence vs inference

**Direct evidence:** frame-level visual state changes, long-lived structural elements, low-activity/reset periods, and the measured recording duration/media properties.

**Inference:** exact named physical landmark correspondence, exact electrical channels, and exact musical causes of individual visual changes. Those require synchronized source material or additional metadata and must not be presented as observed facts yet.

## Next calibration target

Use the recording's audio and frame sequence to construct a machine-readable event table containing:

- video timestamp
- visual activity score
- horizontal activity centroid
- left/center/right activity ratios
- dominant visible color family
- transition magnitude
- confidence
- human-readable observation label

This table can then become the visual calibration fixture for deterministic Wadena spatial-intent tests without encoding guessed channel numbers.
