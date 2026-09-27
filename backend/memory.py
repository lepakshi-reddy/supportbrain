import os
from hindsight_client import Hindsight

HINDSIGHT_BASE_URL = os.getenv(
    "HINDSIGHT_BASE_URL", "http://localhost:8888"
)
BANK_ID = os.getenv(
    "HINDSIGHT_BANK_ID", "supportbrain"
)

client = Hindsight(
    base_url=HINDSIGHT_BASE_URL
)

def remember(content: str, user_id: str):
    """
    Store useful customer information in Hindsight.
    """
    return client.retain(
        bank_id=BANK_ID,
        content=content,
        context="supportbrain-customer-support",
        metadata={
            "user_id": user_id
        }
    )

def recall(query: str, user_id: str):
    """
    Search Hindsight for memories relevant to the customer's message.
    """
    response = client.recall(
        bank_id=BANK_ID,
        query=query
    )

    memories = []

    for result in response.results:
        memories.append({
            "text": result.text,
            "type": result.type,
            "context": result.context
        })

    return memories
