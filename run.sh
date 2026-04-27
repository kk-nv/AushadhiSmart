#!/bin/bash
# Quick-start script for Unix/Mac
# Usage: bash run.sh

echo "🔍 Checking dependencies..."
pip install -r requirements.txt --quiet

echo "🚀 Launching Generic Medicine Recommender..."
streamlit run app/main.py
