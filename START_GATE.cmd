@echo off
cd /d "%~dp0backend"
echo SHESEETVAI USB gate - COM4
echo.
echo Close Arduino Serial Monitor before continuing.
echo Keep the tested SHESEETVAI_GATE_TEST sketch uploaded.
echo The bench motors MUST currently represent the CLOSED position.
echo Opening USB may reset the Uno; this starts a new gate session.
echo Press Ctrl+C to cancel if the closed reference is uncertain.
echo.
pause
venv\Scripts\python.exe manage.py gate_bridge --port COM4 --closed-reference
echo.
pause
