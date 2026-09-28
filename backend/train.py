import os

try:
    from .memory import remember
except ImportError:
    from memory import remember


TRAINING_ITEMS = [
    "SupportBrain helps customers with product support, onboarding, troubleshooting, and account issues.",
    "Customers often need help with login problems, password reset, billing concerns, and service outages.",
    "When a customer gives their name, use it in the response and be friendly and professional.",
    "Document recurring issues, priorities, and past troubleshooting steps for future conversations.",
    "Always confirm the customer's problem before suggesting a fix or escalation.",
    "If the customer mentions a prior issue, use that context to provide a personalized response.",
]


def seed_supportbrain_knowledge():
    stored = []
    for item in TRAINING_ITEMS:
        try:
            remember(content=item, user_id="supportbrain-training")
            stored.append(item)
        except Exception as error:
            print(f"Training item failed: {item} -> {error}")
    return {"stored": len(stored), "items": stored}


if __name__ == "__main__":
    print(seed_supportbrain_knowledge())
