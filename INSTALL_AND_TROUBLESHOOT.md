# Install and use Helix Beta v1.0

## Windows

Extract the entire portable Windows folder. Keep Helix.exe, HelixCLI.exe and _internal together. Launch Helix.exe. No separate Python installation is needed. Choose MP3/WAV, choose xLights or LOR, supply the matching layout/template or an existing LMS with real Unit/Circuit addresses, choose an output folder, then Generate. Keep all exported show files together. The engine sequences the full song; preview length is separately configurable.

If Windows blocks the executable, first verify its checksum and source. Keep the complete error and the generated run log for support. A missing DLL usually means the portable folder was not completely extracted. LOR supports legacy LMS; modern .loredit is not exported directly. MP4 previews are Helix simulations unless explicitly marked as native FSEQ playback.

## Android and Samsung

1. Download the verified APK and compare its published SHA256.
2. Open it with My Files/Files. Allow that trusted app to install unknown apps if Android asks.
3. If Samsung Auto Blocker refuses installation, temporarily disable it in Settings > Security and privacy > Auto Blocker. Recheck its actual state; the reported off/on/off toggle helped on the user's device. Return to Files and retry.
4. Re-enable protection after installation. Preserve the old application and back up saved shows before an update. A differently signed APK cannot update an existing installation; do not uninstall just to work around this without backing up data.
5. Select MP3/WAV and a layout/template for xLights, or your addressed LMS for LOR. Generate locally, inspect the report, play the preview, then save/export the sequence and complete show ZIP.

If preview generation fails, completed sequences remain available for saving. Check the specific run error. Advanced technical settings are optional. Local sequencing does not require a desktop connection.

The beta APK is debug-signed unless its manifest states otherwise. Physical Samsung/ARM64 operation and upgrade from earlier signing keys require device testing. Emulator results do not prove a particular Samsung policy is resolved.

Community and support: [Facebook.com/helixsequencer](https://Facebook.com/helixsequencer).
