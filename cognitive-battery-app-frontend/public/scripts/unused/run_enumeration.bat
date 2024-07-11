@ECHO OFF
set TASK_NAME="enumeration"
call .\..\config.bat

setlocal enabledelayedexpansion

:inputLoop
set "USERNAME="
set /p USERNAME=Enter User_ID: 

if not defined USERNAME (
    echo Please enter User_ID.
    goto inputLoop
)

if not exist Data\ (
	mkdir Data
)
cd Data

start python -i .\..\Python_scripts\record_eye.py  %COMPUTER_NAME% %TASK_NAME% %USERNAME%
start python -i .\..\Python_scripts\record_movesense_sensor.py %END_OF_SERIAL% %COMPUTER_NAME% %TASK_NAME% %USERNAME%
