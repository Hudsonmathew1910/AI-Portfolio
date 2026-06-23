"""
Utility functions for the chat application.

This module provides reusable helper functions for common tasks
like data validation, formatting, and text processing.
"""

import logging
from typing import List, Dict, Any, Optional
from .constants import MAX_HISTORY_ITEMS, MAX_MESSAGE_LENGTH
from .types import ChatMessage

logger = logging.getLogger(__name__)


def sanitize_history(history: Any) -> List[ChatMessage]:
    """
    Clean and validate chat history to ensure security and consistency.
    
    - Validates that all items have required fields (role, content)
    - Filters out invalid messages
    - Truncates history to prevent token overflow
    - Limits individual message length
    
    Args:
        history: Raw history from request (should be list of dicts)
        
    Returns:
        List of validated ChatMessage objects
    """
    if not isinstance(history, list):
        logger.warning("History is not a list: %s", type(history))
        return []

    cleaned: List[ChatMessage] = []
    
    for item in history[-MAX_HISTORY_ITEMS:]:
        if not isinstance(item, dict):
            logger.debug("Skipping non-dict history item: %s", type(item))
            continue
            
        role = item.get("role")
        content = item.get("content")
        
        # Validate role
        if role not in {"user", "assistant"}:
            logger.debug("Skipping message with invalid role: %s", role)
            continue
        
        # Validate content
        if not isinstance(content, str):
            logger.debug("Skipping message with non-string content")
            continue
            
        # Clean whitespace
        text = content.strip()
        if not text:
            logger.debug("Skipping empty message")
            continue
        
        # Truncate if too long
        if len(text) > MAX_MESSAGE_LENGTH:
            logger.warning(
                "Truncating message from %d to %d chars",
                len(text),
                MAX_MESSAGE_LENGTH
            )
            text = text[:MAX_MESSAGE_LENGTH]
        
        cleaned.append({"role": role, "content": text})
    
    return cleaned


def build_portfolio_summary(data: Optional[Dict[str, Any]]) -> str:
    """
    Build a concise portfolio summary from full portfolio data.
    
    Extracts key information while staying within token limits:
    - Basic info (name, summary)
    - Education details
    - Internship experience
    - Project highlights
    - Core skills
    - Career focus
    
    Args:
        data: Portfolio data dictionary from data.json
        
    Returns:
        Formatted portfolio summary text
    """
    if not data or not isinstance(data, dict):
        logger.warning("Invalid portfolio data: %s", type(data))
        return str(data or "")

    parts: List[str] = []

    # Add basic information
    if data.get("name"):
        parts.append(f"Name: {data['name']}")
    
    if data.get("summary"):
        parts.append(f"Summary: {data['summary']}")

    # Add education
    education = data.get("education") or {}
    if isinstance(education, dict) and (education.get("degree") or education.get("institution")):
        degree = education.get("degree", "")
        institution = education.get("institution", "")
        year = education.get("year", "")
        edu_text = f"Education: {degree} from {institution}"
        if year:
            edu_text += f" ({year})"
        parts.append(edu_text.strip())

    # Add internship
    internship = data.get("internship") or {}
    if isinstance(internship, dict) and internship.get("company"):
        role = internship.get("role", "")
        company = internship.get("company", "")
        duration = internship.get("duration", "")
        intern_text = f"Internship: {role} at {company}"
        if duration:
            intern_text += f", {duration}"
        parts.append(intern_text.strip())

    # Add projects (truncated)
    projects = data.get("projects") or []
    if isinstance(projects, list) and projects:
        project_lines: List[str] = []
        for proj in projects[:6]:
            if not isinstance(proj, dict):
                continue
            name = proj.get("name")
            overview = proj.get("overview", "")
            if name:
                if overview:
                    project_lines.append(f"- {name}: {overview[:120]}")
                else:
                    project_lines.append(f"- {name}")
        
        if project_lines:
            parts.append("Projects: " + " ".join(project_lines))

    # Add skills
    skills = data.get("skills") or {}
    if isinstance(skills, dict):
        all_skills: List[str] = []
        for skill_list in skills.values():
            if isinstance(skill_list, list):
                all_skills.extend(skill_list[:8])
            elif skill_list:
                all_skills.append(str(skill_list))
        
        if all_skills:
            parts.append("Skills: " + ", ".join(all_skills[:20]))

    # Add focus
    if data.get("focus"):
        parts.append(f"Focus: {data['focus']}")

    return "\n".join(parts)


def escape_html(text: str) -> str:
    """
    Escape HTML special characters in text.
    
    Prevents XSS attacks by escaping dangerous characters.
    
    Args:
        text: Raw text to escape
        
    Returns:
        HTML-escaped text
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def validate_chat_message(message: str) -> tuple[bool, Optional[str]]:
    """
    Validate user chat message.
    
    Args:
        message: Message text to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(message, str):
        return False, "Message must be a string"
    
    text = message.strip()
    
    if not text:
        return False, "Message cannot be empty"
    
    if len(text) > 5000:
        return False, "Message is too long (max 5000 characters)"
    
    return True, None
