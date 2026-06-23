"""
Service layer for chat application business logic.

This module contains the core business logic separated from
view logic, making it testable and reusable.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass

import requests

from .constants import (
    OPENROUTER_API_URL,
    OPENROUTER_MODEL,
    OPENROUTER_API_KEY_ENV_VAR,
    API_REQUEST_TIMEOUT_SECONDS,
    MAX_COMPLETION_TOKENS,
)
from .types import ChatMessage, PortfolioData, OpenRouterRequest
from .utils import build_portfolio_summary, sanitize_history
from .prompts import get_system_prompt

logger = logging.getLogger(__name__)


@dataclass
class ChatResponse:
    """Response from chat service."""
    success: bool
    reply: Optional[str] = None
    error: Optional[str] = None
    status_code: int = 200


class PortfolioService:
    """Service for managing portfolio data."""
    
    def __init__(self, data_file_path: Path):
        """
        Initialize portfolio service.
        
        Args:
            data_file_path: Path to data.json file
        """
        self.data_file_path = data_file_path
        self._cache: Optional[PortfolioData] = None
    
    def load_data(self) -> Optional[PortfolioData]:
        """
        Load portfolio data from file.
        
        Data is loaded fresh on each call to pick up file changes
        without requiring server restart.
        
        Returns:
            Portfolio data or None if file missing/invalid
        """
        try:
            with open(self.data_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info("Successfully loaded portfolio data")
                return data
        except FileNotFoundError:
            logger.error("Portfolio data file not found: %s", self.data_file_path)
            return None
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in portfolio data: %s", e)
            return None
        except Exception as e:
            logger.error("Unexpected error loading portfolio data: %s", e)
            return None
    
    def get_summary(self) -> Optional[str]:
        """
        Get compact portfolio summary for AI context.
        
        Returns:
            Formatted portfolio summary or None if data unavailable
        """
        data = self.load_data()
        if data is None:
            return None
        return build_portfolio_summary(data)

    def find_project(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Find a project by name (case-insensitive match).

        Args:
            name: Project name or partial name to search for

        Returns:
            The project dict if found, otherwise None
        """
        data = self.load_data()
        if not data:
            return None

        projects = data.get("projects") or []
        if not isinstance(projects, list):
            return None

        name_lower = (name or "").strip().lower()
        for proj in projects:
            if not isinstance(proj, dict):
                continue
            proj_name = proj.get("name", "")
            if not proj_name:
                continue
            if proj_name.strip().lower() == name_lower or name_lower in proj_name.strip().lower():
                return proj

        return None

    def get_project_links(self, name: str) -> Optional[Dict[str, str]]:
        """
        Return available links for a project (live_url, github_url, repository, etc.).

        Args:
            name: Project name or partial name

        Returns:
            Dict of link type -> url, or None if project not found
        """
        proj = self.find_project(name)
        if not proj:
            return None

        links: Dict[str, str] = {}
        for key in ("live_url", "github_url", "repository", "repo", "url"):
            val = proj.get(key)
            if isinstance(val, str) and val:
                links[key] = val

        return links if links else None

    def list_project_links(self) -> Dict[str, Dict[str, str]]:
        """
        Return a mapping of project name to available links for all projects.

        Returns:
            Dict where keys are project names and values are dicts of link-type->url
        """
        data = self.load_data()
        if not data:
            return {}
        projects = data.get("projects") or []
        out: Dict[str, Dict[str, str]] = {}
        for proj in projects:
            if not isinstance(proj, dict):
                continue
            name = proj.get("name") or ""
            if not name:
                continue
            links: Dict[str, str] = {}
            for key in ("live_url", "github_url", "repository", "repo", "url"):
                val = proj.get(key)
                if isinstance(val, str) and val:
                    links[key] = val
            if links:
                out[name] = links

        return out


