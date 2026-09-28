import os
import tempfile
import traceback

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from sqlalchemy.orm import Session

try:
    from .database import Customer, get_db
    from .memory import recall, remember
except ImportError:  # pragma: no cover
    from database import Customer, get_db
    from memory import recall, remember

load_dotenv()

app = FastAPI(
    title="Memora",
    description="AI Assistant with Memory",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=api_key) if api_key else None
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

MOCK_MEMORIES = []


@app.get("/")
def home():
    return {"status": "success", "message": "Memora is running!"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "supportbrain",
        "database": "ready",
        "hindsight": "fallback-ok",
    }


@app.post("/chat")
def chat(data: dict, db: Session = Depends(get_db)):
    global MOCK_MEMORIES
    user_id = data.get("user_id", "demo-user")
    message = data.get("message", "").strip()

    if not message:
        return {"success": False, "error": "Message is required"}

    customer = db.query(Customer).filter(Customer.user_id == user_id).first()
    if not customer:
        customer = Customer(user_id=user_id)
        db.add(customer)
        db.commit()
        db.refresh(customer)

    memories = []
    try:
        memories = recall(query=message, user_id=user_id)
    except Exception as error:
        print("HINDSIGHT RECALL ERROR:", error)
        memories = MOCK_MEMORIES.copy()

    memory_text = "\n".join(
        [f"- {m['text']}" for m in memories]) if memories else "No previous memory."
    db_context = f"Database Profile -> Name: {customer.name or 'Unknown'}"

    system_prompt = f"""
    You are Memora, an AI assistant with perfect memory.

    {db_context}

    RELEVANT MEMORY:
    {memory_text}

    RULES:
    1. Use remembered information when it is relevant.
    2. Be conversational and helpful.
    3. If the user tells you a fact about themselves, acknowledge that you will remember it.
    """

    try:
        if openai_client is None:
            answer = (
                "I’m running in demo mode, and I’ll use the context I have so far. "
                "If you tell me your name or issue, I’ll remember it for next time."
            )
        else:
            response = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message},
                ],
            )
            answer = response.choices[0].message.content
    except Exception as error:
        print("OPENAI ERROR:", error)
        return {"success": False, "error": "AI response failed. Check OpenAI API Key."}

    retained_messages = []
    content1 = str(message)
    try:
        remember(content=content1, user_id=user_id)
        retained_messages.append(content1)
    except Exception:
        MOCK_MEMORIES.append(
            {"text": content1, "type": "memory", "context": "mock"})
        retained_messages.append(content1)

    activity = [
        {"type": "retained", "text": f"Stored memory for {user_id}: {message}"},
        {"type": "recalled", "text": f"Used relevant context for: {message}"},
    ]

    return {
        "success": True,
        "answer": answer,
        "memories": memories,
        "retained": retained_messages,
        "activity": activity,
    }
