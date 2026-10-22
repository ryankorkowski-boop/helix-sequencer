; A single download expands the unchanged, verified portable runtime per user.
; Official command reference: https://nsis.sourceforge.io/Docs/Chapter4.html
Unicode true
!ifndef SOURCE_SHA
  !error "A verified runtime SOURCE_SHA is required"
!endif
!ifndef PAYLOAD_DIR
  !error "The verified portable PAYLOAD_DIR is required"
!endif
!ifndef OUTPUT_FILE
  !error "An OUTPUT_FILE is required"
!endif
Name "Helix Sequencer Beta"
OutFile "${OUTPUT_FILE}"
Icon "${ICON_FILE}"
RequestExecutionLevel user
SilentInstall silent
SetCompressor /SOLID lzma
InstallDir "$LOCALAPPDATA\HelixSequencer\beta-runtime\${SOURCE_SHA}"

Section "Helix runtime"
  SetOutPath "$INSTDIR"
  IfFileExists "$INSTDIR\source-ready.txt" launch
  ClearErrors
  File /r "${PAYLOAD_DIR}\*"
  IfErrors unpack_error
  FileOpen $0 "$INSTDIR\source-ready.txt" w
  IfErrors unpack_error
  FileWrite $0 "${SOURCE_SHA}"
  FileClose $0
launch:
  ClearErrors
  Exec '"$INSTDIR\Helix.exe"'
  IfErrors launch_error
  SetErrorLevel 0
  Goto done
unpack_error:
  Delete "$INSTDIR\source-ready.txt"
  MessageBox MB_OK|MB_ICONSTOP "Helix could not unpack its runtime in your local application folder."
  SetErrorLevel 1
  Goto done
launch_error:
  MessageBox MB_OK|MB_ICONSTOP "Helix could not start. The bundled runtime is in $INSTDIR."
  SetErrorLevel 1
done:
SectionEnd
