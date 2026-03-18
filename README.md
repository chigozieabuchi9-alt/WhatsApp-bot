# WhatsApp Bot 🤖

A powerful, production-ready WhatsApp bot built with Python, FastAPI, Twilio, PostgreSQL, and Redis. Features 90+ commands across 18 categories, user tier system, rate limiting, games, reminders, and more!

## Features ✨

- **90+ Commands** across 18 categories
- **User Tiers**: Guest → User → Premium → Admin
- **Rate Limiting** & Anti-spam protection
- **Wordle Game** with state management
- **Reminder System** with scheduled notifications
- **PostgreSQL Database** for persistent storage
- **Redis Caching** for sessions and game states
- **Docker Compose** for easy deployment
- **Comprehensive Logging** with structured JSON logs

## Tech Stack 🛠️

| Component | Technology |
|-----------|------------|
| Framework | FastAPI |
| Messaging | Twilio WhatsApp API |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| Task Queue | Celery + Redis |
| Monitoring | Flower (Celery) |
| Deployment | Docker + Docker Compose |

## Quick Start 🚀

### Prerequisites

- Docker & Docker Compose
- Twilio Account with WhatsApp Sandbox
- (Optional) OpenWeatherMap API Key
- (Optional) NewsAPI Key

### 1. Clone and Configure

```bash
git clone <repository-url>
cd whatsapp-bot
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_whatsapp_number
TWILIO_WEBHOOK_URL=https://your-domain.com/webhook/whatsapp
SECRET_KEY=your-super-secret-key

# Optional (for weather & news features)
OPENWEATHERMAP_API_KEY=your_key
NEWS_API_KEY=your_key
```

### 2. Start Services

```bash
docker-compose up -d
```

### 3. Run Database Migrations

```bash
docker-compose exec app alembic upgrade head
```

### 4. Configure Twilio Webhook

1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to **Messaging** → **Try it out** → **Send a WhatsApp message**
3. Under **Sandbox Settings**, set the webhook URL:
   - When a message comes in: `https://your-domain.com/webhook/whatsapp`
   - Method: HTTP POST

### 5. Test the Bot

Send a WhatsApp message to your Twilio number:
```
!help
```

## Command Categories 📚

| Category | Commands | Description |
|----------|----------|-------------|
| `general` | 18 | Basic utilities, help, time, etc. |
| `weather` | 3 | Weather forecasts, temperature conversion |
| `news` | 6 | News, search, facts, quotes |
| `games` | 6 | Wordle, Trivia, Hangman, RPS |
| `utilities` | 12 | Calculator, converters, encoding |
| `reminders` | 6 | Reminders, timers, alarms |
| `admin` | 10 | User management, stats, system |
| `fun` | 15 | Memes, roasts, games, compliments |
| `media` | 12 | Save view-once, download, stickers, GIFs |
| `security` | 10 | Passwords, encryption, bypass tools |
| `ai` | 6 | AI chat, image gen, code help, translate |
| `social` | 10 | Social media tools, hashtags, downloaders |
| `productivity` | 12 | Todo, notes, habits, workout, budget |

**Total: 130+ Commands!**

### Popular Commands

```
!help                    - Show all commands
!weather London          - Get weather
!wordle                  - Play Wordle
!reminder 30m Call mom   - Set reminder
!joke                    - Get a joke
!calc 2 + 2              - Calculate
!roll 2d6                - Roll dice
!coin                    - Flip coin
!fact                    - Random fact
!quote                   - Inspirational quote
```

### Media Commands 🖼️

```
!save viewonce           - Save view-once photos/videos
!save <url>              - Download media from URL
!save video <url>        - Download video (YT, TikTok, etc.)
!screenshot <url>        - Take website screenshot
!sticker <text>          - Create sticker
!gif <search>            - Search GIFs
!removebg                - Remove image background
!ocr                     - Extract text from image
!tts <text>              - Text to speech
```

### Security Tools 🔐

```
!passgen                 - Generate strong password
!passgen 20 easy         - Memorable password
!passcheck <password>    - Check password strength
!bypass base64 <data>    - Decode base64
!bypass url <data>       - URL decode
!bypass jwt <token>      - Decode JWT
!encrypt caesar 3 <text> - Caesar cipher
!2fa <secret>            - Generate 2FA code
!keygen api              - Generate API key
```

