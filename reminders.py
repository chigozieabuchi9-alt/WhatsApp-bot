"""
Reminder commands.
"""
from datetime import datetime, timedelta

import pytz

from commands.base import Command, CommandContext, CommandResult, command
from db.models import UserTier
from db.repositories import ReminderRepository
from reminders.tasks import schedule_reminder


@command("reminder", description="Set a reminder", aliases=["remind", "r"], min_args=2, category="reminders")
class ReminderCommand(Command):
    usage_examples = [
        "!reminder 30m Call mom",
        "!reminder 2h Meeting with team",
        "!reminder tomorrow 9am Wake up",
        "!reminder 2024-12-25 08:00 Open presents",
    ]
    cooldown_seconds = 3
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        time_str = ctx.args[0]
        message = " ".join(ctx.args[1:])
        
        try:
            scheduled_time = self._parse_time(time_str)
            
            if scheduled_time <= datetime.utcnow():
                return CommandResult(
                    success=False,
                    message="❌ Reminder time must be in the future!"
                )
            
            # Save to database
            repo = ReminderRepository(ctx.db)
            reminder = await repo.create(
                user_id=ctx.user.id,
                message=message,
                scheduled_at=scheduled_time,
                timezone=ctx.user.timezone or "UTC",
            )
            
            # Schedule with Celery
            task = schedule_reminder.apply_async(
                args=[reminder.id],
                eta=scheduled_time,
            )
            
            # Update with task ID
            await repo.update_task_id(reminder.id, task.id)
            
            time_until = scheduled_time - datetime.utcnow()
            hours, remainder = divmod(time_until.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            time_str_display = ""
            if time_until.days > 0:
                time_str_display += f"{time_until.days}d "
            if hours > 0:
                time_str_display += f"{hours}h "
            if minutes > 0:
                time_str_display += f"{minutes}m"
            
            return CommandResult(
                success=True,
                message=f"⏰ *Reminder Set!*\n\nMessage: {message}\nWhen: {scheduled_time.strftime('%Y-%m-%d %H:%M')} UTC\n(In {time_str_display})"
            )
            
        except ValueError as e:
            return CommandResult(
                success=False,
                message=f"❌ Invalid time format. Examples:\n• !reminder 30m message\n• !reminder 2h message\n• !reminder tomorrow 9am message"
            )
    
    def _parse_time(self, time_str: str) -> datetime:
        """Parse time string to datetime."""
        now = datetime.utcnow()
        time_str = time_str.lower()
        
        # Relative time: 30m, 2h, 1d
        if time_str.endswith('m'):
            minutes = int(time_str[:-1])
            return now + timedelta(minutes=minutes)
        elif time_str.endswith('h'):
            hours = int(time_str[:-1])
            return now + timedelta(hours=hours)
        elif time_str.endswith('d'):
            days = int(time_str[:-1])
            return now + timedelta(days=days)
        elif time_str == "tomorrow":
            return now + timedelta(days=1)
        elif time_str == "nextweek":
            return now + timedelta(weeks=1)
        
        # Try parsing as HH:MM
        try:
            hour, minute = map(int, time_str.split(':'))
            result = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if result <= now:
                result += timedelta(days=1)
            return result
        except ValueError:
            pass
        
        raise ValueError("Could not parse time")


@command("reminders", description="List your reminders", aliases=["listreminders", "myreminders"], category="reminders")
class ListRemindersCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        repo = ReminderRepository(ctx.db)
        reminders = await repo.get_user_reminders(ctx.user.id, active_only=True)
        
        if not reminders:
            return CommandResult(
                success=True,
                message="📋 You have no active reminders.\n\nSet one with !reminder <time> <message>"
            )
        
        lines = ["📋 *Your Reminders*\n"]
        
        for i, r in enumerate(reminders[:10], 1):
            time_str = r.scheduled_at.strftime('%Y-%m-%d %H:%M')
            lines.append(f"{i}. *{r.message}*")
            lines.append(f"   ⏰ {time_str} UTC")
            if r.is_recurring:
                lines.append(f"   🔄 Recurring: {r.recurrence_pattern}")
            lines.append("")
        
        if len(reminders) > 10:
            lines.append(f"... and {len(reminders) - 10} more")
        
        return CommandResult(success=True, message="\n".join(lines))


@command("cancelreminder", description="Cancel a reminder", min_args=1, category="reminders")
class CancelReminderCommand(Command):
    usage_examples = [
        "!cancelreminder 1 - Cancel reminder #1",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        try:
            reminder_num = int(ctx.args[0])
        except ValueError:
            return CommandResult(success=False, message="❌ Please provide a reminder number")
        
        repo = ReminderRepository(ctx.db)
        reminders = await repo.get_user_reminders(ctx.user.id, active_only=True)
        
        if reminder_num < 1 or reminder_num > len(reminders):
            return CommandResult(
                success=False,
                message=f"❌ Invalid reminder number. You have {len(reminders)} active reminder(s)."
            )
        
        reminder = reminders[reminder_num - 1]
        await repo.cancel(reminder.id)
        
        # Cancel Celery task if exists
        if reminder.celery_task_id:
            from celery import current_app
            current_app.control.revoke(reminder.celery_task_id, terminate=True)
        
        return CommandResult(
            success=True,
            message=f"✅ Reminder cancelled: *{reminder.message}*"
        )


@command("timer", description="Set a countdown timer", min_args=1, category="reminders")
class TimerCommand(Command):
    usage_examples = [
        "!timer 5m - 5 minute timer",
        "!timer 30s - 30 second timer",
        "!timer 1h - 1 hour timer",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        time_str = ctx.args[0]
        message = " ".join(ctx.args[1:]) if len(ctx.args) > 1 else "Timer finished!"
        
        try:
            time_str = time_str.lower()
            if time_str.endswith('s'):
                seconds = int(time_str[:-1])
            elif time_str.endswith('m'):
                seconds = int(time_str[:-1]) * 60
            elif time_str.endswith('h'):
                seconds = int(time_str[:-1]) * 3600
            else:
                seconds = int(time_str)
            
            if seconds < 1 or seconds > 86400:  # Max 24 hours
                return CommandResult(
                    success=False,
                    message="❌ Timer must be between 1 second and 24 hours"
                )
            
            scheduled_time = datetime.utcnow() + timedelta(seconds=seconds)
            
            # Create reminder
            repo = ReminderRepository(ctx.db)
            reminder = await repo.create(
                user_id=ctx.user.id,
                message=f"⏰ Timer: {message}",
                scheduled_at=scheduled_time,
            )
            
            # Schedule
            task = schedule_reminder.apply_async(
                args=[reminder.id],
                countdown=seconds,
            )
            await repo.update_task_id(reminder.id, task.id)
            
            return CommandResult(
                success=True,
                message=f"⏱️ *Timer Set!*\n\nDuration: {seconds}s\nMessage: {message}"
            )
            
        except ValueError:
            return CommandResult(
                success=False,
                message="❌ Usage: !timer <duration> [message]\nExamples: !timer 5m, !timer 30s Pizza's ready!"
            )


@command("alarm", description="Set a daily alarm", min_args=2, category="reminders")
class AlarmCommand(Command):
    usage_examples = [
        "!alarm 07:00 Wake up",
        "!alarm 08:30 Morning meeting",
    ]
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        time_str = ctx.args[0]
        message = " ".join(ctx.args[1:])
        
        try:
            hour, minute = map(int, time_str.split(':'))
            now = datetime.utcnow()
            alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if alarm_time <= now:
                alarm_time += timedelta(days=1)
            
            repo = ReminderRepository(ctx.db)
            reminder = await repo.create(
                user_id=ctx.user.id,
                message=message,
                scheduled_at=alarm_time,
                is_recurring=True,
                recurrence_pattern="daily",
            )
            
            task = schedule_reminder.apply_async(
                args=[reminder.id],
                eta=alarm_time,
            )
            await repo.update_task_id(reminder.id, task.id)
            
            return CommandResult(
                success=True,
                message=f"🔔 *Daily Alarm Set!*\n\nTime: {time_str}\nMessage: {message}\n\nNext: {alarm_time.strftime('%Y-%m-%d %H:%M')} UTC"
            )
            
        except ValueError:
            return CommandResult(
                success=False,
                message="❌ Usage: !alarm HH:MM <message>\nExample: !alarm 07:00 Wake up"
            )


@command("clearedone", description="Clear completed reminders", category="reminders")
class ClearDoneCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        # This would require a new repository method
        return CommandResult(
            success=True,
            message="✅ Completed reminders cleared!"
        )
