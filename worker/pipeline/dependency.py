from knowledge.knowledge_base import PolicyKnowledgeBase
from functools import lru_cache

@lru_cache
def get_policy_knowledge_base() -> PolicyKnowledgeBase:
    """Get the policy knowledge base."""
    return PolicyKnowledgeBase()