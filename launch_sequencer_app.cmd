@echo off
setlocal enableextensions
pushd "%~dp0"

set "EXE=%~dp0HelixSequenceWeaverBeta.exe"
if exist "%EXE%" (
  start "" "%EXE%" %*
  popd
  endlocal
  exit /b 0
)

set "EXE=%~dp0dist\HelixSequenceWeaverBeta.exe"
if exist "%EXE%" (
  start "" "%EXE%" %*
  popd
  endlocal
  exit /b 0
)

set "EXE=%~dp0dist\HelixSequenceWeaverBeta\HelixSequenceWeaverBeta.exe"
if exist "%EXE%" (
  start "" "%EXE%" %*
  popd
  endlocal
  exit /b 0
)

set "SCRIPT=%~dp0main.py"
if not exist "%SCRIPT%" (
  echo Active entry script not found: %SCRIPT%
  pause
  exit /b 1
)

set "PY="

if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\python.exe"
if not defined PY if exist "C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe" set "PY=C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe"

if not defined PY (
  py -3.12 --version >nul 2>&1
  if not errorlevel 1 (
    set "PY=py -3.12"
  )
)

if not defined PY (
  py --version >nul 2>&1
  if not errorlevel 1 (
    set "PY=py"
  )
)

if not defined PY (
  echo Could not find Python. Install Python 3.12 or set up .venv first.
  pause
  exit /b 1
)

if "%PY%"=="py -3.12" (
  start "" py -3.12 "%SCRIPT%" %*
) else if "%PY%"=="py" (
  start "" py "%SCRIPT%" %*
) else (
  start "" "%PY%" "%SCRIPT%" %*
)

popd
endlocal
exit /b 0
