"""
Views for the chat application.

This module handles HTTP request/response cycles while delegating
business logic to service layer for separation of concerns.
"""

import json
import logging
from typing import Optional

from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

from .services import ChatManager, PortfolioService, AIService
from .types import ChatRequest
from .utils import validate_chat_message
from .constants import (
    DATA_JSON_FILENAME,
    ERROR_MESSAGE_REQUIRED,
    ERROR_INVALID_JSON,
    STATUS_BAD_REQUEST,
    STATUS_SERVER_ERROR,
)

logger = logging.getLogger(__name__)

# Initialize services
_portfolio_service: Optional[PortfolioService] = None
_ai_service: Optional[AIService] = None
_chat_manager: Optional[ChatManager] = None


def _get_chat_manager() -> ChatManager:
    """
    Lazy-initialize and return chat manager singleton.
    
    This ensures services are only instantiated once per app startup
    and reused across requests for efficiency.
    
    Returns:
        ChatManager instance
    """
    global _chat_manager, _portfolio_service, _ai_service
    
    if _chat_manager is None:
        data_file = settings.BASE_DIR / DATA_JSON_FILENAME
        _portfolio_service = PortfolioService(data_file)
        _ai_service = AIService()
        _chat_manager = ChatManager(_portfolio_service, _ai_service)
        logger.info("Initialized chat services")
    
    return _chat_manager


def home(request: HttpRequest) -> HttpResponse:
    """
    Render chat home page.
    
    Args:
        request: HTTP request
        
    Returns:
        Rendered HTML response
    """
    logger.debug("Serving home page")
    return render(request, "chat.html")


@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request: HttpRequest) -> JsonResponse:
    """
    Handle chat API requests.
    
    Processes user messages and returns AI-generated responses
    while maintaining conversation history context.
    
    Request JSON:
        {
            "message": str,  # User's message
            "history": [{"role": str, "content": str}, ...]  # Previous messages
        }
    
    Response JSON:
        {
            "reply": str  # AI response
        }
        or
        {
            "error": str  # Error message
        }
    
    Args:
        request: HTTP POST request with JSON body
        
    Returns:
        JsonResponse with reply or error
    """
    try:
        # Parse request body
        body_data = _parse_request_body(request)
        if isinstance(body_data, JsonResponse):
            return body_data
        
        request_data: ChatRequest = body_data
        
        # Validate message
        is_valid, error_msg = validate_chat_message(request_data.get("message", ""))
        if not is_valid:
            logger.warning("Invalid message: %s", error_msg)
            return JsonResponse(
                {"error": error_msg or ERROR_MESSAGE_REQUIRED},
                status=STATUS_BAD_REQUEST
            )
        
        user_message = request_data["message"].strip()
        history: list = request_data.get("history", [])
        
        logger.debug("Processing message: %s (history: %d items)", 
                    user_message[:50], len(history))
        
        # Get chat manager and process message
        chat_manager = _get_chat_manager()
        response = chat_manager.process_chat(user_message, history)
        
        # Return response
        if response.success:
            logger.info("Chat response generated successfully")
            return JsonResponse({"reply": response.reply})
        else:
            status_code = response.status_code or STATUS_SERVER_ERROR
            logger.error("Chat error: %s (status: %d)", response.error, status_code)
            return JsonResponse(
                {"error": response.error},
                status=status_code
            )
    
    except Exception as e:
        logger.exception("Unexpected error in chat_api")
        return JsonResponse(
            {"error": "An unexpected error occurred. Please try again."},
            status=STATUS_SERVER_ERROR
        )


def _parse_request_body(request: HttpRequest) -> dict | JsonResponse:
    """
    Parse and validate request JSON body.
    
    Args:
        request: HTTP request
        
    Returns:
        Parsed request data or error JsonResponse
    """
    try:
        body = json.loads(request.body)
        
        # Validate required fields
        if "message" not in body:
            logger.warning("Missing 'message' field in request")
            return JsonResponse(
                {"error": ERROR_MESSAGE_REQUIRED},
                status=STATUS_BAD_REQUEST
            )
        
        return body
    
    except json.JSONDecodeError as e:
        # Log the raw body for debugging malformed requests
        try:
            raw = request.body.decode('utf-8', errors='replace')
        except Exception:
            raw = repr(request.body)
        logger.warning("Invalid JSON in request: %s; raw_body=%s", e, raw[:2000])
        return JsonResponse(
            {"error": ERROR_INVALID_JSON},
            status=STATUS_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error("Error parsing request: %s", e)
        return JsonResponse(
            {"error": "Invalid request format"},
            status=STATUS_BAD_REQUEST
        )
