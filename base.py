"""
Base command system and registry.
"""
import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.logging_config import get_logger
from db.models import User, UserTier
from db.repositories import CommandAliasRepository, UserRepository
from utils.rate_limiter import command_cooldown

logger = get_logger(__name__)


@dataclass
class CommandContext:
    """Context passed to command handlers."""
    user: User
    phone_number: str
    args: List[str]
    raw_message: str
    db: AsyncSession
    
    @property
    def args_str(self) -> str:
        """Get arguments as string."""
        return " ".join(self.args)


@dataclass
class CommandResult:
    """Result of command execution."""
    success: bool
    message: str
    extra_data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None


class Command(ABC):
    """Base command class."""
    
    name: str = ""
    description: str = ""
    aliases: List[str] = []
    category: str = "general"
    min_args: int = 0
    max_args: int = -1  # -1 means unlimited
    required_tier: UserTier = UserTier.GUEST
    cooldown_seconds: int = 1
    usage_examples: List[str] = []
    
    def __init__(self):
        self.logger = get_logger(f"command.{self.name}")
    
    @abstractmethod
    async def execute(self, ctx: CommandContext) -> CommandResult:
        """Execute the command."""
        pass
    
    def validate_args(self, args: List[str]) -> tuple[bool, Optional[str]]:
        """Validate command arguments."""
        if len(args) < self.min_args:
            return False, f"This command requires at least {self.min_args} argument(s)"
        
        if self.max_args >= 0 and len(args) > self.max_args:
            return False, f"This command accepts at most {self.max_args} argument(s)"
        
        return True, None
    
    def check_tier(self, user_tier: UserTier) -> bool:
        """Check if user has required tier."""
        tier_levels = {
            UserTier.GUEST: 0,
            UserTier.USER: 1,
            UserTier.PREMIUM: 2,
            UserTier.ADMIN: 3,
        }
        return tier_levels.get(user_tier, 0) >= tier_levels.get(self.required_tier, 0)
    
    def get_help_text(self) -> str:
        """Get formatted help text for this command."""
        lines = [
            f"📋 *Command: !{self.name}*",
            f"",
            f"📝 Description: {self.description}",
        ]
        
        if self.aliases:
            lines.append(f"🔗 Aliases: {', '.join(f'!{a}' for a in self.aliases)}")
        
        lines.append(f"👤 Required tier: {self.required_tier.value}")
        
        if self.usage_examples:
            lines.append(f"")
            lines.append(f"💡 Examples:")
            for example in self.usage_examples:
                lines.append(f"   {example}")
        
        return "\n".join(lines)


class CommandRegistry:
    """Registry for all commands."""
    
    def __init__(self):
        self.commands: Dict[str, Command] = {}
        self.categories: Dict[str, List[str]] = {}
        self.logger = get_logger("command_registry")
    
    def register(self, command_class: type) -> type:
        """Register a command class (decorator)."""
        instance = command_class()
        self.commands[instance.name] = instance
        
        # Register aliases
        for alias in instance.aliases:
            self.commands[alias] = instance
        
        # Add to category
        if instance.category not in self.categories:
            self.categories[instance.category] = []
        self.categories[instance.category].append(instance.name)
        
        self.logger.info(
            "command_registered",
            name=instance.name,
            category=instance.category,
            aliases=instance.aliases,
        )
        
        return command_class
    
    def get(self, name: str) -> Optional[Command]:
        """Get command by name or alias."""
        return self.commands.get(name.lower())
    
    def get_by_category(self, category: str) -> List[Command]:
        """Get all commands in a category."""
        names = self.categories.get(category, [])
        # Return unique commands (not aliases)
        seen = set()
        result = []
        for name in names:
            cmd = self.commands.get(name)
            if cmd and cmd.name not in seen:
                seen.add(cmd.name)
                result.append(cmd)
        return result
    
    def get_all_categories(self) -> List[str]:
        """Get all category names."""
        return list(self.categories.keys())
    
    def get_all_commands(self) -> List[Command]:
        """Get all unique commands (not aliases)."""
        seen = set()
        result = []
        for cmd in self.commands.values():
            if cmd.name not in seen:
                seen.add(cmd.name)
                result.append(cmd)
        return result
    
    async def execute(
        self,
        command_name: str,
        ctx: CommandContext,
    ) -> CommandResult:
        """Execute a command by name."""
        start_time = time.time()
        
        # Resolve alias
        alias_repo = CommandAliasRepository(ctx.db)
        resolved_name = await alias_repo.get_command(command_name)
        if resolved_name:
            command_name = resolved_name
        
        command = self.get(command_name)
        
        if not command:
            return CommandResult(
                success=False,
                message=f"❌ Unknown command: !{command_name}\n\nType !help to see available commands.",
                error_code="unknown_command",
            )
        
        # Check tier
        if not command.check_tier(ctx.user.tier):
            return CommandResult(
                success=False,
                message=f"🔒 This command requires {command.required_tier.value} tier or higher.",
                error_code="insufficient_tier",
            )
        
        # Validate arguments
        valid, error = command.validate_args(ctx.args)
        if not valid:
            return CommandResult(
                success=False,
                message=f"❌ {error}\n\n{command.get_help_text()}",
                error_code="invalid_args",
            )
        
        # Check cooldown
        can_execute, remaining = await command_cooldown.check_cooldown(
            ctx.phone_number,
            command.name,
        )
        if not can_execute:
            return CommandResult(
                success=False,
                message=f"⏳ Please wait {remaining} second(s) before using this command again.",
                error_code="cooldown",
            )
        
        try:
            # Execute command
            result = await command.execute(ctx)
            
            # Set cooldown on success
            if result.success:
                await command_cooldown.set_cooldown(
                    ctx.phone_number,
                    command.name,
                    command.cooldown_seconds,
                )
                
                # Increment user command count
                user_repo = UserRepository(ctx.db)
                await user_repo.increment_command_count(ctx.user.id)
            
            execution_time = int((time.time() - start_time) * 1000)
            self.logger.info(
                "command_executed",
                command=command.name,
                user_id=ctx.user.id,
                success=result.success,
                execution_time_ms=execution_time,
            )
            
            return result
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            self.logger.error(
                "command_execution_failed",
                command=command.name,
                user_id=ctx.user.id,
                error=str(e),
                execution_time_ms=execution_time,
            )
            return CommandResult(
                success=False,
                message="❌ An error occurred while executing this command. Please try again later.",
                error_code="execution_error",
            )


# Global registry instance
registry = CommandRegistry()


def command(name: str = None, **kwargs):
    """Decorator to register a command."""
    def decorator(cls):
        if name:
            cls.name = name
        for key, value in kwargs.items():
            setattr(cls, key, value)
        return registry.register(cls)
    return decorator
