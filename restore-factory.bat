@echo off
rem Put M-VAVE's official V15 back: drag the unmodified FM-1.fwsc onto this file.
rem Back up first (the updater page's "Back up and return to official V15" does it); Felucca / NightShift
rem projects do not open on V15.
python "%~dp0tools\fm1_install.py" %*
pause
