# Syft LLM Router Template Generator v2

A simplified router template generation system with two distinct paths: **default** (batteries included) and **custom** (build from scratch).

## 🎯 Architecture Overview

This template generator creates production-ready router applications with intelligent dependency management and deployment automation.

### Two-Path Approach

- **Default Router**: Pre-implemented Ollama chat + Local RAG with ChromaDB
- **Custom Router**: Template with placeholder implementations for your own services

### Factory Pattern

Uses a factory pattern for dynamic service loading with graceful error handling:

```python
class RouterFactory:
    @staticmethod
    def create_chat_service() -> ChatService:
        try:
            from chat_service import ChatService as ChatServiceImpl
            return ChatServiceImpl()
        except ImportError:
            raise ImportError("Chat service implementation not found")
```

## 🚀 Quick Start

### Generate a Default Router (Batteries Included)

```bash
python generate_v2.py \
  --project-name my_default_router \
  --router-type default \
  --enable-chat \
  --enable-search
```

### Generate a Custom Router (Build from Scratch)

```bash
python generate_v2.py \
  --project-name my_custom_router \
  --router-type custom \
  --enable-chat \
  --enable-search
```

### Deploy and Test

```bash
cd my_default_router  # or my_custom_router
./setup.sh    # First time setup
./run.sh      # Start the router
python validate.py  # Test the router
```

## 📁 Directory Structure

```
router_template_v2/
├── common/                    # Shared layer
│   ├── base_services.py      # Abstract base classes
│   ├── schema.py             # Common schemas
│   └── server.py             # Factory-based server
├── templates/
│   ├── default/              # Default implementations
│   │   ├── chat_service.py   # Ollama implementation
│   │   ├── search_service.py # Local RAG implementation
│   │   └── config.py         # Default config
│   └── custom/               # Custom template
│       ├── chat_service.py   # Placeholder implementation
│       ├── search_service.py # Placeholder implementation
│       └── config.py         # Custom config template
├── generate_v2.py            # Main generator
├── test_v2_generation.py     # Test script
├── QUICK_START_V2.md         # Detailed guide
└── README.md                 # This file
```

## 🎯 What You Get

### Generated Files

Every generated router includes:

```
generated_router/
├── router.py              # Main router with factory pattern
├── server.py              # FastAPI server
├── base_services.py       # Abstract base classes
├── schema.py              # Pydantic schemas
├── config.py              # Configuration management
├── pyproject.toml         # Project toml
├── .env.example          # Environment template
├── README.md             # Project documentation
├── run.sh                # 🚀 Main deployment script
├── setup.sh              # 🔧 Initial setup script
├── validate.py           # 🧪 Validation and testing
├── chat_service.py       # Chat service implementation
└── search_service.py   # Search service implementation
```

### Default Router Features

- ✅ **Ollama Chat Service** - Ready to use with local LLMs
- ✅ **Local RAG Service** - ChromaDB + Sentence Transformers
- ✅ **Intelligent Setup** - Automatically installs dependencies
- ✅ **Production Ready** - Includes validation and monitoring

### Custom Router Features

- 🔧 **Placeholder Services** - Implement your own logic
- 🔧 **Template Structure** - Clear TODO comments and examples
- 🔧 **Flexible Configuration** - Add your own config options
- 🔧 **Easy Extension** - Simple to add new service types

## 🔧 Usage Examples

### Default Router - Full Stack

```bash
# Generate default router with both services
python generate_v2.py \
  --project-name my_full_router \
  --router-type default \
  --enable-chat \
  --enable-search

cd my_full_router
./setup.sh    # Installs Ollama, ChromaDB, models
./run.sh      # Starts router with both services
```

### Default Router - Chat Only

```bash
# Generate default router with chat only
python generate_v2.py \
  --project-name my_chat_router \
  --router-type default \
  --enable-chat \
  --enable-search false

cd my_chat_router
./setup.sh    # Installs Ollama and models
./run.sh      # Starts router with chat service only
```

### Custom Router - Your Implementation

```bash
# Generate custom router template
python generate_v2.py \
  --project-name my_custom_router \
  --router-type custom \
  --enable-chat \
  --enable-search

cd my_custom_router
# Edit chat_service.py and search_service.py
./setup.sh
./run.sh
```

## 🧪 Testing

### Run Tests

```bash
python test_v2_generation.py
```

This will generate and test:
- Default router (Chat + RAG)
- Custom router template
- Chat-only router
- Search-only router

### Manual Testing

```bash
# Test health
curl http://localhost:8000/health

# Test chat (if enabled)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"model": "llama2", "messages": [{"role": "user", "content": "Hello!"}]}'

# Test search (if enabled)
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "options": {"limit": 5}}'
```

## 🚀 Production Deployment

### Simple Production Setup

```bash
# Background deployment
nohup ./run.sh > router.log 2>&1 &

# Check status
ps aux | grep "python server.py"

# View logs
tail -f router.log
```

### Process Management

```bash
# Start with PID tracking
./run.sh &
PID=$!
echo "Router started with PID: $PID"

# Stop router
kill $PID
```

## 🔧 Customization

### Adding New Service Types

1. **Create Service Implementation**:
```python
# templates/default/new_service.py
class NewService(NewServiceBase):
    def __init__(self):
        # Your implementation
        pass
```

2. **Update Factory**:
```python
# In generated router.py
@staticmethod
def create_new_service() -> NewServiceBase:
    try:
        from new_service import NewService as NewServiceImpl
        return NewServiceImpl()
    except ImportError:
        raise ImportError("New service implementation not found")
```

3. **Update Generator**:
```python
# In generate_v2.py
if config.enable_new_service:
    self.search_service = RouterFactory.create_new_service()
```

### Modifying Default Services

The default services are fully customizable:
- Edit `chat_service.py` for custom Ollama logic
- Edit `search_service.py` for custom RAG logic
- Add new configuration options in `config.py`

## 🎯 Benefits

### 1. **Clear User Choice**
- **Default**: Get started immediately with working services
- **Custom**: Build exactly what you need from scratch

### 2. **Factory Pattern**
- **Dynamic Loading**: Services loaded only when needed
- **Graceful Failures**: Clear error messages for missing services
- **Easy Testing**: Mock services for unit tests

### 3. **Conditional Imports**
- **No Dependencies**: Services work even if others fail to load
- **Flexible Configuration**: Enable/disable services independently
- **Clean Architecture**: Clear separation of concerns

### 4. **Easy Extension**
- **New Service Types**: Simple to add new service categories
- **Provider Variations**: Easy to add new providers for existing services
- **Configuration Options**: Flexible configuration system

## 📚 Documentation

- [Quick Start Guide](QUICK_START_V2.md) - Detailed usage instructions
- [Test Script](test_v2_generation.py) - Examples and testing

## 🎉 Conclusion

This two-path architecture is perfect for an MVP because it:

- ✅ **Reduces complexity** while maintaining flexibility
- ✅ **Provides clear user choice** between quick start and full control
- ✅ **Uses factory pattern** for clean, maintainable code
- ✅ **Handles conditional imports** gracefully
- ✅ **Scales easily** as requirements grow

Perfect for building a dashboard that lets users choose between "quick start" and "full control"! 🚀 