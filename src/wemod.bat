@echo off
@title Wemod Launcher

SET mypath=%~dp0
SET wemodname=WeMod.exe

IF "%mypath:~-5%" == "\src\" (
    SET wemodpath=%mypath:~0,-5%\wemod_data\wemod_bin\%wemodname%
) ELSE (
    SET wemodpath=%mypath:~0,-1%\wemod_data\wemod_bin\%wemodname%
)

SET temptime=%mypath:~0,-1%\.cache\early.tmp
SET returnfile=%mypath:~0,-1%\.cache\return.tmp

echo Hello from the WeMod Launcher, the WeMod bat was started successfully.
echo.
echo WeMod EXE path:
echo %wemodpath%
echo.
echo CWD:
echo %cd%
echo.
echo Command:
echo %*

echo.
echo.

REM Start WeMod.exe and get its PID
echo Starting WeMod by using %wemodname%.
start "" "%wemodpath%"

set wemodPID=

REM Get the WeMod launcher PID, loop until found, and exit subroutine when found.
set wemodPIDCounter=0

:search
echo Searching for WeMod PID...
REM Check we haven't run this more than 3 times.
if %wemodPIDCounter% GTR 3 (
    echo WeMod not found in process list, defaulting to prevent infinite loop... > "%returnfile%"
    type "%returnfile%"
    goto :discovered
)
for /F "TOKENS=1,2 delims=," %%a in ('C:/windows/system32/tasklist /FO CSV /NH /FI "IMAGENAME eq %wemodname%"') do (
  set wemodPID=%%b
)
if defined wemodPID goto :discovered
echo Continue search for WeMod PID...
set /A wemodPIDCounter+=1
@ping localhost -n 6 >NUL
goto :search

:discovered

echo WeMod found with pid %wemodPID%
echo.

REM start the game and wait for exit
echo Running game "%~1" and waiting for closure..
echo The full command is: %*
start /wait "" %*
echo.
echo The game was closed.

if defined wemodPID (
    if exist "%temptime%" (
        del "%temptime%"
        echo Game closed too fast, Game detection may have failed. > "%returnfile%"
        echo Keep in mind that wemod-launcher usually can`t detect game launchers. >> "%returnfile%"
        echo Only open an issue IF the game did not start, >> "%returnfile%"
        echo or IF the game crashed, or IF WeMod exits unexpectedly. >> "%returnfile%"
        type "%returnfile%"
        call :WaitUser
    )
    echo Closing WeMod..
    C:/windows/system32/taskkill.exe /PID %wemodPID% /F >NUL
    echo Killed %wemodname% with pid %wemodPID%
)

echo.
echo Done running bat, closing in 1 second
@ping localhost -n 2 >NUL
echo.
goto :eof

REM Wait for the Python side (bat_respond) to consume return.tmp, with a
REM timeout (~150 * ~2s) so a dead Python side can't block this script forever
REM inside the Wine prefix.
:WaitUser
set waitCounter=0
:WaitUserLoop
if not exist "%returnfile%" goto :eof
@ping localhost -n 3 >NUL
set /A waitCounter+=1
if %waitCounter% LSS 150 goto :WaitUserLoop
echo Timed out waiting for the launcher response; continuing to close WeMod.
del "%returnfile%" >NUL 2>&1
goto :eof
