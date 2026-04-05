#!/bin/bash
set -e
cd /opt/taiwan-strait-monitor/backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi
exec uvicorn main:app --host 127.0.0.1 --port 8000
