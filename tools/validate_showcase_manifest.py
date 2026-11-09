#!/usr/bin/env python3
"""Compatibility entrypoint for the canonical six-video showcase batch validator.

Use tools/validate_showcase_batch.py for the implementation. This module deliberately
delegates rather than maintaining a second, inconsistent validation contract.
"""
from validate_showcase_batch import main, validate_manifest

if __name__ == "__main__":
    raise SystemExit(main())
