@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" -m echobot app --host 127.0.0.1 --port 8000 1> ".echobot-app.out.log" 2> ".echobot-app.err.log"
