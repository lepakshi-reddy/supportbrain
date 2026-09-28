import os

try:
    from hindsight_client import Hindsight
except ImportError:  # pragma: no cover - optional dependency in local demos
    Hindsight = None

try:
    from .database import MemoryEntry, SessionLocal
except ImportError:  # pragma: no cover
    from database import MemoryEntry, SessionLocal

HINDSIGHT_BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "http://localhost:8888")
BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "supportbrain")
client = Hindsight(
    base_url=HINDSIGHT_BASE_URL) if Hindsight is not None else None


def _local_store(user_id: str, content: str, source: str = "local"):
    db = SessionLocal()
    try:
        entry = MemoryEntry(user_id=user_id, content=content, source=source)
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
    finally:
        db.close()


def _local_recall(query: str, user_id: str):
    db = SessionLocal()
    try:
        text = (query or "").lower()
        terms = [word for word in text.split() if len(word) > 3]
        rows = (
            db.query(MemoryEntry)
            .filter(MemoryEntry.user_id == user_id)
            .order_by(MemoryEntry.created_at.desc())
            .all()
        )

        scored = []
        for row in rows:
            row_text = row.content.lower()
            score = sum(1 for term in terms if term in row_text)
            if score or not terms:
                scored.append(
                    {
                        "text": row.content,
                        "type": row.source,
                        "context": "local-memory",
                        "score": score,
                    }
                )

        scored.sort(key=lambda item: item["score"], reverse=True)
        return [
            {"text": item["text"], "type": item["type"],
                "context": item["context"]}
            for item in scored[:5]
        ]
    finally:
        db.close()


def remember(content: str, user_id: str):
    """
    Store useful customer information in Hindsight with a local fallback.
    """
    if client is None:
        return _local_store(user_id=user_id, content=content, source="local")

    try:
        return client.retain(
            bank_id=BANK_ID,
            content=content,
            context="supportbrain-customer-support",
            metadata={"user_id": user_id},
        )
    except Exception:
        return _local_store(user_id=user_id, content=content, source="local")


def recall(query: str, user_id: str):
    """
    Search Hindsight for memories relevant to the customer's message.
    Falls back to a local SQLite memory store when Hindsight is unavailable.
    """
    if client is None:
        return _local_recall(query=query, user_id=user_id)

    try:
        response = client.recall(bank_id=BANK_ID, query=query)
        memories = []

        for result in getattr(response, "results", []):
            memories.append(
                {
                    "text": result.text,
                    "type": getattr(result, "type", "memory"),
                    "context": getattr(result, "context", "hindsight"),
                }
            )

        if memories:
            return memories
    except Exception:
        pass

    return _local_recall(query=query, user_id=user_id)
