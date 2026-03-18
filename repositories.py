"""
Database repository classes for data access operations.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    BlockedNumber,
    CommandAlias,
    CommandLog,
    GameState,
    RateLimit,
    Reminder,
    SpamPattern,
    SystemSetting,
    User,
    UserTier,
)


class UserRepository:
    """Repository for User operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_phone(self, phone_number: str) -> Optional[User]:
        """Get user by phone number."""
        result = await self.session.execute(
            select(User).where(User.phone_number == phone_number)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create(self, phone_number: str, name: Optional[str] = None, tier: UserTier = UserTier.GUEST) -> User:
        """Create a new user."""
        user = User(
            phone_number=phone_number,
            name=name,
            tier=tier,
            daily_reset_at=datetime.utcnow(),
        )
        self.session.add(user)
        await self.session.flush()
        return user
    
    async def get_or_create(self, phone_number: str, name: Optional[str] = None) -> User:
        """Get existing user or create new one."""
        user = await self.get_by_phone(phone_number)
        if not user:
            user = await self.create(phone_number, name)
        return user
    
    async def update_activity(self, user_id: int) -> None:
        """Update user's last activity timestamp."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_activity=datetime.utcnow())
        )
    
    async def increment_command_count(self, user_id: int) -> None:
        """Increment user's command count."""
        user = await self.get_by_id(user_id)
        if not user:
            return
        
        now = datetime.utcnow()
        
        # Reset daily count if needed
        if user.daily_reset_at and user.daily_reset_at.date() != now.date():
            user.daily_command_count = 0
            user.daily_reset_at = now
        
        user.command_count += 1
        user.daily_command_count += 1
        user.last_activity = now
        
        await self.session.flush()
    
    async def get_daily_limit(self, tier: UserTier) -> int:
        """Get daily command limit for tier."""
        from app.config import settings
        
        limits = {
            UserTier.GUEST: settings.TIER_GUEST_DAILY_LIMIT,
            UserTier.USER: settings.TIER_USER_DAILY_LIMIT,
            UserTier.PREMIUM: settings.TIER_PREMIUM_DAILY_LIMIT,
            UserTier.ADMIN: float('inf') if settings.TIER_ADMIN_UNLIMITED else 1000,
        }
        return limits.get(tier, 20)
    
    async def can_execute_command(self, user: User) -> bool:
        """Check if user can execute more commands today."""
        if user.tier == UserTier.ADMIN:
            return True
        
        limit = await self.get_daily_limit(user.tier)
        return user.daily_command_count < limit
    
    async def update_tier(self, user_id: int, tier: UserTier) -> None:
        """Update user's tier."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(tier=tier, updated_at=datetime.utcnow())
        )
    
    async def block_user(self, user_id: int) -> None:
        """Block a user."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_blocked=True, is_active=False, updated_at=datetime.utcnow())
        )
    
    async def unblock_user(self, user_id: int) -> None:
        """Unblock a user."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_blocked=False, is_active=True, updated_at=datetime.utcnow())
        )
    
    async def get_stats(self) -> dict:
        """Get user statistics."""
        total = await self.session.execute(select(func.count(User.id)))
        active = await self.session.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        by_tier = await self.session.execute(
            select(User.tier, func.count(User.id)).group_by(User.tier)
        )
        
        return {
            "total_users": total.scalar(),
            "active_users": active.scalar(),
            "by_tier": {tier.value: count for tier, count in by_tier.all()},
        }


class CommandLogRepository:
    """Repository for CommandLog operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def log_command(
        self,
        user_id: int,
        command: str,
        args: Optional[str] = None,
        response: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> CommandLog:
        """Log a command execution."""
        log = CommandLog(
            user_id=user_id,
            command=command,
            args=args,
            response=response[:1000] if response else None,
            execution_time_ms=execution_time_ms,
            success=success,
            error_message=error_message,
        )
        self.session.add(log)
        await self.session.flush()
        return log
    
    async def get_recent_commands(self, user_id: int, limit: int = 10) -> List[CommandLog]:
        """Get recent commands for a user."""
        result = await self.session.execute(
            select(CommandLog)
            .where(CommandLog.user_id == user_id)
            .order_by(desc(CommandLog.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_popular_commands(self, limit: int = 10) -> List[tuple]:
        """Get most popular commands."""
        result = await self.session.execute(
            select(CommandLog.command, func.count(CommandLog.id))
            .group_by(CommandLog.command)
            .order_by(desc(func.count(CommandLog.id)))
            .limit(limit)
        )
        return result.all()


class ReminderRepository:
    """Repository for Reminder operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        user_id: int,
        message: str,
        scheduled_at: datetime,
        timezone: str = "UTC",
        is_recurring: bool = False,
        recurrence_pattern: Optional[str] = None,
    ) -> Reminder:
        """Create a new reminder."""
        reminder = Reminder(
            user_id=user_id,
            message=message,
            scheduled_at=scheduled_at,
            timezone=timezone,
            is_recurring=is_recurring,
            recurrence_pattern=recurrence_pattern,
        )
        self.session.add(reminder)
        await self.session.flush()
        return reminder
    
    async def get_by_id(self, reminder_id: int) -> Optional[Reminder]:
        """Get reminder by ID."""
        result = await self.session.execute(
            select(Reminder).where(Reminder.id == reminder_id)
        )
        return result.scalar_one_or_none()
    
    async def get_pending_reminders(self, before: datetime) -> List[Reminder]:
        """Get pending reminders scheduled before a time."""
        result = await self.session.execute(
            select(Reminder)
            .where(
                and_(
                    Reminder.scheduled_at <= before,
                    Reminder.is_completed == False,
                    Reminder.is_cancelled == False,
                )
            )
            .order_by(Reminder.scheduled_at)
        )
        return result.scalars().all()
    
    async def get_user_reminders(self, user_id: int, active_only: bool = True) -> List[Reminder]:
        """Get reminders for a user."""
        query = select(Reminder).where(Reminder.user_id == user_id)
        
        if active_only:
            query = query.where(
                and_(
                    Reminder.is_completed == False,
                    Reminder.is_cancelled == False,
                )
            )
        
        query = query.order_by(Reminder.scheduled_at)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def mark_completed(self, reminder_id: int) -> None:
        """Mark a reminder as completed."""
        await self.session.execute(
            update(Reminder)
            .where(Reminder.id == reminder_id)
            .values(is_completed=True, completed_at=datetime.utcnow())
        )
    
    async def cancel(self, reminder_id: int) -> None:
        """Cancel a reminder."""
        await self.session.execute(
            update(Reminder)
            .where(Reminder.id == reminder_id)
            .values(is_cancelled=True)
        )
    
    async def update_task_id(self, reminder_id: int, task_id: str) -> None:
        """Update Celery task ID for a reminder."""
        await self.session.execute(
            update(Reminder)
            .where(Reminder.id == reminder_id)
            .values(celery_task_id=task_id)
        )


class GameStateRepository:
    """Repository for GameState operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_active_game(self, user_id: int, game_type: str) -> Optional[GameState]:
        """Get active game state for user."""
        result = await self.session.execute(
            select(GameState)
            .where(
                and_(
                    GameState.user_id == user_id,
                    GameState.game_type == game_type,
                    GameState.is_active == True,
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def create_or_update(
        self,
        user_id: int,
        game_type: str,
        state_data: dict,
        score: int = 0,
        moves: int = 0,
    ) -> GameState:
        """Create or update game state."""
        existing = await self.get_active_game(user_id, game_type)
        
        if existing:
            existing.state_data = state_data
            existing.score = score
            existing.moves = moves
            existing.updated_at = datetime.utcnow()
            await self.session.flush()
            return existing
        
        game_state = GameState(
            user_id=user_id,
            game_type=game_type,
            state_data=state_data,
            score=score,
            moves=moves,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        self.session.add(game_state)
        await self.session.flush()
        return game_state
    
    async def end_game(self, user_id: int, game_type: str) -> None:
        """End an active game."""
        await self.session.execute(
            update(GameState)
            .where(
                and_(
                    GameState.user_id == user_id,
                    GameState.game_type == game_type,
                    GameState.is_active == True,
                )
            )
            .values(is_active=False)
        )
    
    async def get_user_games(self, user_id: int, limit: int = 10) -> List[GameState]:
        """Get user's recent games."""
        result = await self.session.execute(
            select(GameState)
            .where(GameState.user_id == user_id)
            .order_by(desc(GameState.created_at))
            .limit(limit)
        )
        return result.scalars().all()


class RateLimitRepository:
    """Repository for RateLimit operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_current_window(
        self, phone_number: str, window_start: datetime
    ) -> Optional[RateLimit]:
        """Get rate limit for current window."""
        result = await self.session.execute(
            select(RateLimit)
            .where(
                and_(
                    RateLimit.phone_number == phone_number,
                    RateLimit.window_start == window_start,
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def increment_request(
        self, phone_number: str, window_start: datetime
    ) -> RateLimit:
        """Increment request count for window."""
        existing = await self.get_current_window(phone_number, window_start)
        
        if existing:
            existing.request_count += 1
            await self.session.flush()
            return existing
        
        rate_limit = RateLimit(
            phone_number=phone_number,
            window_start=window_start,
            request_count=1,
        )
        self.session.add(rate_limit)
        await self.session.flush()
        return rate_limit
    
    async def block(
        self,
        phone_number: str,
        blocked_until: datetime,
        reason: str = "rate_limit_exceeded",
    ) -> None:
        """Block a phone number."""
        await self.session.execute(
            update(RateLimit)
            .where(RateLimit.phone_number == phone_number)
            .values(is_blocked=True, blocked_until=blocked_until, block_reason=reason)
        )
    
    async def is_blocked(self, phone_number: str) -> Optional[datetime]:
        """Check if phone number is blocked and return unblock time."""
        result = await self.session.execute(
            select(RateLimit)
            .where(
                and_(
                    RateLimit.phone_number == phone_number,
                    RateLimit.is_blocked == True,
                    RateLimit.blocked_until > datetime.utcnow(),
                )
            )
            .order_by(desc(RateLimit.blocked_until))
            .limit(1)
        )
        rate_limit = result.scalar_one_or_none()
        return rate_limit.blocked_until if rate_limit else None


class BlockedNumberRepository:
    """Repository for BlockedNumber operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def is_blocked(self, phone_number: str) -> bool:
        """Check if phone number is permanently blocked."""
        result = await self.session.execute(
            select(BlockedNumber)
            .where(
                and_(
                    BlockedNumber.phone_number == phone_number,
                    BlockedNumber.expires_at > datetime.utcnow(),
                )
            )
        )
        return result.scalar_one_or_none() is not None


class CommandAliasRepository:
    """Repository for CommandAlias operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_command(self, alias: str) -> Optional[str]:
        """Get command for alias."""
        result = await self.session.execute(
            select(CommandAlias.command)
            .where(CommandAlias.alias == alias.lower())
        )
        command = result.scalar_one_or_none()
        
        if command:
            # Increment usage count
            await self.session.execute(
                update(CommandAlias)
                .where(CommandAlias.alias == alias.lower())
                .values(usage_count=CommandAlias.usage_count + 1)
            )
        
        return command
    
    async def create_alias(self, alias: str, command: str, description: Optional[str] = None) -> CommandAlias:
        """Create a new command alias."""
        alias_obj = CommandAlias(
            alias=alias.lower(),
            command=command.lower(),
            description=description,
        )
        self.session.add(alias_obj)
        await self.session.flush()
        return alias_obj
    
    async def get_all_aliases(self) -> List[CommandAlias]:
        """Get all command aliases."""
        result = await self.session.execute(select(CommandAlias))
        return result.scalars().all()


class SystemSettingRepository:
    """Repository for SystemSetting operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get setting value."""
        result = await self.session.execute(
            select(SystemSetting.value).where(SystemSetting.key == key)
        )
        value = result.scalar_one_or_none()
        return value if value is not None else default
    
    async def set(
        self,
        key: str,
        value: str,
        value_type: str = "string",
        description: Optional[str] = None,
        updated_by: Optional[str] = None,
    ) -> None:
        """Set setting value."""
        existing = await self.session.execute(
            select(SystemSetting).where(SystemSetting.key == key)
        )
        
        if existing.scalar_one_or_none():
            await self.session.execute(
                update(SystemSetting)
                .where(SystemSetting.key == key)
                .values(
                    value=value,
                    value_type=value_type,
                    description=description,
                    updated_by=updated_by,
                )
            )
        else:
            setting = SystemSetting(
                key=key,
                value=value,
                value_type=value_type,
                description=description,
                updated_by=updated_by,
            )
            self.session.add(setting)
        
        await self.session.flush()
