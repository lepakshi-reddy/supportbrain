import os
import traceback

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session

try:
    from .database import Customer, get_db
    from .memory import recall, remember
except ImportError:
    from database import Customer, get_db
    from memory import recall, remember

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# --------------------------------------------------
# APP
# --------------------------------------------------
app = FastAPI(
    title="SupportBrain",
    description="AI Customer Support with Long-Term Memory and DB",
    version="1.1.0"
)

# --------------------------------------------------
# CORS
# --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# OPENAI
# --------------------------------------------------
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL", "gpt-5.5"
)

# --------------------------------------------------
# HOME
# --------------------------------------------------


@app.get("/")
def home():
    return {
        "status": "success",
        "message": "SupportBrain is running!"
    }


@app.post("/train")
def train_memory():
    try:
        try:
            from .train import seed_supportbrain_knowledge
        except ImportError:
            from train import seed_supportbrain_knowledge

        result = seed_supportbrain_knowledge()
        return {
            "success": True,
            "message": "SupportBrain training data loaded.",
            "stored": result.get("stored", 0),
            "items": result.get("items", [])
        }
    except Exception as error:
        print("TRAINING ERROR:")
        print(error)
        return {
            "success": False,
            "error": f"Training failed: {type(error).__name__}: {error}"
        }

# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------


@app.get("/health")
def health(db: Session = Depends(get_db)):
    status = {
        "backend": "online",
        "service": "SupportBrain",
        "database": "unknown",
        "hindsight": "unknown"
    }

    try:
        db.execute(text("SELECT 1"))
        status["database"] = "online"
    except Exception as error:
        status["database"] = "offline"
        print("DATABASE HEALTH CHECK ERROR:")
        print(error)

    try:
        try:
            from .memory import client
        except ImportError:
            from memory import client

        client.banks()
        status["hindsight"] = "online"
    except Exception as error:
        status["hindsight"] = "offline"
        print("HINDSIGHT HEALTH CHECK ERROR:")
        print(error)

    return status

# --------------------------------------------------
# CUSTOMER CRUD ENDPOINTS
# --------------------------------------------------


@app.get("/customer/{user_id}")
def get_customer(user_id: str, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.user_id == user_id).first()
    if not customer:
        return {"success": False, "error": "Customer not found"}
    return {
        "success": True,
        "customer": {
            "user_id": customer.user_id,
            "name": customer.name,
            "email": customer.email
        }
    }


@app.post("/customer/{user_id}")
def update_customer(user_id: str, data: dict, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.user_id == user_id).first()
    if not customer:
        customer = Customer(user_id=user_id)
        db.add(customer)

    if "name" in data:
        customer.name = data["name"]
    if "email" in data:
        customer.email = data["email"]

    db.commit()
    db.refresh(customer)
    return {
        "success": True,
        "customer": {
            "user_id": customer.user_id,
            "name": customer.name,
            "email": customer.email
        }
    }

# --------------------------------------------------
# CHAT
# --------------------------------------------------


@app.post("/chat")
def chat(data: dict, db: Session = Depends(get_db)):
    user_id = data.get("user_id", "customer-001")
    message = data.get("message", "").strip()

    if not message:
        return {
            "success": False,
            "error": "Message is required"
        }

    try:
        customer = db.query(Customer).filter(
            Customer.user_id == user_id).first()
        if not customer:
            customer = Customer(user_id=user_id)
            db.add(customer)
            db.commit()
            db.refresh(customer)

        memories = []
        try:
            memories = recall(query=message, user_id=user_id)
        except Exception as error:
            print("HINDSIGHT RECALL ERROR:")
            print(error)
            memories = []

        if memories:
            memory_text = "\n".join(
                [f"- {memory['text']}" for memory in memories]
            )
        else:
            memory_text = "No relevant previous customer information was found."

        db_context = (
            f"Database Record -> Name: {customer.name or 'Unknown'}, "
            f"Email: {customer.email or 'Unknown'}"
        )

        system_prompt = f"""
        You are SupportBrain, an AI customer-support assistant.
        Your job is to provide helpful, friendly and concise customer support.

        You have access to information remembered from previous customer conversations as well as their structured database profile.

        CUSTOMER DATABASE PROFILE:
        {db_context}

        RELEVANT CUSTOMER MEMORY (from past chats):
        {memory_text}

        IMPORTANT RULES:
        1. Use remembered information when it is relevant.
        2. Never invent a customer memory.
        3. Do not claim to remember something if it is not present in the provided memory.
        4. If there is no relevant memory, answer normally.
        5. Be professional and friendly.
        6. Personalize the response using their Database Profile name if known, or if they mention their name, use it.
        7. If the customer previously had an issue, use that information when appropriate.
        """

        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
        )
        answer = response.choices[0].message.content

        try:
            remember(
                content=f"Customer {user_id} said: {message}", user_id=user_id)
        except Exception as error:
            print("HINDSIGHT RETAIN ERROR:")
            print(error)

        try:
            remember(
                content=f"SupportBrain responded to customer {user_id}: {answer}", user_id=user_id)
        except Exception as error:
            print("HINDSIGHT RESPONSE RETAIN ERROR:")
            print(error)

        return {
            "success": True,
            "answer": answer,
            "memories": memories,
            "memory_count": len(memories),
            "db_profile": {
                "name": customer.name,
                "email": customer.email
            }
        }
    except Exception as error:
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Chat request failed: {type(error).__name__}: {error}"
        }
