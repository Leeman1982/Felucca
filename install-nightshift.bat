@echo off
rem Install NightShift on the FM-1 connected by USB (needs Python 3: pip install mido python-rtmidi).
rem Without Python: open build\NightShift-updater.html in Chrome or Edge instead.
python "%~dp0tools\fm1_install.py" "%~dp0build\felucca.fwsc" %*
pause
