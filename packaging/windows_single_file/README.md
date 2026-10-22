# Single-download Windows beta

Open `Helix-Sequencer-Beta.exe`. It contains the full portable Helix runtime,
including Python, numerical libraries, FFmpeg and the engine worker. No separate
Python installation or administrator account is required.

The launcher expands its payload into a persistent per-user folder under
`%LOCALAPPDATA%\HelixSequencer\beta-runtime\<runtime-source-commit>` and starts
Helix. Later launches reuse that version's runtime. Generated sequences are kept
in the output folder shown in the GUI; choose another folder there if preferred.

The build verifies the upstream portable archive, embedded source identity,
executable and guide hashes, then tests the extracted GUI and worker on Windows.
The receipt records the runtime source separately from this launcher's source.
An executable is offered for review only after these checks pass. It does not
establish musical, physical-controller or owner release approval.

The launcher is built with [NSIS](https://nsis.sourceforge.io/), separately from
the unchanged Helix runtime and its bundled license notices.
