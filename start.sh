#!/bin/bash
# Start the authentication service

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port ${AUTH_SERVICE_PORT:-3001} --reload
