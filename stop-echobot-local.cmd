@echo off
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do taskkill /PID %%p /F
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8091" ^| findstr "LISTENING"') do taskkill /PID %%p /F
