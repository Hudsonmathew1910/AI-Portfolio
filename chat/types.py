"""
Type definitions for the chat application.

This module defines custom types and protocols to improve type safety
and code clarity throughout the application.
"""

from typing import TypedDict, List, Dict, Any, Optional


class ChatMessage(TypedDict):
    """Structure for a chat message."""
    role: str  # 'user' or 'assistant'
    content: str


class PortfolioData(TypedDict, total=False):
    """Structure for portfolio data from data.json."""
    name: str
    summary: str
    focus: Optional[str]
    education: Dict[str, Any]
    internship: Dict[str, Any]
    projects: List[Dict[str, Any]]
    skills: Dict[str, List[str]]
    career: Dict[str, Any]
    personal: Dict[str, Any]


class ChatRequest(TypedDict):
    """Structure for chat API request."""
    message: str
    history: List[ChatMessage]


class ChatResponse(TypedDict):
    """Structure for chat API response."""
    reply: str


class ErrorResponse(TypedDict):
    """Structure for error response."""
    error: str


class OpenRouterMessage(TypedDict):
    """Structure for OpenRouter API message."""
    role: str
    content: str


class OpenRouterRequest(TypedDict, total=False):
    """Structure for OpenRouter API request."""
    model: str
    messages: List[OpenRouterMessage]
    max_tokens: int
