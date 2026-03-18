"""
Rate limiting and anti-spam protection.
"""
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.logging_config import get_logger
from db.repositories import BlockedNumberRepository, RateLimitRepository
from utils.redis_client import redis_client

logger = get_logger(__name__)

# Spam patterns
SPAM_PATTERNS = [
    r"\b(buy now|click here|limited time|act now)\b",
    r"(https?://\S{100,})",  # Very long URLs
    r"(\S+)\1{10,}",  # Repeated characters
    r"[A-Z]{20,}",  # All caps
    r"(.)\1{15,}",  # Single character repeated
    r"\b(viagra|cialis|lottery|winner|prize)\b",
    r"\$\d{3,}\s*(USD|usd)?\s*(free|win|won)",
    r"(send|transfer|wire)\s+money",
    r"\b(bitcoin|crypto|investment)\s+(double|triple|guaranteed)\b",
]

SUSPICIOUS_PATTERNS = [
    r"!{5,}",  # Multiple exclamation marks
    r"\?{5,}",  # Multiple question marks
    r"[\$€£¥]{3,}",  # Multiple currency symbols
]


class RateLimitResult:
    """Result of rate limit check."""
    
    def __init__(
        self,
        allowed: bool,
        remaining: int = 0,
        reset_after: int = 0,
        block_reason: Optional[str] = None,
    ):
        self.allowed = allowed
        self.remaining = remaining
        self.reset_after = reset_after
        self.block_reason = block_reason


class RateLimiter:
    """Rate limiter with Redis and database fallback."""
    
    def __init__(self):
        self.minute_limit = settings.RATE_LIMIT_REQUESTS_PER_MINUTE
        self.hour_limit = settings.RATE_LIMIT_REQUESTS_PER_HOUR
        self.block_duration = settings.RATE_LIMIT_BLOCK_DURATION
    
    async def check_rate_limit(
        self,
        phone_number: str,
        db: AsyncSession,
    ) -> RateLimitResult:
        """Check if request is within rate limits."""
        
        # Check permanent block first
        blocked_repo = BlockedNumberRepository(db)
        if await blocked_repo.is_blocked(phone_number):
            return RateLimitResult(
                allowed=False,
                block_reason="permanently_blocked",
            )
        
        # Check Redis rate limit (minute window)
        minute_key = f"ratelimit:{phone_number}:minute"
        allowed, remaining, reset_after = await redis_client.check_rate_limit(
            minute_key,
            self.minute_limit,
            60,
        )
        
        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                phone_number=phone_number,
                window="minute",
            )
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_after=reset_after,
                block_reason="rate_limit_minute",
            )
        
        # Check Redis rate limit (hour window)
        hour_key = f"ratelimit:{phone_number}:hour"
        allowed, remaining_hour, reset_after_hour = await redis_client.check_rate_limit(
            hour_key,
            self.hour_limit,
            3600,
        )
        
        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                phone_number=phone_number,
                window="hour",
            )
            # Block for longer duration
            await self._block_number(db, phone_number, "rate_limit_hour")
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_after=self.block_duration,
                block_reason="rate_limit_hour",
            )
        
        return RateLimitResult(
            allowed=True,
            remaining=min(remaining, remaining_hour),
            reset_after=0,
        )
    
    async def _block_number(
        self,
        db: AsyncSession,
        phone_number: str,
        reason: str,
    ) -> None:
        """Block a number temporarily."""
        repo = RateLimitRepository(db)
        blocked_until = datetime.utcnow() + timedelta(seconds=self.block_duration)
        await repo.block(phone_number, blocked_until, reason)
        logger.warning("number_blocked", phone_number=phone_number, reason=reason)


class AntiSpam:
    """Anti-spam detection and filtering."""
    
    def __init__(self):
        self.spam_score_threshold = 5
        self.suspicious_score_threshold = 3
        self.compiled_spam_patterns = [re.compile(p, re.IGNORECASE) for p in SPAM_PATTERNS]
        self.compiled_suspicious_patterns = [re.compile(p, re.IGNORECASE) for p in SUSPICIOUS_PATTERNS]
    
    def analyze_message(self, message: str) -> Tuple[bool, int, list]:
        """
        Analyze message for spam indicators.
        Returns: (is_spam, spam_score, reasons)
        """
        score = 0
        reasons = []
        
        # Check spam patterns
        for pattern in self.compiled_spam_patterns:
            if pattern.search(message):
                score += 2
                reasons.append(f"spam_pattern: {pattern.pattern[:30]}...")
        
        # Check suspicious patterns
        for pattern in self.compiled_suspicious_patterns:
            if pattern.search(message):
                score += 1
                reasons.append(f"suspicious_pattern: {pattern.pattern[:30]}...")
        
        # Check message length (very long messages)
        if len(message) > 2000:
            score += 1
            reasons.append("very_long_message")
        
        # Check for excessive newlines
        if message.count('\n') > 20:
            score += 1
            reasons.append("excessive_newlines")
        
        # Check for excessive URLs
        url_count = len(re.findall(r'https?://', message))
        if url_count > 5:
            score += 2
            reasons.append(f"excessive_urls: {url_count}")
        
        # Check for phone number spam
        phone_count = len(re.findall(r'\+?\d{10,}', message))
        if phone_count > 3:
            score += 2
            reasons.append(f"excessive_phone_numbers: {phone_count}")
        
        is_spam = score >= self.spam_score_threshold
        
        if is_spam:
            logger.warning(
                "spam_detected",
                score=score,
                reasons=reasons,
                message_preview=message[:100],
            )
        
        return is_spam, score, reasons
    
    def is_suspicious(self, message: str) -> Tuple[bool, int, list]:
        """Check if message is suspicious but not necessarily spam."""
        score = 0
        reasons = []
        
        for pattern in self.compiled_suspicious_patterns:
            if pattern.search(message):
                score += 1
                reasons.append(f"suspicious: {pattern.pattern[:30]}...")
        
        # Rapid command repetition check would be done at a higher level
        
        is_suspicious = score >= self.suspicious_score_threshold
        return is_suspicious, score, reasons


class CommandCooldown:
    """Command cooldown manager."""
    
    def __init__(self):
        self.default_cooldown = 1  # 1 second
        self.command_cooldowns = {
            "weather": 5,
            "news": 10,
            "joke": 3,
            "quote": 3,
            "image": 10,
            "translate": 5,
            "search": 5,
            "calculate": 2,
            "convert": 3,
            "game": 2,
            "reminder": 3,
            "stats": 5,
            "help": 1,
        }
    
    def _get_key(self, phone_number: str, command: str) -> str:
        """Get Redis key for cooldown."""
        return f"cooldown:{phone_number}:{command}"
    
    async def check_cooldown(
        self,
        phone_number: str,
        command: str,
    ) -> Tuple[bool, int]:
        """
        Check if command is on cooldown.
        Returns: (can_execute, remaining_seconds)
        """
        key = self._get_key(phone_number, command)
        
        # Check if cooldown exists
        ttl = await redis_client.ttl(key)
        
        if ttl > 0:
            return False, ttl
        
        return True, 0
    
    async def set_cooldown(
        self,
        phone_number: str,
        command: str,
        custom_seconds: Optional[int] = None,
    ) -> None:
        """Set cooldown for command."""
        key = self._get_key(phone_number, command)
        cooldown = custom_seconds or self.command_cooldowns.get(command, self.default_cooldown)
        await redis_client.set(key, "1", expire=cooldown)


# Global instances
rate_limiter = RateLimiter()
anti_spam = AntiSpam()
command_cooldown = CommandCooldown()
