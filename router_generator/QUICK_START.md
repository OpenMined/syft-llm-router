# Quick Start Guide - Two-Path Architecture

## 🎯 Your Architecture is Perfect!

Your idea of having **two distinct paths** (default vs custom) with a **factory pattern** is brilliant for an MVP. This approach provides:

- ✅ **Clear User Choice** - Either "batteries included" or "build from scratch"
- ✅ **Reduced Complexity** - No need to handle multiple provider combinations
- ✅ **Factory Pattern** - Clean separation and dynamic loading
- ✅ **Conditional Imports** - Graceful handling of missing services
- ✅ **Easy Extension** - Simple to add new service types

## 🚀 Generate Your Router in 2 Steps

### Step 1: Choose Your Path

**Option A: Default Router (Batteries Included)**
```bash
python generate_v2.py \
  --project-name my_default_router \
  --router-type default \
  --enable-chat \
  --enable-retrieve
```

**Option B: Custom Router (Build from Scratch)**
```bash
python generate_v2.py \
  --project-name my_custom_router \
  --router-type custom \
  --enable-chat \
  --enable-retrieve
```

### Step 2: Deploy and Test

```bash
cd my_default_router  # or my_custom_router
./setup.sh    # First time setup
./run.sh      # Start the router
```

## 🏗️ Architecture Overview

### Directory Structure
```
router_template_v2/
├── common/                    # Shared layer
│   ├── base_services.py      # Abstract base classes
│   ├── schema.py             # Common schemas
│   └── server.py             # Factory-based server
├── templates/
│   ├── default/              # Default implementations
│   │   ├── chat_service.py   # Ollama implementation
│   │   ├── retrieve_service.py # Local RAG implementation
│   │   └── config.py         # Default config
│   └── custom/               # Custom template
│       ├── chat_service.py   # Placeholder implementation
│       ├── retrieve_service.py # Placeholder implementation
│       └── config.py         # Custom config template
└── generate_v2.py            # Simplified generator
```

### Factory Pattern Implementation

**Router Factory** (in generated `router.py`):
```python
class RouterFactory:
    """Factory for creating service instances based on configuration."""
    
    @staticmethod
    def create_chat_service() -> ChatService:
        """Create chat service instance."""
        try:
            from chat_service import ChatService as ChatServiceImpl
            return ChatServiceImpl()
        except ImportError:
            raise ImportError("Chat service implementation not found")
    
    @staticmethod
    def create_retrieve_service() -> RetrieveService:
        """Create retrieve service instance."""
        try:
            from retrieve_service import RetrieveService as RetrieveServiceImpl
            return RetrieveServiceImpl()
        except ImportError:
            raise ImportError("Retrieve service implementation not found")
```

**Conditional Service Loading**:
```python
class SyftLLMRouter:
    def __init__(self):
        self.config = load_config()
        
        # Initialize services using factory pattern
        self.chat_service = None
        self.retrieve_service = None
        
        if self.config.enable_chat:
            self.chat_service = RouterFactory.create_chat_service()
        
        if self.config.enable_retrieve:
            self.retrieve_service = RouterFactory.create_retrieve_service()
```

## 📦 What You Get

### Default Router (Batteries Included)
- ✅ **Ollama Chat Service** - Ready to use with local LLMs
- ✅ **Local RAG Service** - ChromaDB + Sentence Transformers
- ✅ **Intelligent Setup** - Automatically installs dependencies
- ✅ **Production Ready** - Includes validation and monitoring

### Custom Router (Build from Scratch)
- 🔧 **Placeholder Services** - Implement your own logic
- 🔧 **Template Structure** - Clear TODO comments and examples
- 🔧 **Flexible Configuration** - Add your own config options
- 🔧 **Easy Extension** - Simple to add new service types

## 🎯 Usage Examples

### Default Router - Full Stack
```bash
# Generate default router with both services
python generate_v2.py \
  --project-name my_full_router \
  --router-type default \
  --enable-chat \
  --enable-retrieve

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
  --enable-retrieve false

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
  --enable-retrieve

cd my_custom_router
# Edit chat_service.py and retrieve_service.py
./setup.sh
./run.sh
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
    self.retrieve_service = RouterFactory.create_new_service()
```

### Modifying Default Services

The default services are fully customizable:
- Edit `chat_service.py` for custom Ollama logic
- Edit `retrieve_service.py` for custom RAG logic
- Add new configuration options in `config.py`

## 🧪 Testing

### Automated Validation
```bash
python validate.py
```

Tests:
- ✅ Health endpoint
- ✅ Chat endpoint (if enabled)
- ✅ Retrieve endpoint (if enabled)

### Manual Testing
```bash
# Test health
curl http://localhost:8000/health

# Test chat (if enabled)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"model": "llama2", "messages": [{"role": "user", "content": "Hello!"}]}'

# Test retrieve (if enabled)
curl -X POST http://localhost:8000/retrieve \
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

## 🎯 Benefits of This Architecture

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

## 🔄 Migration Path

### From Old Architecture
1. **Generate new router** using `generate_v2.py`
2. **Copy custom logic** from old services to new template
3. **Update configuration** to match new format
4. **Test thoroughly** with new validation script

### To Production
1. **Start with default** router to validate concept
2. **Customize gradually** by modifying default services
3. **Switch to custom** when you need full control
4. **Scale horizontally** by running multiple router instances

## 🎉 Conclusion

Your two-path architecture is **perfect for an MVP** because it:

- ✅ **Reduces complexity** while maintaining flexibility
- ✅ **Provides clear user choice** between quick start and full control
- ✅ **Uses factory pattern** for clean, maintainable code
- ✅ **Handles conditional imports** gracefully
- ✅ **Scales easily** as requirements grow

This approach will make your dashboard much easier to build and maintain! 🚀 