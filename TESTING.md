# Testing Guide

This document explains how to run tests for the Graph Data Modeling System.

## Prerequisites

- Python 3.11+ installed
- Node.js 18+ installed
- Backend dependencies installed (`pip install -r requirements.txt`)
- Frontend dependencies installed (`npm install`)

---

## Backend Testing (Python/pytest)

### Running All Tests

```bash
cd backend

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=html --cov-report=term-missing
```

### Running Specific Test Categories

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run specific test file
pytest tests/test_graph_service.py

# Run specific test function
pytest tests/test_graph_service.py::TestGraphService::test_get_overview
```

### Test Coverage

After running tests with coverage, view the HTML report:

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# Open in browser (macOS)
open htmlcov/index.html

# Open in browser (Linux)
xdg-open htmlcov/index.html

# Open in browser (Windows)
start htmlcov/index.html
```

**Target Coverage:** >80%

### Test Files

```
backend/tests/
├── conftest.py                    # Fixtures and test configuration
├── test_graph_service.py          # Unit tests for GraphService (25 tests)
├── test_guardrail_service.py      # Unit tests for GuardrailService (8 tests)
├── test_graph_api.py              # Integration tests for graph API (15 tests)
└── __init__.py
```

### Writing New Tests

Example unit test:

```python
import pytest
from app.services.graph_service import GraphService

@pytest.mark.unit
class TestMyFeature:
    def test_something(self, sample_graph):
        """Test description."""
        service = GraphService(sample_graph)
        result = service.some_method()
        assert result is not None
```

Example integration test:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.mark.integration
def test_api_endpoint(client):
    """Test API endpoint."""
    response = client.get("/api/some/endpoint")
    assert response.status_code == 200
```

---

## Frontend Testing (Vitest + React Testing Library)

### Running All Tests

```bash
cd frontend

# Run all tests
npm test

# Run in watch mode (auto-rerun on changes)
npm test -- --watch

# Run with UI
npm test -- --ui

# Run with coverage
npm test -- --coverage
```

### Running Specific Tests

```bash
# Run specific test file
npm test -- FilterPanel.test.tsx

# Run tests matching pattern
npm test -- Entity

# Run in specific mode
npm test -- --run  # Run once (no watch)
```

### Test Coverage

```bash
# Generate coverage report
npm test -- --coverage

# Coverage report will be in:
# - coverage/index.html (HTML report)
# - Terminal output (summary)
```

**Target Coverage:** >70%

### Test Files

```
frontend/src/tests/
├── setup.ts                 # Test setup and global mocks
├── FilterPanel.test.tsx     # FilterPanel component tests (7 tests)
└── EntityChip.test.tsx      # EntityChip component tests (6 tests)
```

### Writing New Tests

Example component test:

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import MyComponent from '../components/MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent prop="value" />)
    expect(screen.getByText('value')).toBeInTheDocument()
  })

  it('handles clicks', () => {
    const mockClick = vi.fn()
    render(<MyComponent onClick={mockClick} />)

    fireEvent.click(screen.getByRole('button'))
    expect(mockClick).toHaveBeenCalled()
  })
})
```

---

## Continuous Integration

### GitHub Actions (Example)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: cd backend && pip install -r requirements.txt
      - run: cd backend && pytest --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm install
      - run: cd frontend && npm test -- --coverage
```

---

## Test Database

Backend tests use an in-memory SQLite database for speed and isolation.

### Configuration

Test database is configured in `pytest.ini`:

```ini
[pytest]
env =
    DATABASE_URL=sqlite:///./test.db
```

### Fixtures

Common test data is provided via fixtures in `conftest.py`:

- `test_db` - Test database session
- `sample_graph` - Pre-populated graph with test data
- `sample_customer_data` - Customer test data
- `sample_product_data` - Product test data
- `mock_llm_response` - Mocked LLM responses

---

## Mocking External Services

### Mocking LLM API Calls

```python
from unittest.mock import patch, Mock

@patch('app.services.guardrail_service.LLMService')
def test_with_mocked_llm(mock_llm_class):
    mock_llm = Mock()
    mock_llm.generate_structured.return_value = {"is_valid": True}
    mock_llm_class.return_value = mock_llm

    # Your test code here
```

### Mocking Database Queries

Use the `test_db` fixture which provides an isolated in-memory database.

---

## Performance Testing

### Backend Query Performance

```bash
# Use pytest-benchmark (if installed)
pytest tests/test_performance.py --benchmark-only

# Or time specific operations
python -m timeit -s "from app.services.graph_service import GraphService" "service.get_nodes()"
```

### Frontend Render Performance

```typescript
import { render } from '@testing-library/react'

it('renders quickly', () => {
  const start = performance.now()
  render(<LargeComponent />)
  const end = performance.now()

  expect(end - start).toBeLessThan(100) // <100ms
})
```

---

## Common Issues

### Issue: Import errors in tests

**Solution:** Make sure you're running from the correct directory:

```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test
```

### Issue: Database errors in integration tests

**Solution:** Clear test database:

```bash
rm backend/test.db
pytest
```

### Issue: Frontend tests fail with "Cannot find module"

**Solution:** Install dependencies:

```bash
cd frontend
npm install
npm test
```

### Issue: Mock not working

**Solution:** Check import paths in patches:

```python
# ❌ Wrong
@patch('guardrail_service.LLMService')

# ✅ Correct
@patch('app.services.guardrail_service.LLMService')
```

---

## Test Quality Checklist

- [ ] Tests are isolated (no dependencies between tests)
- [ ] Tests use descriptive names
- [ ] Tests have clear assertions
- [ ] Tests cover happy path and edge cases
- [ ] External dependencies are mocked
- [ ] Tests run quickly (<5 seconds total)
- [ ] Coverage is >80% for backend, >70% for frontend
- [ ] No warnings or deprecation errors
- [ ] Tests can run in any order

---

## Running Tests Before Commit

### Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash

echo "Running backend tests..."
cd backend && pytest || exit 1

echo "Running frontend tests..."
cd ../frontend && npm test -- --run || exit 1

echo "All tests passed!"
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

---

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [Vitest documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

## Summary

**Backend:**
- 48 unit + integration tests
- pytest with coverage
- In-memory SQLite for speed
- Mocked external dependencies

**Frontend:**
- 13 component tests
- Vitest + React Testing Library
- jsdom environment
- Testing user interactions

**Running Everything:**
```bash
# Backend
cd backend && pytest --cov=app

# Frontend
cd frontend && npm test -- --coverage
```

Target: >80% code coverage overall