### AI Commands 🤖

```
!ai <question>           - Ask AI assistant
!image <prompt>          - Generate AI image
!summarize <text>        - Summarize long text
!translate es <text>     - Translate to Spanish
!code python <query>     - Get code examples
!explain <concept>       - Explain programming concept
```

### Social Media 📱

```
!social instagram <user> - Get profile link
!dl youtube <url>        - Download video
!trending twitter        - Get trending topics
!hashtag travel 10       - Get travel hashtags
!profile developer       - Generate bio
!schedule instagram      - Best posting times
```

### Productivity 📝

```
!todo add <task>         - Add todo
!todo list               - Show todos
!todo done <num>         - Complete task
!note <text>             - Save note
!pomodoro start          - Start focus session
!water 250               - Track water intake
!workout home            - Get workout
!sleep 6am               - Calculate sleep times
!budget 3000             - Plan budget
```

## User Tiers 👥

| Tier | Daily Limit | Features |
|------|-------------|----------|
| Guest | 20 | Basic commands |
| User | 100 | All commands, reminders |
| Premium | 500 | Priority, advanced features |
| Admin | Unlimited | All commands + admin tools |

### Upgrade User Tier

```
!settier +1234567890 premium
```

## API Endpoints 🔌

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Bot info & status |
| `/health` | GET | Health check |
| `/webhook/whatsapp` | POST | Twilio webhook |
| `/docs` | GET | API documentation (dev) |

## Monitoring 📊

### Flower (Celery Monitoring)

Access at: `http://localhost:5555`

Default credentials: `admin/admin` (change in docker-compose.yml)

### Health Check

```bash
curl http://localhost:8000/health
```

### Logs

```bash
# View app logs
docker-compose logs -f app

# View Celery worker logs
docker-compose logs -f celery-worker

# View all logs
docker-compose logs -f
```

## Database Migrations 🗄️

### Create Migration

```bash
docker-compose exec app alembic revision --autogenerate -m "description"
```

### Apply Migrations

```bash
docker-compose exec app alembic upgrade head
```

### Rollback

```bash
docker-compose exec app alembic downgrade -1
```

## Development 💻

### Local Setup (without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your settings

# Run database migrations
alembic upgrade head

# Start Redis (required)
redis-server

# Start Celery worker
celery -A reminders.celery_config.celery_app worker --loglevel=info

# Start the app
uvicorn app.main:app --reload
```

### Running Tests

```bash
pytest tests/ -v --cov=app --cov-report=html
```

## Production Deployment 🌐

### Using Docker Compose

```bash
# Production build
docker-compose -f docker-compose.yml up -d

# Scale workers
docker-compose up -d --scale celery-worker=4
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment | `production` |
| `DEBUG` | Debug mode | `false` |
| `SECRET_KEY` | App secret key | Required |
| `DATABASE_URL` | PostgreSQL URL | Required |
| `REDIS_URL` | Redis URL | Required |
| `TWILIO_*` | Twilio credentials | Required |
| `RATE_LIMIT_*` | Rate limiting settings | See `.env.example` |

### SSL/TLS with Nginx

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Security 🔒

- Webhook signature validation
- Rate limiting per user
- Anti-spam filtering
- SQL injection protection (SQLAlchemy)
- XSS protection
- Input sanitization

## Troubleshooting 🔧

### Common Issues

**Bot not responding**
- Check Twilio webhook URL is correct
- Verify `TWILIO_WEBHOOK_URL` matches your domain
- Check logs: `docker-compose logs app`

**Database connection errors**
- Ensure PostgreSQL is running: `docker-compose ps db`
- Check database credentials in `.env`

**Redis connection errors**
- Ensure Redis is running: `docker-compose ps redis`
- Check `REDIS_URL` in `.env`

**Celery tasks not running**
- Check Celery worker: `docker-compose logs celery-worker`
- Verify `CELERY_BROKER_URL` is correct

### Debug Mode

Enable debug logging:
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License 📄

MIT License - see LICENSE file for details

## Support 💬

- Create an issue for bugs or feature requests
- Join our community Discord (link)
- Email: support@whatsapp-bot.com

---

Built with ❤️ using Python, FastAPI, and Twilio
