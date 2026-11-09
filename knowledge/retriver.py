from knowledge_base import PolicyKnowledgeBase
from functools import lru_cache


@lru_cache
async def search_policy(query:str,limit:int=5):
    knowledge=PolicyKnowledgeBase()
    chunks= await knowledge.search_policy(query,limit)
    return chunks




if __name__ == "__main__":
    import asyncio
    query=""
    asyncio.run(search_policy(query))