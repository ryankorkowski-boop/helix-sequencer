"""Archived feature-only V3 experiment, retained for legacy callers/tests.

Production consumers must use audio.drummer_v3. This adapter does not classify
production audio and must not grow independent thresholds.
"""
from audio.archive.drummer_v3_features import DrumType, Candidate, DrumEvent, analyze_drummer_features
