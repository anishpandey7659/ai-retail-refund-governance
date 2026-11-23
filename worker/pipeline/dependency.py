from knowledge.knowledge_base import PolicyKnowledgeBase
from functools import lru_cache
from backend.app.services import mail

@lru_cache
def get_policy_knowledge_base() -> PolicyKnowledgeBase:
    """Get the policy knowledge base."""
    return PolicyKnowledgeBase()


def notify_reviewer(to: str, subject: str, body: str) -> None:
    mail.send(
        to,
        subject,
        body,
    )