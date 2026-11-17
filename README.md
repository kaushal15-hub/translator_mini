# Translator Platform

AI-Powered Multilingual Communication Platform with Domain-Aware Translation

## Overview

A real-time communication platform enabling seamless multilingual conversations between users speaking different languages. Features domain-aware translation with terminology protection for Technology, Medical, and General domains.

## Features

- **Multilingual Support**: Kannada, English, Hindi, Malayalam, Tamil
- **Domain-Aware Translation**: Technology, Medical, General domains
- **Terminology Protection**: Aho-Corasick based protected term preservation
- **Real-time Communication**: WebSocket-based messaging
- **Role-Based Access**: User, Admin, Room Agent roles
- **Ticket Workflow**: Request → Approve → Assign → Communicate
- **Glossary Management**: CSV/JSON upload for domain terminology
- **CPU Optimized**: INT8 quantization, shared models, bounded queues

## Architecture

```
translator-platform/
├── frontend/                 # React + TypeScript + Vite
├── backend/                  # FastAPI + Python
│   ├── app/                  # Main application
│   ├── ai_engine/            # AI/ML components
│   ├── inference/            # Model inference optimization
│   ├── datasets/             # Glossary and evaluation data
│   └── tests/                # Backend tests
├── docker/                   # Docker configurations
├── tests/                    # Integration tests
├── scripts/                  # Utility scripts
├── docker-compose.yml
└── README.md
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Start all services
docker-compose up -d

# Access frontend at http://localhost:3000
# Backend API at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp ../.env.example .env
# Edit .env with database/redis credentials

# Run database migrations
alembic upgrade head

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Environment Configuration

Key environment variables (see `.env.example`):

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/translator
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Models
MODEL_CACHE_DIR=./models
INDIC_TRANS2_MODEL_PATH=./models/indictrans2
WHISPER_MODEL_PATH=./models/whisper

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Model Setup

Download IndicTrans2 models:

```bash
# Create model directory
mkdir -p backend/models

# Download IndicTrans2 distilled models (CPU optimized)
python scripts/download_models.py --models indictrans2 whisper

# Or download specific models
python scripts/download_models.py --models indictrans2
python scripts/download_models.py --models whisper --whisper-size base
```

See: https://github.com/AI4Bharat/IndicTrans2 for model details.

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Load testing
cd backend
locust -f tests/concurrency/load_test.py
```

## Project Structure Details

### Backend (`backend/app/`)

- `api/v1/` - REST API endpoints
- `authentication/` - JWT auth, password hashing
- `tickets/` - Ticket workflow management
- `rooms/` - Communication room management
- `users/` - User management
- `websocket/` - WebSocket handlers
- `database/` - DB session, base models
- `models/` - SQLAlchemy models
- `schemas/` - Pydantic schemas
- `services/` - Business logic services
- `core/` - Configuration, security, exceptions

### AI Engine (`backend/ai_engine/`)

- `translation/` - Translation service, domain handling
- `terminology/` - Glossary management, Aho-Corasick matcher
- `context/` - Conversation context management
- `validation/` - Translation quality validation
- `language_detection/` - Language identification
- `speech/` - Speech processing interfaces

### Inference (`backend/inference/`)

- `model_loader.py` - Lazy model loading, warmup
- `scheduler.py` - Bounded inference queue
- `cpu_optimizer.py` - INT8, thread config

## Domain Glossary Format

### CSV Format

```csv
original_term,alternatives,aliases,domain,source_language,target_language,case_sensitive,preserve_original,priority,active
Python,Py,Python3,technology,en,kn,true,true,10,true
Machine Learning,ML,Artificial Intelligence,technology,en,kn,true,true,10,true
```

### JSON Format

```json
[
  {
    "original_term": "Python",
    "alternatives": ["Py", "Python3"],
    "aliases": ["Python"],
    "domain": "technology",
    "source_lang": "en",
    "target_lang": "kn",
    "case_sensitive": true,
    "preserve_original": true,
    "priority": 10,
    "active": true
  }
]
```

## Supported Language Pairs

| Source \ Target | English | Kannada | Hindi | Malayalam | Tamil |
|----------------|---------|---------|-------|-----------|-------|
| English        | -       | ✓       | ✓     | ✓         | ✓     |
| Kannada        | ✓       | -       | ✓     | ✓         | ✓     |
| Hindi          | ✓       | ✓       | -     | ✓         | ✓     |
| Malayalam      | ✓       | ✓       | ✓     | -         | ✓     |
| Tamil          | ✓       | ✓       | ✓     | ✓         | -     |

## User Roles

### User
- Register and log in
- Select preferred language
- Create communication tickets
- View ticket status
- Join authorized communication rooms
- Send and receive translated messages

### Admin
- Secure admin login
- View all tickets
- Approve or reject requests
- Assign room agents
- Create and manage rooms
- Manage users and roles
- Manage domain glossaries
- Upload CSV/JSON glossary files

### Room Agent / Communicator
- View assigned rooms
- Manage room access
- Communicate with participants
- View original and translated messages

## Ticket Workflow

1. User creates a communication ticket
2. Admin reviews and approves/rejects
3. Admin assigns room agent if needed
4. Room is created and participants added
5. Users communicate via WebSocket
6. Messages translated in real-time
7. Ticket marked complete when done

Ticket statuses: Pending → Approved → Assigned → Active → Completed

## Security Features

- JWT authentication with refresh tokens
- Secure password hashing (bcrypt)
- Role-based permissions
- Room membership validation
- WebSocket authorization
- Input validation and sanitization
- SQL injection prevention via ORM
- CORS configuration
- Rate limiting
- Audit logging for admin actions

## Known Limitations

1. **Model Downloads Required**: IndicTrans2 models must be downloaded separately
2. **CPU Only**: Initial release targets CPU inference (GPU support planned)
3. **Indic-to-Indic**: Limited by model availability
4. **Speech Module**: Interface ready, implementation pending
5. **Concurrent Users**: ~10 users tested, benchmark for production

## License

MIT License - See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create feature branch
3. Run tests: `pytest` and `npm test`
4. Submit pull request

## Support

For issues and feature requests, please use the GitHub issue tracker.