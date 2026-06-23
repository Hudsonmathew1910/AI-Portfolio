# Portfolio AI Bot - Architecture & Code Structure

This document describes the refactored, production-ready architecture of the Portfolio AI Bot codebase.

## Project Overview

The Portfolio AI Bot is a Django-based chatbot application that helps answer questions about Hudson's professional portfolio using AI-powered responses from the OpenRouter API.

## Architecture Philosophy

The refactored codebase follows these key principles:

1. **Separation of Concerns**: Business logic is decoupled from views
2. **Modularity**: Reusable components with single responsibilities
3. **Type Safety**: Full type hints for better IDE support and error detection
4. **Production-Ready**: Security, logging, error handling, and performance optimizations
5. **Maintainability**: Clear documentation, logging, and consistent code style
6. **Scalability**: Service layer pattern enables easy feature expansion

## Directory Structure

```
portfolio_ai/
├── manage.py                          # Django management CLI
├── requirements.txt                   # Python dependencies
├── Procfile                           # Heroku/Platform deployment
├── README.md                          # Project documentation
├── ARCHITECTURE.md                    # This file
├── DEPLOY.md                          # Deployment guide
├── data.json                          # Portfolio data source
├── db.sqlite3                         # SQLite database
├── .env                               # Environment variables (not in git)
│
├── portfolio_ai/                      # Django project settings
│   ├── __init__.py
│   ├── settings.py                    # Production-ready configuration
│   ├── urls.py                        # Project URL routing
│   ├── wsgi.py                        # WSGI application
│   └── asgi.py                        # ASGI application
│
├── chat/                              # Main application
│   ├── __init__.py
│   ├── models.py                      # Django ORM models
│   ├── views.py                       # HTTP request handlers
│   ├── urls.py                        # URL routing
│   ├── admin.py                       # Django admin configuration
│   │
│   ├── services.py                    # 🎯 Core business logic
│   ├── prompts.py                     # 🎯 AI system prompts
│   ├── constants.py                   # 🎯 Application constants
│   ├── types.py                       # 🎯 Type definitions
│   ├── utils.py                       # 🎯 Utility functions
│   │
│   ├── migrations/                    # Database migrations
│   └── tests.py                       # Test suite
│
├── templates/
│   └── chat.html                      # Frontend UI
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── [other static assets]
│
└── logs/                              # Application logs (auto-created)
    ├── app.log                        # General application logs
    └── error.log                      # Error-level logs
```

## Key Components

### 1. Views (`chat/views.py`)

**Responsibility**: HTTP request/response handling

```python
home()           # Renders chat UI
chat_api()       # Processes chat requests
_parse_request_body()  # Request validation
_get_chat_manager()    # Service initialization
```

**Key Features**:
- Type hints on all function signatures
- Comprehensive error handling
- Proper logging at each step
- Lazy service initialization (singleton pattern)
- Decorator-based HTTP method restrictions

### 2. Services (`chat/services.py`)

**Responsibility**: Core business logic and external service integration

#### `PortfolioService`
- Loads portfolio data from `data.json`
- Generates compact summaries for AI context
- Fresh data loading on each call (no caching)

#### `AIService`
- Handles OpenRouter API communication
- Message formatting and validation
- Response parsing and error recovery
- Request retry logic

#### `ChatManager`
- Orchestrates services together
- Ensures all components work seamlessly
- Single entry point for chat processing

### 3. Prompts (`chat/prompts.py`)

**Responsibility**: AI system prompt generation

```python
get_system_prompt(portfolio_summary: str) -> str
```

A sophisticated, context-aware system prompt that:
- Defines assistant role and boundaries
- Provides portfolio context
- Sets interaction rules
- Guides response format and style
- Includes examples for edge cases

### 4. Constants (`chat/constants.py`)

**Responsibility**: Centralized configuration constants

- API endpoints and models
- Request timeouts and token limits
- Error messages
- HTTP status codes

**Benefits**:
- Single source of truth for config values
- Easy updates across the codebase
- Type safety with `Final` annotations

### 5. Types (`chat/types.py`)

**Responsibility**: Type definitions and schemas

```python
ChatMessage        # Message structure
PortfolioData      # Portfolio JSON structure
ChatRequest        # API request payload
ChatResponse       # API response payload
OpenRouterMessage  # Third-party API format
```

**Benefits**:
- IDE autocomplete and type checking
- Self-documenting code
- Runtime validation with TypedDict

### 6. Utilities (`chat/utils.py`)

**Responsibility**: Reusable helper functions

```python
sanitize_history()           # Message validation & truncation
build_portfolio_summary()    # Data formatting
escape_html()                # XSS prevention
validate_chat_message()      # Input validation
```

### 7. Models (`chat/models.py`)

**Responsibility**: Django ORM models for persistence

```python
ChatSession        # Conversation sessions
ChatMessage        # Individual messages
PortfolioDataSnapshot  # Historical data tracking
```

**Future Use Cases**:
- Session recovery
- Conversation analytics
- User engagement tracking
- Data versioning

### 8. Settings (`portfolio_ai/settings.py`)

**Responsibility**: Production-ready Django configuration

**Features**:
- Environment-based configuration
- Security headers and SSL settings
- Structured logging with rotation
- Cache configuration
- Database optimization

