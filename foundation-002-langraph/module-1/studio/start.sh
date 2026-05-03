#!/bin/bash
# Find an available port starting from 2024
PORT=9999
while lsof -ti :$PORT > /dev/null 2>&1; do
  PORT=$((PORT + 1))
done
echo "Starting LangGraph dev on port $PORT"
uv run --project ../.. langgraph dev --port $PORT
