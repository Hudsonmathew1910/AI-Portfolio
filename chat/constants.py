"""
Constants for the chat application.

This module contains all application-level constants to maintain
consistency and facilitate easy configuration updates.
"""

from typing import Final

# API Configuration
OPENROUTER_API_URL: Final[str] = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL: Final[str] = "openai/gpt-4o-mini"
OPENROUTER_API_KEY_ENV_VAR: Final[str] = "HUDDY_OPENROUTER_API_KEY_1"

# Request Configuration
API_REQUEST_TIMEOUT_SECONDS: Final[int] = 45
MAX_COMPLETION_TOKENS: Final[int] = 180
MAX_HISTORY_ITEMS: Final[int] = 12
MAX_MESSAGE_LENGTH: Final[int] = 800

# File Configuration
DATA_JSON_FILENAME: Final[str] = "data.json"

# Error Messages
ERROR_API_NOT_CONFIGURED: Final[str] = (
    "Chat is not configured. Set HUDDY_OPENROUTER_API_KEY_1 in .env."
)
ERROR_PORTFOLIO_DATA_MISSING: Final[str] = (
    "Portfolio data (data.json) is missing or invalid."
)
ERROR_INVALID_REQUEST: Final[str] = "Invalid request"
ERROR_MESSAGE_REQUIRED: Final[str] = "Message required"
ERROR_INVALID_JSON: Final[str] = "Invalid JSON in request body."
ERROR_API_TIMEOUT: Final[str] = "AI service timed out. Try again."
ERROR_API_UNREACHABLE: Final[str] = "Unable to reach AI service. Try again later."
ERROR_API_INVALID_RESPONSE: Final[str] = (
    "AI service returned an invalid response. Try again later."
)
ERROR_EMPTY_REPLY: Final[str] = "AI returned an empty reply."

# HTTP Status Codes
STATUS_OK: Final[int] = 200
STATUS_BAD_REQUEST: Final[int] = 400
STATUS_SERVER_ERROR: Final[int] = 500
STATUS_SERVICE_UNAVAILABLE: Final[int] = 503
STATUS_BAD_GATEWAY: Final[int] = 502
STATUS_GATEWAY_TIMEOUT: Final[int] = 504
