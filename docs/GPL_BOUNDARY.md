# GPL Boundary Guidance

## Purpose

This document describes the intended interoperability boundary between Helix systems and GPL-covered software such as xLights.

## Intended Architecture

Helix is intended to operate primarily as:

- an orchestration layer
- automation framework
- sequencing assistant
- rendering coordinator
- Lua/script generation system
- analysis pipeline

rather than directly embedding GPL-covered application source code.

## Preferred Integration Methods

Preferred interoperability mechanisms include:

- XSQ interchange
- XML interchange
- external process invocation
- CLI workflows
- Lua scripting
- exported sequence files
- temporary runtime interoperability

## Avoid Where Possible

Avoid:

- static linking against GPL systems
- embedding GPL application source directly
- redistributing modified GPL binaries without full compliance review

## Important Reminder

This document is operational guidance only and not legal advice.

All distributions should independently validate:

- dependency obligations
- binary redistribution requirements
- codec licensing
- FFmpeg licensing
- GPL interoperability implications
