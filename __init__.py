"""
Commands package - imports all command modules to register commands.
"""
# Import all command modules to register commands with the registry
from commands import (
    admin,
    ai,
    fun,
    games,
    general,
    media,
    news,
    productivity,
    reminders,
    security,
    social,
    utilities,
    weather,
)
from commands.base import registry

__all__ = ["registry"]
