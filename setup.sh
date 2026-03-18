#!/bin/bash

# WhatsApp Bot Setup Script
# This script helps you set up the WhatsApp bot quickly

set -e

echo "🤖 WhatsApp Bot Setup"
echo "====================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose are installed${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  Please edit .env with your credentials before continuing!${NC}"
    echo "   Required variables:"
    echo "   - TWILIO_ACCOUNT_SID"
    echo "   - TWILIO_AUTH_TOKEN"
    echo "   - TWILIO_PHONE_NUMBER"
    echo "   - TWILIO_WEBHOOK_URL"
    echo "   - SECRET_KEY"
    echo ""
    read -p "Press Enter to open .env in nano (or Ctrl+C to exit and edit manually)..."
    nano .env
fi

echo -e "${GREEN}✅ .env file exists${NC}"
echo ""

# Validate required variables
echo "🔍 Validating environment variables..."

required_vars=(
    "TWILIO_ACCOUNT_SID"
    "TWILIO_AUTH_TOKEN"
    "TWILIO_PHONE_NUMBER"
    "SECRET_KEY"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" .env || grep -q "^${var}=your-" .env; then
        missing_vars+=($var)
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo -e "${RED}❌ Missing or default values for required variables:${NC}"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please edit .env and set these variables."
    exit 1
fi

echo -e "${GREEN}✅ All required variables are set${NC}"
echo ""

# Build and start services
echo "🏗️  Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo ""
echo "🔍 Checking service status..."

if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Services are running${NC}"
else
    echo -e "${RED}❌ Some services failed to start${NC}"
    docker-compose ps
    exit 1
fi

# Run migrations
echo ""
echo "🗄️  Running database migrations..."
docker-compose exec -T app alembic upgrade head || {
    echo -e "${YELLOW}⚠️  Migration failed, retrying in 10 seconds...${NC}"
    sleep 10
    docker-compose exec -T app alembic upgrade head
}

echo -e "${GREEN}✅ Database migrations completed${NC}"
echo ""

# Health check
echo "🏥 Performing health check..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ Bot is healthy and responding${NC}"
else
    echo -e "${YELLOW}⚠️  Health check failed. The bot may still be starting up.${NC}"
fi

echo ""
echo "🎉 Setup complete!"
echo "=================="
echo ""
echo "Your bot is now running at:"
echo "  - API: http://localhost:8000"
echo "  - Health: http://localhost:8000/health"
echo "  - Flower (Celery): http://localhost:5555"
echo ""
echo "Next steps:"
echo "  1. Configure Twilio webhook (see TWILIO_SETUP.md)"
echo "  2. Send '!help' to your bot to test"
echo "  3. View logs: make logs"
echo ""
echo "Useful commands:"
echo "  make logs       - View all logs"
echo "  make logs-app   - View app logs only"
echo "  make shell      - Open app shell"
echo "  make down       - Stop all services"
echo ""
echo -e "${GREEN}Happy botting! 🤖${NC}"
