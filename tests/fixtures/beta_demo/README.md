# Clean-Room Beta Demo Fixture

This directory contains tiny repo-safe inputs for beta smoke checks.

The files here are intentionally minimal. They exist to prove that the beta fixture plumbing, XML parsing, and smoke scripts work without relying on private tester assets or copyrighted songs.

## Files

- `generate_synthetic_audio.py` — writes a short synthetic WAV using only the Python standard library.
- `minimal_layout.xml` — tiny xLights-style layout XML fixture.
- `minimal_template.xsq` — tiny xLights-style sequence/template XML fixture.

## Asset policy

Do not commit private layouts, real show sequences, copyrighted songs, tester screenshots, generated user outputs, or customer-provided material here.

Use only generated, synthetic, public-domain, or explicitly permissioned files. When in doubt, generate the fixture from source code and document that it is clean-room material.

## Scope

This fixture does not prove xLights visual quality, controller/channel safety, or production readiness. Those claims require separate artifact evidence and manual xLights validation.
