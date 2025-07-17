# Syft LLM Router 

A modern, full-stack platform for creating, managing, and publishing Language Model (LLM) routers on SyftBox. Built with a Python backend (FastAPI, SyftBox) and a sleek Preact/TypeScript frontend.

<div align="center">

![SyftBox Logo](frontend/public/syftbox-logo.svg)

**Create • Manage • Publish • Monetize**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Preact](https://img.shields.io/badge/Preact-10.19+-purple.svg)](https://preactjs.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)

</div>

---

## ✨ Features

### 🎯 **Dual User Experience**
- **Provider Mode**: Create, manage, and publish routers with monetization
- **Client Mode**: Discover and use published routers

### 🛠️ **Router Management**
- **Web-Based Creation**: Intuitive UI for creating routers through the dashboard
- **Two-Path Generation**: Choose between "batteries included" (default) or "build from scratch" (custom)
- **Service Configuration**: Enable/disable chat and search services
- **Pricing Control**: Set per-service pricing with flexible charge types
- **Real-time Status**: Monitor router health and service status

### 🎨 **Modern UI/UX**
- **Responsive Design**: Works seamlessly on desktop and mobile
- **Type Safety**: Full TypeScript support with strict typing
- **Real-time Feedback**: Loading states, error handling, and success animations
- **Accessible**: Built with accessibility best practices

### 🚀 **Production Ready**
- **Database Integration**: SQLite with SQLModel for data persistence
- **Static Asset Serving**: Optimized frontend build with Vite
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Easy Deployment**: Simple setup scripts and configuration

---

## 📁 Project Structure

```
syft-llm-router/
├── backend/                    # FastAPI + SyftBox backend
│   ├── main.py                # Main application entry point
│   ├── router/                # Router management module
│   │   ├── api.py             # FastAPI routes and endpoints
│   │   ├── manager.py         # Business logic and orchestration
│   │   ├── repository.py      # Data access layer (Repository pattern)
│   │   ├── models.py          # SQLAlchemy ORM models
│   │   ├── schemas.py         # Pydantic DTOs and validation
│   │   ├── constants.py       # Application constants
│   │   ├── exceptions.py      # Custom exception classes
│   │   └── publish.py         # Publishing logic and metadata
│   ├── generator/             # Router template generation
│   │   ├── service.py         # Router generation service
│   │   ├── common/            # Shared generation utilities
│   │   └── templates/         # Router templates (default/custom)
│   ├── shared/                # Shared utilities and configuration
│   │   └── database.py        # Database configuration and session management
│   ├── static/                # Served frontend assets (generated)
│   └── build_frontend.sh      # Frontend build script
├── frontend/                  # Preact + TypeScript frontend
│   ├── src/                   # Source code
│   ├── public/                # Static assets
│   └── package.json           # Frontend dependencies
├── data/                      # SQLite database
├── run.sh                     # Full-stack startup script
└── README.md                  # This file
```

### **Key Components**

- **`backend/router/`**: Core router management with Repository pattern and DTOs
- **`backend/generator/`**: Router template generation and customization
- **`backend/shared/`**: Shared utilities and database configuration
- **`frontend/`**: Preact application with TypeScript and TailwindCSS
- **`data/`**: SQLite database storage
- **`run.sh`**: One-command startup script

### **Backend Architecture**

The backend follows modern architectural patterns:

- **Repository Pattern**: Data access layer in `router/repository.py` with proper separation of concerns
- **DTO Pattern**: Pydantic models in `router/schemas.py` for API contracts and validation
- **Manager Layer**: Business logic orchestration in `router/manager.py`
- **API Layer**: FastAPI routes in `router/api.py` with RESTful design
- **Shared Database**: Centralized database configuration in `shared/database.py`
- **Eager Loading**: Optimized database queries with `selectinload` to prevent N+1 problems

---

## 🚀 Quick Start

### Prerequisites

- [Python 3.12+](https://www.python.org/)
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- [Bun](https://bun.sh/) (JavaScript runtime)

### Single Command Setup

```bash
# Clone the repository
git clone <repository-url>
cd syft-llm-router

# One command to start everything
./run.sh
```

That's it! 🎉 The `run.sh` script handles everything:

- ✅ **Environment Setup**: Creates Python virtual environment
- ✅ **Dependencies**: Installs all Python and JavaScript packages
- ✅ **Frontend Build**: Compiles the React application
- ✅ **Database**: Initializes SQLite database with tables
- ✅ **Server Start**: Launches the backend on `http://localhost:8080`

### Access Your Application

Once the script completes, open your browser and navigate to:

**http://localhost:8080**

You'll see the Syft LLM Router dashboard where you can:
- Choose your profile (Provider/Client)
- Create and manage routers
- Publish and monetize your services

### Custom Port (Optional)

If you need to use a different port:

```bash
export SYFTBOX_ASSIGNED_PORT=9000
./run.sh
```

---

## 👥 User Flows

### 🔧 **Provider Flow** (Router Creator)

1. **Onboarding**: Choose "Provider" profile during first visit
2. **Create Router**: 
   - Click "Create Router" button in the dashboard
   - Enter router name and select type (Default/Custom)
   - Choose services (Chat/Search)
   - Router is generated and saved to database
3. **Manage Router**:
   - View router in dashboard
   - Check status and health
   - Edit configuration
4. **Publish Router**:
   - Click "Publish" button
   - Add metadata (summary, description, tags)
   - Configure pricing for each service
   - Set charge type (per request, per token, etc.)
   - Router becomes publicly available
5. **Monitor & Monetize**:
   - Track usage and revenue
   - Update pricing as needed
   - Unpublish if necessary

### 👤 **Client Flow** (Router Consumer)

1. **Onboarding**: Choose "Client" profile during first visit
2. **Discover Routers**:
   - Browse published routers in dashboard
   - View summaries, pricing, and service details
   - Filter by tags or services
3. **Use Router**:
   - Click "View Details" to see full documentation
   - Access API endpoints
   - Integrate into your applications
4. **Chat Interface** (if available):
   - Use built-in chat interface
   - Test router capabilities
   - View conversation history

---

## 🎯 Router Types

### **Default Router** (Batteries Included)
- **Chat Service**: Pre-configured Ollama integration
- **Search Service**: Local RAG with ChromaDB
- **Auto-setup**: Dependencies installed automatically
- **Production Ready**: Includes validation and monitoring

### **Custom Router** (Build from Scratch)
- **Template Structure**: Clear TODO comments and examples
- **Flexible Configuration**: Add your own config options
- **Service Placeholders**: Implement your own logic
- **Easy Extension**: Simple to add new service types

---

## 🔌 API Endpoints

### Router Management
- `GET /router/list` - List all routers (filtered by user profile)
- `POST /router/create` - Create a new router via web UI
- `GET /router/exists` - Check if router name is available
- `GET /router/details` - Get detailed router information
- `DELETE /router/delete` - Delete a router (RESTful DELETE method)

### Publishing
- `POST /router/publish` - Publish router with metadata and pricing
- `PUT /router/unpublish` - Unpublish a router (RESTful PUT method)

### User & System
- `GET /username` - Get current user information
- `GET /sburl` - Get SyftBox server URL
- `GET /router/status` - Get router runtime status

---

## 🎨 Frontend Features

### **Modern Dashboard**
- Clean, responsive interface with TailwindCSS
- Real-time data updates
- Loading states and error handling
- Accessible design patterns

### **Router Management**
- **List View**: See all routers with status indicators
- **Detail View**: Comprehensive router information
- **Create Modal**: Step-by-step router creation via web UI
- **Publish Modal**: Multi-step publishing with pricing

### **Service Configuration**
- Toggle switches for enabling/disabling services
- Price input with validation
- Charge type selection (per request, per token, etc.)
- Real-time pricing preview

---

## 🔧 Development

### Backend Development

```bash
cd backend
uv venv -p 3.12 .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

### Frontend Development

```bash
cd frontend
bun install
bun run dev
```

### Database

The application uses SQLite with automatic table creation:

```bash
# Database is automatically created at data/routers.db
# Tables are created on first startup
```

---

## 🚀 Deployment

### Production Setup

```bash
# Build frontend for production
cd frontend
bun run build

# Start backend with production settings
cd backend
uvicorn main:app --host 0.0.0.0 --port 8080 --workers 4
```

### Environment Variables

```bash
# Optional: Set custom port
export SYFTBOX_ASSIGNED_PORT=8080
```

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines

- Use TypeScript for all frontend code
- Follow Preact best practices
- Write reusable, accessible components
- Add proper error handling and loading states
- Keep backend and frontend types in sync
- Test on different screen sizes
- Follow Repository pattern for data access
- Use Pydantic DTOs for API contracts
- Implement proper separation of concerns
- Use eager loading for database queries to avoid N+1 problems

---

## 📝 License

This project is part of the Syft LLM Router ecosystem and is licensed under the same terms as the parent project.

---

## 🆘 Support

- **Documentation**: Check the `backend/router_generator/README.md` for detailed router generation docs
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Discussions**: Join community discussions for questions and ideas

---

<div align="center">

**Built with ❤️ by the OpenMined Community**

[OpenMined](https://www.openmined.org/) • [SyftBox](https://syftbox.net/)
</div>