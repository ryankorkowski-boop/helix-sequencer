#!/usr/bin/env python3
"""Helix v28.1 legacy GUI adapter.

v28.1 is the first legacy-GUI exposure of the current Helix pipeline style lane.
It intentionally delegates to the shared variant engine instead of copying older
version logic.
"""

from variant_engine import main_for


if __name__ == "__main__":
    main_for("v28.1")
