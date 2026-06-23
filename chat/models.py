"""
Database models for the chat application.

This module defines Django ORM models for persistent data storage.
Currently, the application primarily uses file-based data (data.json)
for portfolio information. These models can be extended for features like:
- Conversation history storage
- User preferences
- Analytics and usage tracking
"""

from django.db import models
from django.utils import timezone


class ChatSession(models.Model):
    """
    Model to store chat session information.
    
    Future enhancement: Store conversation sessions and user interactions
    for analytics, improvement, and conversation recovery.
    """
    
    session_id = models.CharField(
        max_length=36,
        unique=True,
        help_text="UUID for session identification"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when session was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp of last activity"
    )
    
    user_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="User's IP address (for analytics)"
    )
    
    message_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of messages in session"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['session_id']),
        ]
        verbose_name = "Chat Session"
        verbose_name_plural = "Chat Sessions"
    
    def __str__(self) -> str:
        """String representation of chat session."""
        return f"Session {self.session_id[:8]}... ({self.message_count} messages)"


class ChatMessage(models.Model):
    """
    Model to store individual chat messages.
    
    Persists conversation history for session recovery,
    analytics, and continuous improvement.
    """
    
    ROLE_CHOICES = [
        ('user', 'User Message'),
        ('assistant', 'Assistant Response'),
    ]
    
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text="Associated chat session"
    )
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        help_text="Message sender role"
    )
    
    content = models.TextField(
        help_text="Message content"
    )
    
    tokens_used = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Approximate tokens used (for API tracking)"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when message was created"
    )
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
            models.Index(fields=['role']),
        ]
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"
    
    def __str__(self) -> str:
        """String representation of chat message."""
        preview = self.content[:50]
        return f"{self.get_role_display()}: {preview}..."


class PortfolioDataSnapshot(models.Model):
    """
    Model to store snapshots of portfolio data.
    
    Tracks changes to data.json over time for auditing,
    recovery, and historical analysis.
    """
    
    data_json = models.JSONField(
        help_text="Full portfolio data snapshot"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when snapshot was created"
    )
    
    hash_value = models.CharField(
        max_length=64,
        unique=True,
        help_text="SHA256 hash of data for duplicate detection"
    )
    
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Manual description of changes"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['hash_value']),
        ]
        verbose_name = "Portfolio Data Snapshot"
        verbose_name_plural = "Portfolio Data Snapshots"
    
    def __str__(self) -> str:
        """String representation of portfolio snapshot."""
        return f"Snapshot {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