class AIService:
    """Service for interacting with OpenRouter AI API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize AI service.
        
        Args:
            api_key: OpenRouter API key (defaults to env var)
        """
        self.api_key = api_key or os.getenv(OPENROUTER_API_KEY_ENV_VAR)
        self.model = OPENROUTER_MODEL
        self.api_url = OPENROUTER_API_URL
    
    def is_configured(self) -> bool:
        """Check if API credentials are configured."""
        return bool(self.api_key)
    
    def _build_request_payload(
        self,
        system_prompt: str,
        history: List[ChatMessage],
        user_message: str
    ) -> OpenRouterRequest:
        """
        Build request payload for OpenRouter API.
        
        Args:
            system_prompt: System instruction prompt
            history: Previous conversation messages
            user_message: Current user message
            
        Returns:
            Formatted request payload
        """
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add history
        messages.extend(history)
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        return {
            "model": self.model,
            "messages": messages,
            "max_tokens": MAX_COMPLETION_TOKENS,
        }
    
    def get_response(
        self,
        user_message: str,
        history: List[ChatMessage],
        portfolio_summary: str
    ) -> ChatResponse:
        """
        Get AI response to user message.
        
        Args:
            user_message: User's input message
            history: Previous conversation messages
            portfolio_summary: Portfolio summary for context
            
        Returns:
            ChatResponse with success status and reply or error
        """
        if not self.is_configured():
            logger.error("API key not configured")
            return ChatResponse(
                success=False,
                error="Chat service not configured",
                status_code=503
            )
        
        # Clean history
        clean_history = sanitize_history(history)
        
        # Build system prompt
        system_prompt = get_system_prompt(portfolio_summary)
        
        # Build request
        payload = self._build_request_payload(
            system_prompt,
            clean_history,
            user_message
        )
        
        # Make API call
        return self._call_api(payload)
    
    def _call_api(self, payload: OpenRouterRequest) -> ChatResponse:
        """
        Make HTTP request to OpenRouter API.
        
        Args:
            payload: Request payload
            
        Returns:
            ChatResponse with API response or error
        """
        try:
            response = requests.post(
                self.api_url,
                headers=self._build_headers(),
                json=payload,
                timeout=API_REQUEST_TIMEOUT_SECONDS,
            )
            
            return self._parse_response(response)
        
        except requests.exceptions.Timeout:
            logger.error("API request timed out")
            return ChatResponse(
                success=False,
                error="AI service timed out. Try again.",
                status_code=504
            )
        
        except requests.exceptions.RequestException as e:
            logger.error("API request failed: %s", e)
            return ChatResponse(
                success=False,
                error="Unable to reach AI service. Try again later.",
                status_code=502
            )
        
        except Exception as e:
            logger.error("Unexpected error in API call: %s", e)
            return ChatResponse(
                success=False,
                error=str(e),
                status_code=500
            )
    
    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers for API request."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://portfolio-ai-bot.onrender.com",
            "X-Title": "Hudson Portfolio AI"
        }
    
    def _parse_response(self, response: requests.Response) -> ChatResponse:
        """
        Parse OpenRouter API response.
        
        Args:
            response: HTTP response from API
            
        Returns:
            ChatResponse with parsed result or error
        """
        try:
            result = response.json()
        except (ValueError, requests.exceptions.JSONDecodeError):
            logger.warning(
                "API returned non-JSON response (status=%s)",
                response.status_code
            )
            return ChatResponse(
                success=False,
                error="AI service returned an invalid response. Try again later.",
                status_code=502
            )
        
        # Check for API errors
        if not response.ok:
            error_msg = self._extract_error_message(result)
            logger.error("API error (status=%s): %s", response.status_code, error_msg)
            return ChatResponse(
                success=False,
                error=error_msg,
                status_code=response.status_code
            )
        
        # Check for choices in response
        if "choices" not in result or not result["choices"]:
            logger.error("No choices in API response: %s", result)
            return ChatResponse(
                success=False,
                error="API returned an invalid response",
                status_code=500
            )
        
        # Extract reply
        reply = result["choices"][0].get("message", {}).get("content", "").strip()
        
        if not reply:
            logger.error("API returned empty reply")
            return ChatResponse(
                success=False,
                error="AI returned an empty reply.",
                status_code=500
            )
        
        logger.info("Successfully got AI response")
        return ChatResponse(success=True, reply=reply)
    
    @staticmethod
    def _extract_error_message(result: Dict[str, Any]) -> str:
        """Extract error message from API response."""
        error = result.get("error", {})
        
        if isinstance(error, dict):
            return error.get("message", "API Error")
        
        return str(error) if error else "API Error"


class ChatManager:
    """Orchestrator for chat operations combining services."""
    
    def __init__(
        self,
        portfolio_service: PortfolioService,
        ai_service: AIService
    ):
        """
        Initialize chat manager.
        
        Args:
            portfolio_service: Service for portfolio data
            ai_service: Service for AI interactions
        """
        self.portfolio_service = portfolio_service
        self.ai_service = ai_service
    
    def process_chat(
        self,
        user_message: str,
        history: List[ChatMessage]
    ) -> ChatResponse:
        """
        Process user message and return AI response.
        
        Combines portfolio context with AI service to generate response.
        
        Args:
            user_message: User's input message
            history: Previous conversation messages
            
        Returns:
            ChatResponse with AI response or error
        """
        # Verify AI is configured
        if not self.ai_service.is_configured():
            logger.error("AI service not configured")
            return ChatResponse(
                success=False,
                error="Chat is not configured",
                status_code=503
            )
        
        # Load portfolio data
        portfolio_summary = self.portfolio_service.get_summary()
        if portfolio_summary is None:
            logger.error("Failed to load portfolio data")
            return ChatResponse(
                success=False,
                error="Portfolio data is missing or invalid",
                status_code=503
            )
        
        # Get AI response
        return self.ai_service.get_response(
            user_message,
            history,
            portfolio_summary
        )
