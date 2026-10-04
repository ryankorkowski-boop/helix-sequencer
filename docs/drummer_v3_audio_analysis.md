# Drummer V3 Audio Analysis

The Drummer V3 pipeline uses a conservative multi-detector analysis architecture designed to distinguish genuine drum activity from transients produced by other instruments.

## Event rule

A full-mix transient is never sufficient to create a drummer event. Drum-stem or percussive-stem evidence must establish the event first; full-mix evidence may only corroborate it.

Events are clustered from independent detector families and assigned typed targets: kick, snare, hi-hat, cymbal-left, cymbal-right, tom-high, tom-mid, and tom-floor.

## False-positive protection

- Guitar, piano, vocal, and general-mix onsets cannot directly create drum events.
- Weak or conflicting detector evidence is rejected rather than converted into a fallback bus event.
- Beat position supplies timing context only; it cannot manufacture a hit.
- Adaptive thresholds are calculated from the analyzed drum/percussive material rather than the full mix.
- The three tom targets are strictly HIGH, MID, and FLOOR.

## Canonical visual target

The analyzer must feed the asset-first `HX_SNOWMAN_DRUMMER_V3` performer and its approved V3 pose specification. The visual source and model are not interchangeable with the generic legacy drummer renderer.

## Required regression

The test suite must include a guitar-transient-only fixture and assert zero drummer events when drum/percussive evidence is absent.
