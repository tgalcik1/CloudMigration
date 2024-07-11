@ECHO OFF
set TASK_NAME="baseline"
call .\..\config.bat

setlocal enabledelayedexpansion

if "%~1"=="" (
    echo No username provided.
    exit /b 1
)

set "USERNAME=%~1"
echo Username provided: %USERNAME%

if not exist Data\ (
    mkdir Data
)
cd Data

start python -i .\..\public\scripts\Python_scripts\record_eye.py %COMPUTER_NAME% %TASK_NAME% %USERNAME%
start python -i .\..\public\scripts\Python_scripts\record_sensor.py %PORT% %COMPUTER_NAME% %TASK_NAME% %USERNAME%
