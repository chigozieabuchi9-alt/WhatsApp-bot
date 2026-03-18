"""
Database models for the WhatsApp bot.
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from db.database import Base


class UserTier(str, enum.Enum):
    """User tier levels."""
    GUEST = "guest"
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"


class User(Base):
    """User model for WhatsApp users."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    tier = Column(Enum(UserTier), default=UserTier.GUEST, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_activity = Column(DateTime(timezone=True))
    command_count = Column(BigInteger, default=0, nullable=False)
    daily_command_count = Column(Integer, default=0, nullable=False)
    daily_reset_at = Column(DateTime(timezone=True))
    preferred_language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    metadata_json = Column(JSON, default=dict)
    
    # Relationships
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    game_states = relationship("GameState", back_populates="user", cascade="all, delete-orphan")
    command_logs = relationship("CommandLog", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_users_tier", "tier"),
        Index("ix_users_is_active", "is_active"),
    )


class CommandLog(Base):
    """Log of all commands executed."""
    __tablename__ = "command_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    command = Column(String(100), nullable=False, index=True)
    args = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ip_address = Column(String(45), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="command_logs")
    
    __table_args__ = (
        Index("ix_command_logs_created_at", "created_at"),
        Index("ix_command_logs_user_id_created_at", "user_id", "created_at"),
    )


class Reminder(Base):
    """Reminder model for scheduled notifications."""
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    timezone = Column(String(50), default="UTC")
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurrence_pattern = Column(String(50), nullable=True)  # daily, weekly, monthly
    is_completed = Column(Boolean, default=False, nullable=False)
    is_cancelled = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    celery_task_id = Column(String(100), nullable=True, index=True)
    
    # Relationships
    user = relationship("User", back_populates="reminders")
    
    __table_args__ = (
        Index("ix_reminders_scheduled_at", "scheduled_at"),
        Index("ix_reminders_user_id", "user_id"),
        Index("ix_reminders_is_completed", "is_completed"),
    )


class GameState(Base):
    """Game state storage for active games."""
    __tablename__ = "game_states"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    game_type = Column(String(50), nullable=False, index=True)
    state_data = Column(JSON, default=dict, nullable=False)
    score = Column(Integer, default=0, nullable=False)
    moves = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="game_states")
    
    __table_args__ = (
        Index("ix_game_states_user_id_game_type", "user_id", "game_type"),
        Index("ix_game_states_is_active", "is_active"),
    )


class RateLimit(Base):
    """Rate limiting tracking."""
    __tablename__ = "rate_limits"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), nullable=False, index=True)
    window_start = Column(DateTime(timezone=True), nullable=False, index=True)
    request_count = Column(Integer, default=1, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)
    blocked_until = Column(DateTime(timezone=True), nullable=True)
    block_reason = Column(String(200), nullable=True)
    
    __table_args__ = (
        Index("ix_rate_limits_phone_number_window", "phone_number", "window_start"),
    )


class SpamPattern(Base):
    """Known spam patterns for filtering."""
    __tablename__ = "spam_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    pattern = Column(String(500), nullable=False, unique=True)
    pattern_type = Column(String(50), default="regex", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    hit_count = Column(BigInteger, default=0, nullable=False)
    description = Column(Text, nullable=True)


class BlockedNumber(Base):
    """Permanently blocked phone numbers."""
    __tablename__ = "blocked_numbers"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    reason = Column(Text, nullable=True)
    blocked_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)


class CommandAlias(Base):
    """Command aliases mapping."""
    __tablename__ = "command_aliases"
    
    id = Column(Integer, primary_key=True, index=True)
    alias = Column(String(50), unique=True, nullable=False, index=True)
    command = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    usage_count = Column(BigInteger, default=0, nullable=False)


class SystemSetting(Base):
    """System configuration settings."""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(20), default="string", nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(String(100), nullable=True)
