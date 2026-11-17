<#
.SYNOPSIS
    Translator Platform - Development Startup Script for Windows PowerShell

.DESCRIPTION
    Sets up and starts all services for local development on Windows.
#>

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Green
Write-Host "Translator Platform - Development Setup" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Check prerequisites
function Check-Command {
    param([string]$Command, [string]$Name)
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        Write-Host "Error: $Name ($Command) is not installed" -ForegroundColor Red
        Write-Host "Please install $Name and try again" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Checking prerequisites..." -ForegroundColor Yellow
Check-Command "python" "Python"
Check-Command "node" "Node.js"
Check-Command "npm" "npm"
Check-Command "docker" "Docker"
Check-Command "docker-compose" "Docker Compose"

# Check Python version
$pythonVersion = python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))"
$requiredVersion = "3.11"
if ([version]$pythonVersion -lt [version]$requiredVersion) {
    Write-Host "Warning: Python $pythonVersion detected, $requiredVersion+ recommended" -ForegroundColor Yellow
}

# Create .env if not exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env - please edit with your configuration" -ForegroundColor Green
}

# Start database and Redis
Write-Host "Starting PostgreSQL and Redis..." -ForegroundColor Green
docker-compose up -d postgres redis

# Wait for services
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Backend setup
Write-Host "Setting up backend..." -ForegroundColor Green
Set-Location backend

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate venv and install dependencies
& venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# Run migrations
Write-Host "Running database migrations..." -ForegroundColor Yellow
alembic upgrade head

# Create admin user if not exists
Write-Host "Initializing admin user..." -ForegroundColor Yellow
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

Set-Location ..

# Frontend setup
Write-Host "Setting up frontend..." -ForegroundColor Green
Set-Location frontend

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
}

Set-Location ..

# Download models (optional)
Write-Host "Models need to be downloaded separately" -ForegroundColor Yellow
Write-Host "Run: python scripts/download_models.py" -ForegroundColor Yellow

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start development servers:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Terminal 1 - Backend:" -ForegroundColor Yellow
Write-Host "  cd backend; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload" -ForegroundColor White
Write-Host ""
Write-Host "Terminal 2 - Frontend:" -ForegroundColor Yellow
Write-Host "  cd frontend; npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "Access:" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Default admin login:" -ForegroundColor Cyan
Write-Host "  Email: admin@translator.local" -ForegroundColor White
Write-Host "  Password: change-me-immediately" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT: Change the admin password after first login!" -ForegroundColor Red