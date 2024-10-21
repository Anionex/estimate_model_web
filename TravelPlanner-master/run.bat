cd agents
set OUTPUT_DIR=.\outputs

set MODEL_NAME=gpt-4o-2024-08-06
set OPENAI_API_KEY=sk-Opz25zl4iSRoXnwF87350eC7E5B9494bA3BfFfF4243c4331
set OPENAI_API_BASE=https://chatapi.onechats.top/v1
set GOOGLE_API_KEY=1

set SET_TYPE=validation
pause
..\python-3.10.11-embed-amd64\python.exe tool_agents.py
pause