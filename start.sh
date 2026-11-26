#!/bin/bash
cd "$(dirname "$0")"
echo "Starting CometAI Studio..."
echo "Opening http://127.0.0.1:8000"
python3 -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
