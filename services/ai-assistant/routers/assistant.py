"""
AI Assistant router - question answering and recommendations
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()


class AIAssistantQuery(BaseModel):
    question: str
    context: Optional[dict] = None  # warehouse stocks, sales, ads stats, etc.


class AIAssistantResponse(BaseModel):
    answer: str  # Markdown-formatted response
    confidence: float
    sources_used: List[str]  # What data was included in context
    cached: bool


@router.post("/ask")
async def ask_assistant(query: AIAssistantQuery) -> AIAssistantResponse:
    """
    Ask the AI assistant a question
    
    Context automatically includes:
    - Warehouse stock levels (WB)
    - Sales and returns by product/size (last 7 days)
    - Ad campaign statistics (ROMI, CPC, etc.)
    
    Example questions:
    - "Какие размеры срочно пополнить на складе в Коледино?"
    - "Какая кампания в Яндекс.Директ самая неэффективная?"
    - "Что делать если возвраты растут?"
    
    Answers are Markdown-formatted and displayed in the right panel
    """
    # TODO: Implement AI assistant
    # 1. Fetch contextual data (warehouse, sales, ads)
    # 2. Check Redis cache for identical questions
    # 3. If not cached, call OpenAI API
    # 4. Cache result for 1 hour
    # 5. Log query for audit
    pass


@router.get("/history")
async def get_query_history(limit: int = 20) -> List[dict]:
    """
    Get user's recent AI assistant queries
    """
    # TODO: Implement history retrieval
    pass


@router.get("/usage")
async def get_usage_stats() -> dict:
    """
    Get current month's AI usage:
    - Queries used
    - Limit for tier
    - Cost if applicable
    """
    # TODO: Implement usage stats
    pass
