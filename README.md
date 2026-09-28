# 🧠 SupportBrain
AI customer-support assistant with persistent long-term memory.

## Problem
Traditional AI customer-support assistants often forget information from previous conversations. Customers may need to repeatedly explain:
- Their name
- Their previous issue
- Their preferences
- Previous troubleshooting steps
- Previous support interactions

SupportBrain solves this by using Hindsight as a long-term memory layer.

## Architecture
Customer
↓
SupportBrain UI
↓
FastAPI Backend
↓
Hindsight Recall
↓
OpenAI
↓
Personalized Response
↓
Hindsight Retain

## Features
- AI customer support
- Long-term customer memory
- Hindsight RETAIN
- Hindsight RECALL
- Personalized responses
- Memory visualization
- New conversation demonstration
- Simple web interface

## Tech Stack
- Python
- FastAPI
- OpenAI
- Hindsight
- HTML
- CSS
- JavaScript

## Run Backend
```bash
cd backend

# Windows
venv\Scripts\activate

uvicorn main:app --reload
```

Backend:
http://127.0.0.1:8000

## Run Frontend
Open:
`frontend/index.html`
in your browser.

## Demo
Tell SupportBrain your name.
Tell it about a support problem.
Click "Start New Conversation".
Ask about your previous problem.
SupportBrain recalls the information.
The Memory panel shows the retrieved memories.

## Future Scope
Customer authentication
Support ticket integration
CRM integration
Email support
Analytics dashboard
Multi-agent support
Voice support

