# Open-Source Sequence Ruleset

## Corpus
- Files considered: 47
- Files parsed: 40
- Files with no model effects: 5
- Repos used: extra_sequence_root

## Top Effects (Global)
- On: count=27976 weight=0.76847 dur(p50)=400ms
- SingleStrand: count=3368 weight=0.09251 dur(p50)=500ms
- Curtain: count=1414 weight=0.03884 dur(p50)=525ms
- Spirals: count=627 weight=0.01722 dur(p50)=550ms
- Shockwave: count=615 weight=0.01689 dur(p50)=450ms
- Pictures: count=606 weight=0.01665 dur(p50)=525ms
- Marquee: count=432 weight=0.01187 dur(p50)=550ms
- Bars: count=254 weight=0.00698 dur(p50)=1350ms
- Wave: count=134 weight=0.00368 dur(p50)=1050ms
- Morph: count=120 weight=0.0033 dur(p50)=1025ms
- Butterfly: count=118 weight=0.00324 dur(p50)=2075ms
- Snowflakes: count=82 weight=0.00225 dur(p50)=1150ms

## Family Rules
- arch: avg_layers=1.211 multi_layer_rate=0.15789
  - SingleStrand (137, w=0.47241, p50=500ms)
  - On (82, w=0.28276, p50=400ms)
  - Curtain (46, w=0.15862, p50=525ms)
  - Shockwave (8, w=0.02759, p50=450ms)
  - Spirals (5, w=0.01724, p50=550ms)
- face: avg_layers=1.0 multi_layer_rate=0.0
  - On (1485, w=0.99198, p50=400ms)
  - SingleStrand (12, w=0.00802, p50=500ms)
- flood: avg_layers=1.018 multi_layer_rate=0.01198
  - On (992, w=0.91513, p50=400ms)
  - Bars (39, w=0.03598, p50=1350ms)
  - Butterfly (14, w=0.01292, p50=2075ms)
  - Curtain (12, w=0.01107, p50=525ms)
  - Plasma (6, w=0.00554, p50=1150ms)
- line_outline: avg_layers=1.092 multi_layer_rate=0.06338
  - On (3166, w=0.82771, p50=400ms)
  - Spirals (162, w=0.04235, p50=550ms)
  - Marquee (154, w=0.04026, p50=550ms)
  - SingleStrand (96, w=0.0251, p50=500ms)
  - Shockwave (95, w=0.02484, p50=450ms)
- matrix: avg_layers=1.0 multi_layer_rate=0.0
  - Text (1, w=0.25, p50=1525ms)
  - Pinwheel (1, w=0.25, p50=4000ms)
  - Fire (1, w=0.25, p50=2400ms)
  - Butterfly (1, w=0.25, p50=2075ms)
- mega_tree: avg_layers=1.063 multi_layer_rate=0.02586
  - On (12763, w=0.71246, p50=400ms)
  - SingleStrand (2800, w=0.1563, p50=500ms)
  - Curtain (801, w=0.04471, p50=525ms)
  - Pictures (606, w=0.03383, p50=525ms)
  - Shockwave (297, w=0.01658, p50=450ms)
- other: avg_layers=1.025 multi_layer_rate=0.01757
  - On (9094, w=0.80067, p50=400ms)
  - Curtain (514, w=0.04525, p50=525ms)
  - Spirals (412, w=0.03627, p50=550ms)
  - SingleStrand (320, w=0.02817, p50=500ms)
  - Marquee (244, w=0.02148, p50=550ms)
- star_snowflake: avg_layers=1.034 multi_layer_rate=0.03448
  - On (394, w=0.90993, p50=400ms)
  - Marquee (27, w=0.06236, p50=550ms)
  - Fill (12, w=0.02771, p50=1600ms)

## Transition Rules
- On -> On: count=26656 confidence=0.97324
- SingleStrand -> SingleStrand: count=2906 confidence=0.87901
- Curtain -> Curtain: count=1037 confidence=0.7482
- Pictures -> Pictures: count=592 confidence=0.98176
- Spirals -> Spirals: count=524 confidence=0.8438
- Marquee -> Marquee: count=366 confidence=0.85514
- SingleStrand -> On: count=352 confidence=0.10647
- On -> SingleStrand: count=343 confidence=0.01252
- Shockwave -> Shockwave: count=295 confidence=0.48361
- Curtain -> Shockwave: count=230 confidence=0.16595
- Shockwave -> Curtain: count=207 confidence=0.33934
- Bars -> Bars: count=110 confidence=0.44

## General Rules
- Prefer high-support effects first, then diversify with low-weight accents.
- Follow common effect-pair transitions to keep phrase continuity.
- Treat channel-render-only files as timing references, not prop-effect exemplars.
