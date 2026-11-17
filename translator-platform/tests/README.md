# Test Suite Documentation

## Overview

This directory contains integration and end-to-end tests for the Translator Platform.

## Test Structure

```
tests/
├── translation/        # Translation quality tests
├── terminology/        # Terminology protection tests
├── latency/           # Performance and latency tests
└── concurrency/       # Concurrent request tests
```

## Running Tests

### Backend Tests

```bash
cd backend
pytest tests/ -v
pytest tests/terminology/ -v
pytest tests/translation/ -v
```

### Frontend Tests

```bash
cd frontend
npm test
npm run test:coverage
```

### Load Testing

```bash
cd backend
locust -f tests/concurrency/load_test.py --host=http://localhost:8000
```

## Test Categories

### Terminology Tests
- Protected term preservation
- Alias matching
- Case sensitivity
- Overlapping terminology
- Longest-match priority
- Placeholder restoration
- Punctuation preservation

### Translation Tests
- Kannada ↔ English
- Hindi ↔ English
- Malayalam ↔ English
- Tamil ↔ English
- Indic-to-Indic (where supported)

### Domain Tests
- Technology glossary
- Medical glossary
- General conversation
- Same term in different domains

### Application Tests
- Registration
- Login
- Role permissions
- Ticket creation
- Ticket approval
- Room access
- WebSocket messaging

### Performance Tests
- Concurrent requests
- Queue overflow
- Translation latency
- Cache behavior

## Test Data

Test glossaries are provided in `backend/datasets/glossary/`:
- `technology_sample.csv`
- `medical_sample.csv`
- `general_sample.csv`

## CI/CD Integration

Tests run automatically on:
- Pull requests
- Main branch pushes
- Release tags

Required checks:
- All backend tests pass
- All frontend tests pass
- Code coverage > 80%
- No security vulnerabilities