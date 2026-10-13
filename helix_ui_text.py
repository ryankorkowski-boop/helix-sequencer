"""Shared customer guidance and truthful licensing information."""
TAGLINE = 'Audio in. Lights out.'
INSTRUCTIONS = '''Your first Helix show

1. Choose your music (MP3 or WAV is a good starting point).
2. Choose xLights or Light-O-Rama.
3. For xLights, import xlights_rgbeffects.xml and optionally your XSQ template/controllers. For LOR, import an existing LMS containing your real Unit/Circuit addresses.
4. Choose an output folder on desktop. On Android, generated shows stay private until you save or share them.
5. Keep the default colors and automatic musical response to start. Advanced controls are optional. Neon is only an optional RGB palette.
6. Generate. The full song is sequenced even when the preview is shorter.
7. Play the preview, then save the sequence and complete show ZIP. Keep the soundtrack, layout and controller files together.
8. Import and check the show in your lighting software before controller playback.

If the preview fails, your completed sequence can still be saved. Read the run report for the specific error. Native .loredit/LCC import is not currently supported.

Android installation: use the project APK and verify its published checksum. Open it in My Files/Files, allow that trusted app to install it when prompted, and temporarily disable Samsung Auto Blocker if it blocks the install. Recheck its state if necessary and re-enable protection afterward. Keep the old app and back up shows before an update; a different signing certificate cannot update the old installation.

Desktop control from your phone is optional and requires reaching your own Helix desktop server. Local Android sequencing does not require a desktop.
'''
LEGAL = '''Helix — free for homeowner use

Core software: MIT License, Copyright (c) 2026 Helix Sequencer Contributors. The existing license permits use, modification, distribution and commercial use/resale, subject to its notice requirements. This information page does not revoke those permissions or replace third-party licenses.

Commercial products: separately licensed Helix-branded premium assets, proprietary additions, integration services and support may require a written annual vendor/enterprise agreement. Prices and covered rights must be agreed in writing. An annual fee is not imposed on the existing MIT core by this page.

Attribution: exports identify their generator as “Made with Helix”. Please retain that credit when publicly sharing Helix-branded shows; retain applicable license notices when distributing code or protected assets. Separate commercial asset agreements may contain their own attribution requirements.

Music: preview/demo music is supplied by Helix / Ryan Korkowski. Only tracks explicitly marked rights-cleared are offered for free homeowner use under their accompanying music permission. The application does not verify that all songs are exclusively owned or cleared for redistribution. AI music permissions depend on the creation account, subscription and applicable terms. Your uploaded music remains subject to its own rights and permissions; a software license does not grant music rights.

Provenance marks identify the generator and output integrity. They are not DRM, proof of copyright, or permission to use a song. No hidden network tracking is required.

Use previews to review a show. Check physical wiring, controller mapping and final import/playback before using output with lights. The software is provided under the warranty terms in the included MIT license.
'''
