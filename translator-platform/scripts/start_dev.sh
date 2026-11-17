#!/bin/bash
# Development Startup Script
# Starts all services for local development

set -e

echo "========================================"
echo "Translator Platform - Development Setup"
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}Error: $1 is not installed${NC}"
        echo "Please install $1 and try again"
        exit 1
    fi
}

echo "Checking prerequisites..."
check_command python3
check_command node
check_command npm
check_command docker
check_command docker-compose

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${YELLOW}Warning: Python $PYTHON_VERSION detected, $REQUIRED_VERSION+ recommended${NC}"
fi

# Create .env if not exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}Created .env - please edit with your configuration${NC}"
fi

# Start database and Redis
echo -e "${GREEN}Starting PostgreSQL and Redis...${NC}"
docker-compose up -d postgres redis

# Wait for services
echo "Waiting for services to be ready..."
sleep 5

# Backend setup
echo -e "${GREEN}Setting up backend...${NC}"
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate venv and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Create admin user if not exists
echo "Initializing admin user..."
python -c "
import asyncio
from app.core.database import init_db
from app.authentication.service import AuthService
from app.models.user import User, Role, UserRole, UserStatus
from sqlalchemy import select

async def init():
    await init_db()
    from app.core.database import get_db_context
    async with get_db_context() as db:
        # Check if admin exists
        stmt = select(User).where(User.email == 'admin@translator.local')
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            # Create admin role if not exists
            stmt = select(Role).where(Role.name == UserRole.ADMIN)
            result = await db.execute(stmt)
            admin_role = result.scalar_one_or_none()
            if not admin_role:
                admin_role = Role(name=UserRole.ADMIN, display_name='Administrator', is_system=True)
                db.add(admin_role)
                await db.flush()

            # Create admin user
            from app.core.security import get_password_hash
            admin = User(
                email='admin@translator.local',
                hashed_password=get_password_hash('change-me-immediately'),
                full_name='System Administrator',
                is_superuser=True,
            )
            admin.roles.append(admin_role)
            db.add(admin)
            await db.flush()
            print('Admin user created')
        else:
            print('Admin user already exists')

asyncio.run(init())
"

cd ..

# Frontend setup
echo -e "${GREEN}Setting up frontend...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

cd ..

# Download models (optional)
echo -e "${YELLOW}Models need to be downloaded separately${NC}"
echo "Run: python scripts/download_models.py"

echo ""
echo "========================================"
echo -e "${GREEN}Setup complete!${NC}"
echo "========================================"
echo ""
echo "To start development servers:"
echo ""
echo "Terminal 1 - Backend:"
echo "  cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo ""
echo "Terminal 2 - Frontend:"
echo "  cd frontend && npm run dev"
echo ""
echo "Access:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Default admin login:"
echo "  Email: admin@translator.local"
echo "  Password: change-me-immediately"
echo ""
echo "IMPORTANT: Change the admin password after first login!"