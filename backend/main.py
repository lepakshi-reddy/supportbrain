import os
import traceback

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from memory import remember, recall

# --------------------------------------------------
# LOAD ENVIRONMENT
# --------------------------------------------------
load_dotenv()

# --------------------------------------------------
# APP
# --------------------------------------------------
app = FastAPI(
    title="SupportBrain",
    description="AI Customer Support with Long-Term Memory",
    version="1.0.0"
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

# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------


@app.get("/health")
def health():
    return {
        "backend": "online",
        "service": "SupportBrain"
    }

# --------------------------------------------------
# CHAT
# --------------------------------------------------


@app.post("/chat")
def chat(data: dict):

    user_id = data.get(
        "user_id", "customer-001"
    )
    message = data.get(
        "message", ""
    ).strip()

    # --------------------------------------------------
    # VALIDATE MESSAGE
    # --------------------------------------------------
    if not message:
        return {
            "success": False,
            "error": "Message is required"
        }

    # --------------------------------------------------
    # RECALL
    # --------------------------------------------------
    memories = []
    try:
        memories = recall(
            query=message,
            user_id=user_id
        )
    except Exception as error:
        print("HINDSIGHT RECALL ERROR:")
        print(error)
        memories = []

    # --------------------------------------------------
    # FORMAT MEMORY
    # --------------------------------------------------
    if memories:
        memory_text = "\n".join(
            [
                f"- {memory['text']}"
                for memory in memories
            ]
        )
    else:
        memory_text = (
            "No relevant previous customer information "
            "was found."
        )

    # --------------------------------------------------
    # SYSTEM PROMPT
    # --------------------------------------------------
    system_prompt = f"""
    You are SupportBrain, an AI customer-support assistant.
    Your job is to provide helpful, friendly and concise customer support.
    
    You have access to information remembered from previous customer conversations.
    
    RELEVANT CUSTOMER MEMORY:
    {memory_text}
    
    IMPORTANT RULES:
    1. Use remembered information when it is relevant.
    2. Never invent a customer memory.
    3. Do not claim to remember something if it is not present in the provided memory.
    4. If there is no relevant memory, answer normally.
    5. Be professional and friendly.
    6. If the customer has mentioned their name before, personalize the response.
    7. If the customer previously had an issue, use that information when appropriate.
    """

    # --------------------------------------------------
    # CALL OPENAI
    # --------------------------------------------------
    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
        )
        answer = (
            response
            .choices[0]
            .message
            .content
        )
    except Exception as error:
        print("OPENAI ERROR:")
        print(error)
        return {
            "success": False,
            "error": "AI response failed"
        }

    # --------------------------------------------------
    # RETAIN USER MESSAGE
    # --------------------------------------------------
    try:
        remember(
            content=(
                f"Customer {user_id} said: {message}"
            ),
            user_id=user_id
        )
    except Exception as error:
        print("HINDSIGHT RETAIN ERROR:")
        print(error)

    # --------------------------------------------------
    # RETAIN ASSISTANT RESPONSE
    # --------------------------------------------------
    try:
        remember(
            content=(
                f"SupportBrain responded to customer "
                f"{user_id}: {answer}"
            ),
            user_id=user_id
        )
    except Exception as error:
        print("HINDSIGHT RESPONSE RETAIN ERROR:")
        print(error)

    # --------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------
    return {
        "success": True,
        "answer": answer,
        "memories": memories,
        "memory_count": len(memories)
    }
