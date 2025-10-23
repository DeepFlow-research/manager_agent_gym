#!/bin/bash
# Run the rubric annotation app

cd "$(dirname "$0")/.." || exit
streamlit run src/streamlit_app.py --server.port 8501

