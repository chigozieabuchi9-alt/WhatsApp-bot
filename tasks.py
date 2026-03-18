"""
Celery tasks for reminders and background jobs.
"""
from datetime import datetime

from sqlalchemy import select

from app.config import settings
from app.logging_config import get_logger
from db.database import AsyncSessionLocal
from db.models import Reminder, User
from reminders.celery_config import celery_app
from utils.twilio_client import twilio_client

logger = get_logger(__name__)


@celery_app.task(bind=True, max_retries=3)
def schedule_reminder(self, reminder_id: int):
    """Send a reminder notification."""
    import asyncio
    asyncio.run(_send_reminder(reminder_id))


async def _send_reminder(reminder_id: int):
    """Async function to send reminder."""
    async with AsyncSessionLocal() as session:
        try:
            # Get reminder
            result = await session.execute(
                select(Reminder).where(Reminder.id == reminder_id)
            )
            reminder = result.scalar_one_or_none()
            
            if not reminder or reminder.is_completed or reminder.is_cancelled:
                logger.warning("reminder_not_found_or_completed", reminder_id=reminder_id)
                return
            
            # Get user
            user_result = await session.execute(
                select(User).where(User.id == reminder.user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user or not user.is_active:
                logger.warning("user_not_found_or_inactive", user_id=reminder.user_id)
                return
            
            # Send message via Twilio
            message = f"⏰ *Reminder*\n\n{reminder.message}"
            
            await twilio_client.send_message(
                to=user.phone_number,
                body=message,
            )
            
            # Mark as completed
            reminder.is_completed = True
            reminder.completed_at = datetime.utcnow()
            await session.commit()
            
            logger.info(
                "reminder_sent",
                reminder_id=reminder_id,
                user_id=user.id,
            )
            
            # Handle recurring reminders
            if reminder.is_recurring and reminder.recurrence_pattern:
                await _schedule_recurring(session, reminder)
                
        except Exception as e:
            logger.error("reminder_send_failed", reminder_id=reminder_id, error=str(e))
            raise self.retry(exc=e, countdown=60)


async def _schedule_recurring(session, reminder: Reminder):
    """Schedule next occurrence of a recurring reminder."""
    from datetime import timedelta
    
    patterns = {
        "daily": timedelta(days=1),
        "weekly": timedelta(weeks=1),
        "monthly": timedelta(days=30),
    }
    
    if reminder.recurrence_pattern in patterns:
        new_time = reminder.scheduled_at + patterns[reminder.recurrence_pattern]
        
        # Create new reminder
        new_reminder = Reminder(
            user_id=reminder.user_id,
            message=reminder.message,
            scheduled_at=new_time,
            timezone=reminder.timezone,
            is_recurring=True,
            recurrence_pattern=reminder.recurrence_pattern,
        )
        session.add(new_reminder)
        await session.flush()
        
        # Schedule it
        schedule_reminder.apply_async(
            args=[new_reminder.id],
            eta=new_time,
        )
        
        logger.info(
            "recurring_reminder_scheduled",
            reminder_id=new_reminder.id,
            scheduled_at=new_time.isoformat(),
        )


@celery_app.task
def cleanup_expired_sessions():
    """Clean up expired Redis sessions and game states."""
    import asyncio
    asyncio.run(_cleanup_expired())


async def _cleanup_expired():
    """Async cleanup function."""
    from utils.redis_client import redis_client
    
    try:
        # Connect to Redis
        await redis_client.connect()
        
        # Clean up expired keys (Redis does this automatically, but we can force it)
        # This is mainly for any custom cleanup we might need
        
        logger.info("cleanup_completed")
        
    except Exception as e:
        logger.error("cleanup_failed", error=str(e))
    finally:
        await redis_client.disconnect()


@celery_app.task
def reset_daily_limits():
    """Reset daily command limits for all users."""
    import asyncio
    asyncio.run(_reset_limits())


async def _reset_limits():
    """Async reset function."""
    async with AsyncSessionLocal() as session:
        try:
            from sqlalchemy import update
            from db.models import User
            
            # Reset daily counts
            await session.execute(
                update(User).values(
                    daily_command_count=0,
                    daily_reset_at=datetime.utcnow(),
                )
            )
            await session.commit()
            
            logger.info("daily_limits_reset")
            
        except Exception as e:
            logger.error("reset_limits_failed", error=str(e))


@celery_app.task
def send_broadcast_message(phone_numbers: list, message: str):
    """Send broadcast message to multiple users."""
    import asyncio
    asyncio.run(_send_broadcast(phone_numbers, message))


async def _send_broadcast(phone_numbers: list, message: str):
    """Async broadcast function."""
    for phone in phone_numbers:
        try:
            await twilio_client.send_message(
                to=phone,
                body=message,
            )
            logger.info("broadcast_sent", phone=phone)
        except Exception as e:
            logger.error("broadcast_failed", phone=phone, error=str(e))
