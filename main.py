"""
Main FastAPI application for WhatsApp Bot.
"""
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Form, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from app.config import settings
from app.logging_config import configure_logging, get_logger, log_request
from commands.base import CommandContext, registry
from db.database import close_db, get_db, init_db
from db.models import UserTier
from db.repositories import UserRepository
from utils.rate_limiter import RateLimitResult, anti_spam, rate_limiter
from utils.redis_client import redis_client
from utils.twilio_client import twilio_client

# Configure logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("application_starting", app_name=settings.APP_NAME)
    
    # Initialize database
    await init_db()
    
    # Initialize Redis
    await redis_client.connect()
    
    # Initialize Twilio
    twilio_client.initialize()
    
    logger.info("application_started")
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")
    
    # Close connections
    await close_db()
    await redis_client.disconnect()
    
    logger.info("application_shutdown_complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="A powerful WhatsApp bot with 90+ commands",
    version="2.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests."""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = (time.time() - start_time) * 1000
    
    log_request(
        logger,
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration,
        extra={
            "client_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        },
    )
    
    return response


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": "2.0.0",
        "status": "online",
        "commands": len(registry.get_all_commands()),
        "categories": len(registry.get_all_categories()),
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "database": "unknown",
        "redis": "unknown",
    }
    
    # Check database
    try:
        async with get_db() as db:
            await db.execute("SELECT 1")
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check Redis
    try:
        if redis_client._client:
            await redis_client._client.ping()
            health_status["redis"] = "connected"
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    
    return JSONResponse(
        content=health_status,
        status_code=status_code,
    )


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(default=None),
    NumMedia: int = Form(default=0),
):
    """Handle incoming WhatsApp messages from Twilio."""
    start_time = time.time()
    
    logger.info(
        "webhook_received",
        from_number=From,
        message_sid=MessageSid,
        body_preview=Body[:50] if Body else None,
    )
    
    # Validate webhook in production
    if settings.is_production:
        signature = request.headers.get("X-Twilio-Signature", "")
        url = str(request.url)
        params = await request.form()
        
        if not twilio_client.validate_webhook(signature, url, dict(params)):
            logger.warning("invalid_webhook_signature")
            raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Get database session
    async with get_db() as db:
        try:
            # Check rate limit
            rate_result = await rate_limiter.check_rate_limit(From, db)
            if not rate_result.allowed:
                logger.warning("rate_limit_blocked", phone=From)
                return PlainTextResponse(
                    twilio_client.create_response(
                        f"⏳ Rate limit exceeded. Please try again in {rate_result.reset_after} seconds."
                    )
                )
            
            # Check for spam
            is_spam, spam_score, spam_reasons = anti_spam.analyze_message(Body)
            if is_spam:
                logger.warning(
                    "spam_blocked",
                    phone=From,
                    score=spam_score,
                    reasons=spam_reasons,
                )
                return PlainTextResponse(
                    twilio_client.create_response(
                        "🚫 Your message was flagged as spam. Please try again with different content."
                    )
                )
            
            # Get or create user
            user_repo = UserRepository(db)
            user = await user_repo.get_or_create(From)
            
            # Check if user is blocked
            if user.is_blocked or not user.is_active:
                logger.warning("blocked_user_attempt", phone=From, user_id=user.id)
                return PlainTextResponse(twilio_client.create_empty_response())
            
            # Check maintenance mode
            from db.repositories import SystemSettingRepository
            setting_repo = SystemSettingRepository(db)
            maintenance = await setting_repo.get("maintenance_mode", "false")
            
            if maintenance == "true" and user.tier != UserTier.ADMIN:
                return PlainTextResponse(
                    twilio_client.create_response(
                        "🔧 The bot is currently under maintenance. Please try again later."
                    )
                )
            
            # Check user tier limits
            can_execute = await user_repo.can_execute_command(user)
            if not can_execute:
                daily_limit = await user_repo.get_daily_limit(user.tier)
                return PlainTextResponse(
                    twilio_client.create_response(
                        f"📊 You've reached your daily limit of {daily_limit} commands.\n\n"
                        f"Upgrade your tier for more commands!"
                    )
                )
            
            # Parse command
            message = Body.strip()
            
            if not message.startswith("!"):
                # Not a command - provide helpful response
                return PlainTextResponse(
                    twilio_client.create_response(
                        "👋 Hello! I'm a command-based bot.\n\n"
                        "Start commands with ! like:\n"
                        "• !help - See all commands\n"
                        "• !weather London - Check weather\n"
                        "• !joke - Get a joke"
                    )
                )
            
            # Parse command and arguments
            parts = message[1:].split()
            command_name = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            # Create command context
            ctx = CommandContext(
                user=user,
                phone_number=From,
                args=args,
                raw_message=Body,
                db=db,
            )
            
            # Execute command
            result = await registry.execute(command_name, ctx)
            
            # Log command execution
            from db.repositories import CommandLogRepository
            log_repo = CommandLogRepository(db)
            execution_time = int((time.time() - start_time) * 1000)
            
            await log_repo.log_command(
                user_id=user.id,
                command=command_name,
                args=" ".join(args) if args else None,
                response=result.message[:500] if result.message else None,
                execution_time_ms=execution_time,
                success=result.success,
                error_message=result.error_code,
            )
            
            return PlainTextResponse(
                twilio_client.create_response(result.message)
            )
            
        except Exception as e:
            logger.error("webhook_processing_error", error=str(e), exc_info=True)
            return PlainTextResponse(
                twilio_client.create_response(
                    "❌ An error occurred. Please try again later."
                )
            )


@app.get("/webhook/whatsapp")
async def whatsapp_webhook_verify(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None,
):
    """Verify webhook for WhatsApp Business API (if needed)."""
    # This is mainly for Meta's webhook verification
    # Twilio doesn't require this, but it's here for future expansion
    return PlainTextResponse(content=hub_challenge or "OK")


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "message": "The requested resource was not found"},
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: HTTPException):
    """Handle 500 errors."""
    logger.error("internal_server_error", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": "Something went wrong"},
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        reload=not settings.is_production,
    )
