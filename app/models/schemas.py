"""
app/models/schemas.py
---------------------------------------
Pydantic schemas (data models) defining
the structure of requests and responses
for the HappyFares AI Backend.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class ChatRequest(BaseModel):
    """
    Input format from the frontend chat widget.

    Attributes:
        session_id: Unique identifier for the chat session
        question: User’s question or query
        context: The list of flight cards or booking data for that page
    """
    session_id: str = Field(..., description="Unique session identifier")
    question: str = Field(..., description="User question from the chat")
    context: List[Dict[str, Any]] = Field(..., description="Page context data (e.g. flight cards)")


class ChatResponse(BaseModel):
    """
    Output format sent back to the frontend.

    Attributes:
        answer: The AI-generated response
        excerpt: Supporting text (verbatim snippet) from the context
    """
    answer: str = Field(..., description="Answer generated based on the context")
    excerpt: Optional[str] = Field(None, description="Verbatim excerpt from the page context")
