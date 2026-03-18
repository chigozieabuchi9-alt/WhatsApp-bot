"""
Twilio client for WhatsApp messaging.
"""
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class TwilioClient:
    """Twilio client wrapper for WhatsApp messaging."""
    
    def __init__(self):
        self.client: Client = None
        self.from_number: str = None
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the Twilio client."""
        try:
            self.client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN,
            )
            self.from_number = f"whatsapp:{settings.TWILIO_PHONE_NUMBER}"
            self._initialized = True
            logger.info("twilio_client_initialized")
        except Exception as e:
            logger.error("twilio_init_failed", error=str(e))
            raise
    
    async def send_message(self, to: str, body: str) -> str:
        """Send a WhatsApp message."""
        if not self._initialized:
            self.initialize()
        
        try:
            # Ensure phone number has whatsapp: prefix
            if not to.startswith("whatsapp:"):
                to = f"whatsapp:{to}"
            
            # Split long messages
            max_length = 1600  # Twilio's limit
            if len(body) > max_length:
                body = body[:max_length - 3] + "..."
            
            message = self.client.messages.create(
                from_=self.from_number,
                body=body,
                to=to,
            )
            
            logger.info(
                "message_sent",
                to=to,
                message_sid=message.sid,
                length=len(body),
            )
            
            return message.sid
            
        except Exception as e:
            logger.error("message_send_failed", to=to, error=str(e))
            raise
    
    def create_response(self, message: str) -> str:
        """Create a TwiML response."""
        response = MessagingResponse()
        response.message(message)
        return str(response)
    
    def create_empty_response(self) -> str:
        """Create an empty TwiML response."""
        response = MessagingResponse()
        return str(response)
    
    def validate_webhook(self, signature: str, url: str, params: dict) -> bool:
        """Validate Twilio webhook signature."""
        from twilio.request_validator import RequestValidator
        
        validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
        return validator.validate(url, params, signature)


# Global Twilio client instance
twilio_client = TwilioClient()
