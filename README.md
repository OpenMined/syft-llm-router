# Syft LLM Router

A modern, full-stack platform for creating, managing, and publishing Language Model (LLM) routers, built on SyftBox. Includes a Python backend (FastAPI, SyftBox) and a Preact/TypeScript/TailwindCSS frontend.

---

## Features
- **Modern Dashboard UI**: Clean, responsive, and accessible frontend
- **Router Management**: Create, list, and manage LLM routers
- **Service Pricing**: Enable/disable services, set per-service pricing, and select charge type with modern toggle switches
- **Real-time Feedback**: Loading states, error handling, and success animations
- **Type Safety**: Full TypeScript support on frontend, Pydantic on backend
- **Easy Deployment**: Static frontend build, simple backend launch

---

## Tech Stack
- **Backend**: Python 3.12+, FastAPI, SyftBox, SQLModel, Uvicorn
- **Frontend**: Preact, TypeScript, TailwindCSS, Vite, Bun

---

## Prerequisites
- [Python 3.12+](https://www.python.org/)
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- [Bun](https://bun.sh/) (for frontend)

---

## Quickstart

### 1. Start the Backend
```bash
./backend/run.sh
```
- This sets up a virtual environment, installs dependencies, and starts the FastAPI server (default: http://localhost:8080)

### 2. Start the Frontend
```bash
./run_frontend.sh
```
- This installs frontend dependencies (if needed) and starts the dev server (http://localhost:3000)
- The frontend proxies API requests to the backend

---

## Project Structure
```
syft-llm-router/
├── backend/
│   ├── app.py                # FastAPI app entrypoint
│   ├── run.sh                # Backend launch script
│   ├── requirements.txt      # Python dependencies
│   ├── router_generator/     # Router code generation logic
│   └── ...                   # Other backend modules
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── router/       # Router management UI
│   │   │   └── shared/       # Shared UI components
│   │   ├── services/         # API service functions
│   │   ├── types/            # TypeScript types
│   │   ├── utils/            # Utilities
│   │   ├── App.tsx           # Main app
│   │   └── ...
│   ├── run_frontend.sh       # Frontend launch script
│   └── ...
├── run_api.sh                # (Optional) API launch helper
├── README.md                 # This file
└── ...
```

---

## API Endpoints (Backend)
- `GET /api/router/list` — List all routers
- `POST /api/router/create` — Create a new router
- `GET /api/router/exists` — Check if a router exists
- `POST /api/router/publish` — Publish a router (with per-service pricing, enable/disable, charge type)
- `GET /api/router/details` — Get router details
- `POST /api/router/delete` — Delete a router
- `GET /api/username` — Get current user info

---

## Modern Frontend Features
- **Router List**: See all routers, their status, summary, and enabled services with pricing
- **Router Details**: Spacious, two-column dashboard with summary, tags, meta info, and a modern services card
- **Publish Modal**: Enable/disable services with toggle switches, set price (float input), and select charge type (dropdown)
- **Type Safety**: All API data is strictly typed
- **Responsive Design**: Works on desktop and mobile

---

## Development Tips
- **TypeScript**: All frontend code is typed; use `src/types/` for shared types
- **TailwindCSS**: Use utility classes for styling; custom styles in `src/index.css`
- **Component Structure**: Add new UI in `src/components/`; keep logic in `src/services/` and `src/utils/`
- **Backend**: Use Pydantic models for request/response validation

---

## Build & Deployment
- **Frontend**: Build with `bun run build` (output in `frontend/dist/`)
- **Backend**: Deploy with Uvicorn or your preferred ASGI server
- **Static Assets**: Serve `frontend/dist/` with any static file server if needed

---

## Contributing
1. Use TypeScript and Preact best practices
2. Write reusable, accessible components
3. Add error handling and loading states
4. Test on different screen sizes
5. Keep backend and frontend types in sync

---

## License
This project is part of the Syft LLM Router ecosystem.
