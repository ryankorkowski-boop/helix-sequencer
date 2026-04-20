@echo off
setlocal
cd /d "%~dp0"
if exist "%~dp0HelixSequenceWeaverBeta.exe" (
  start "" "%~dp0HelixSequenceWeaverBeta.exe" %*
) else if exist "%~dp0dist\HelixSequenceWeaverBeta.exe" (
  start "" "%~dp0dist\HelixSequenceWeaverBeta.exe" %*
) else (
  start "" "%~dp0launch_sequencer_app.cmd" %*
)
