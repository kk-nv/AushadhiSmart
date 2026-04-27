@echo off
REM Quick-start script for Windows
REM Double-click this file or run from cmd: run.bat

echo Checking dependencies...
pip install -r requirements.txt --quiet

echo Launching Generic Medicine Recommender...
streamlit run app\main.py