## Data Flow

### Chat Request Processing

```
1. User sends message
   ↓
2. HTTP POST to `/api/chat/`
   ↓
3. views.chat_api() receives request
   ↓
4. _parse_request_body() validates JSON
   ↓
5. validate_chat_message() checks content
   ↓
6. _get_chat_manager() initializes services
   ↓
7. ChatManager.process_chat() orchestrates:
   a. PortfolioService.get_summary() → context
   b. sanitize_history() → clean message history
   c. AIService.get_response() → AI interaction
   d. Response parsing and formatting
   ↓
8. JSON response returned to client
   ↓
9. Frontend displays reply
```

### AI Service Interaction

```
1. AIService.get_response() called
   ↓
2. Build request payload:
   - System prompt (with portfolio context)
   - Message history
   - Current user message
   ↓
3. OpenRouter HTTP POST request
   ↓
4. Parse JSON response
   ↓
5. Extract message content
   ↓
6. Return ChatResponse (success/error)
```

## Security Considerations

### Input Validation
- Message length limits
- HTML escaping
- JSON schema validation
- History sanitization

### Output Safety
- XSS prevention with HTML escaping
- Token limiting to prevent data leaks
- Message truncation for size control

### API Security
- Environment variable for API key storage
- HTTPS enforcement in production
- CSRF protection
- Security headers (HSTS, X-Frame-Options, etc.)

### Database Security
- SQLite with proper permissions
- Password hashing for any user auth
- Connection pooling with timeouts

## Error Handling

**Strategy**: Graceful degradation with detailed logging

```
API Error          → Log error, return 502 with message
Timeout            → Log timeout, return 504 with message
Invalid JSON       → Log parsing error, return 400 with message
Missing Data       → Log missing file, return 503 with message
Unexpected Error   → Log exception, return 500 with generic message
```

## Logging

**Configuration**: Structured logging with rotation

```
Handlers:
- Console: Real-time development feedback
- File: Persistent application logs (10MB, 5 backups)
- Error File: Dedicated error tracking

Loggers:
- django: Framework-level events
- chat: Application-specific events
```

**Levels**:
- DEBUG: Detailed development information
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error-level issues
- CRITICAL: Critical system failures

## Performance Optimizations

1. **Service Singleton**: Services initialized once per app
2. **Connection Pooling**: Database connections reused
3. **Static File Compression**: WhiteNoise with gzip
4. **Request Timeouts**: Prevent hanging connections
5. **Message Truncation**: Limit token usage
6. **History Capping**: Maximum 12 messages per session

## Testing Strategy

### Unit Tests (to be implemented)
- Service methods with mocked dependencies
- Utility function edge cases
- Type validation

### Integration Tests (to be implemented)
- End-to-end API requests
- Database interactions
- External API mocking

### Manual Testing
- Portal UI functionality
- Edge case messages
- Error scenarios

## Deployment Checklist

- [ ] Set `DJANGO_SECRET_KEY` in environment
- [ ] Set `DJANGO_DEBUG=False`
- [ ] Set `ALLOWED_HOSTS` properly
- [ ] Set `CSRF_TRUSTED_ORIGINS` for HTTPS
- [ ] Set `HUDDY_OPENROUTER_API_KEY_1`
- [ ] Run `python manage.py migrate`
- [ ] Run `python manage.py collectstatic`
- [ ] Set up HTTPS/SSL certificate
- [ ] Configure logging directory permissions
- [ ] Use production WSGI server (Gunicorn)

## Future Enhancements

1. **Database Persistence**
   - Store conversation history in ChatSession/ChatMessage
   - Enable session recovery

2. **User Analytics**
   - Track question patterns
   - Measure response satisfaction
   - Improve AI training data

3. **Caching Layer**
   - Cache portfolio summaries
   - Cache frequently asked questions
   - Redis integration for scale

4. **Multi-AI Support**
   - Support multiple AI providers
   - A/B testing different models
   - Fallback mechanisms

5. **Advanced Monitoring**
   - Error rate tracking
   - Response time analytics
   - User behavior tracking

6. **Admin Dashboard**
   - Django admin for chat history
   - Portfolio data editor
   - System health monitoring

## Code Quality Standards

### PEP 8 Compliance
- 4-space indentation
- 88-character line length (Black compatible)
- Consistent naming conventions

### Type Hints
- All function signatures typed
- Complex types use TypedDict
- Optional parameters marked clearly

### Documentation
- Module-level docstrings
- Function docstrings with Args/Returns
- Inline comments for complex logic
- Type hints serve as documentation

### Error Messages
- User-friendly error responses
- Detailed logging for debugging
- Clear error codes and status

## Migration from Old Code

### What Changed
- Business logic moved to services
- Views simplified to HTTP handlers
- Helper functions organized into modules
- Full type hints added
- Production-ready settings
- Comprehensive logging
- Better error handling

### Backward Compatibility
- API endpoints unchanged
- Request/response formats identical
- No breaking changes for frontend

### Benefits
- Easier testing (isolated services)
- Easier debugging (better logging)
- Easier scaling (modular design)
- Easier maintenance (clear structure)
- Easier extension (service layer)
