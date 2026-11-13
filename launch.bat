@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  if errorlevel 1 goto error
)
".venv\Scripts\python.exe" -c "import streamlit,sklearn,pandas,numpy,plotly,joblib" >nul 2>&1
if errorlevel 1 (
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto error
)
".venv\Scripts\python.exe" -m streamlit run streamlit_app.py --server.headless false
if errorlevel 1 goto error
exit /b 0
:error
echo Setup or launch failed. See the message above and the README.
pause
exit /b 1
