CUSTOMER QUICK START

Dream Sequence Weaver is now a one-click xLights auto-sequencer. The default expectation is a show-ready sequence, not a draft that requires a long manual cleanup pass.

HOW TO RUN

1. Place these files together:
   - `template.xsq`
   - `xlights_rgbeffects.xml` or `xlights_rgbeffects.xbkp`
   - your song audio file

2. Start the app with:
   - `launch_sequencer_app.cmd`
   - or `python main.py`

3. For a direct command-line run, use:
   - `python main.py --profile master -- --template template.xsq --audio song.wav --no-prompt --polish --variants 3 --auto-shortlist`

WHAT THE ENGINE DOES FOR YOU

- analyzes the song and available stems
- maps effects across the whole layout
- audits overlap, balance, and musical coherence
- polishes hooks, transitions, breathing moments, and color flow
- generates multiple candidate renders if requested
- auto-selects the best one when shortlisting is enabled

FILES YOU WILL GET

- final `.xsq` sequence
- `.report.json` quality and audit summary
- `.sequence_notes.txt` readiness summary

WHEN TO OPEN XLIGHTS

Open xLights when you want a personal final look check or optional artistic touch-up. It should not be required for normal delivery-quality output.

RECOMMENDED DEFAULT

`python main.py --profile master -- --template template.xsq --audio song.wav --no-prompt --polish --variants 3 --auto-shortlist --learn-from-my-xsqs`
