@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" -m uvicorn shinku_tts_adapter:app --host 127.0.0.1 --port 8091 1> ".shinku-tts-adapter.out.log" 2> ".shinku-tts-adapter.err.log"
