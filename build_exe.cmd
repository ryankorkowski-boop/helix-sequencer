@echo off
setlocal
pushd "%~dp0"

powershell -ExecutionPolicy Bypass -File "%~dp0build_exe.ps1" %*
if errorlevel 1 (
  echo Build failed.
  popd
  endlocal
  exit /b 1
)

echo Build succeeded.
popd
endlocal
exit /b 0
