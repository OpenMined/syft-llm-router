# Syft LLM Router Frontend

A modern, static frontend for managing Syft LLM Router projects built with Preact, TypeScript, and TailwindCSS.

## Features

- **Modern UI**: Clean, responsive design with TailwindCSS
- **Static Build**: Compiles to static assets with no runtime dependencies
- **Type Safety**: Full TypeScript support with strict type checking
- **Router Management**: Create, list, and manage router projects
- **Real-time Feedback**: Loading states, success animations, and error handling
- **Copy to Clipboard**: Easy project directory copying

## Tech Stack

- **Preact**: Lightweight React alternative
- **TypeScript**: Type-safe development
- **TailwindCSS**: Utility-first CSS framework
- **Vite**: Fast build tool and dev server
- **Bun**: JavaScript runtime and package manager

## Getting Started

### Prerequisites

- [Bun](https://bun.sh/) installed on your system
- Backend API running on `http://localhost:8000`

### Installation

1. Install dependencies:
   ```bash
   bun install
   ```

2. Start the development server:
   ```bash
   bun run dev
   ```

3. Open your browser to `http://localhost:3000`

### Building for Production

```bash
bun run build
```

The built files will be in the `dist/` directory.

### Type Checking

```bash
bun run type-check
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── router/
│   │   │   ├── RouterList.tsx          # Main router list component
│   │   │   └── CreateRouterModal.tsx   # Create router modal
│   │   └── shared/
│   │       ├── Button.tsx              # Reusable button component
│   │       └── Modal.tsx               # Reusable modal component
│   ├── services/
│   │   └── routerService.ts            # API service functions
│   ├── types/
│   │   └── router.ts                   # TypeScript type definitions
│   ├── utils/
│   │   └── clipboard.ts                # Clipboard utility
│   ├── App.tsx                         # Main app component
│   ├── main.tsx                        # Entry point
│   └── index.css                       # Global styles
├── package.json                        # Dependencies and scripts
├── vite.config.ts                      # Vite configuration
├── tailwind.config.js                  # TailwindCSS configuration
└── tsconfig.json                       # TypeScript configuration
```

## API Integration

The frontend integrates with the following backend endpoints:

- `GET /api/router/list` - List all routers
- `POST /api/router/create` - Create a new router
- `GET /api/router/exists` - Check if router exists
- `POST /api/router/publish` - Publish a router

## Development

### Adding New Components

1. Create the component in the appropriate directory under `src/components/`
2. Export the component from an `index.ts` file if needed
3. Import and use in your app

### Styling

- Use TailwindCSS utility classes for styling
- Custom styles can be added to `src/index.css`
- Component-specific styles should use TailwindCSS classes

### Type Safety

- All API responses are typed in `src/types/router.ts`
- Use TypeScript interfaces for component props
- Enable strict mode in `tsconfig.json`

## Build Output

The build process creates optimized static assets:

- **HTML**: `dist/index.html` - Entry point
- **CSS**: `dist/assets/index-*.css` - Compiled styles
- **JS**: `dist/assets/index-*.js` - Compiled JavaScript

All assets are optimized for production with:
- Minification
- Tree shaking
- Code splitting
- Asset optimization

## Browser Support

- Modern browsers with ES2020 support
- No polyfills required for core functionality
- Graceful degradation for older browsers

## Contributing

1. Follow TypeScript best practices
2. Use Preact hooks for state management
3. Write reusable components
4. Add proper error handling
5. Test with different screen sizes
6. Ensure accessibility compliance

## License

This project is part of the Syft LLM Router ecosystem. 