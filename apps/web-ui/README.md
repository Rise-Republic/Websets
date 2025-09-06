# WebSets Frontend (web-ui)

React-based frontend application for the WebSets enterprise data mining platform.

## Architecture

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS + shadcn/ui components
- **Authentication**: WorkOS AuthKit
- **State Management**: React hooks + Context API
- **Testing**: Jest + React Testing Library

## Development Setup

### Prerequisites
- Node.js 20+ (required by Vite)
- npm or yarn

### Local Development
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm test
```

### Environment Variables
Create a `.env` file based on `.env.example`:

```bash
# WorkOS Configuration
VITE_WORKOS_CLIENT_ID=your_workos_client_id
VITE_WORKOS_REDIRECT_URI=http://localhost:3000/auth/workos/callback

# API Configuration
VITE_API_BASE=http://localhost:8000
```

## Docker Deployment

The frontend is containerized using a multi-stage Docker build:

```dockerfile
# Build stage with Node.js
FROM node:20-alpine AS build
# ... build process

# Runtime stage with Nginx
FROM nginx:alpine
# ... serve static files
```

### Container Ports
- **Development**: 3000 (Vite dev server)
- **Production**: 80 (Nginx)

## API Integration

The frontend communicates with the API Gateway at `http://localhost:8000`:

- **Authentication**: `/api/v1/auth/*`
- **Jobs**: `/api/v1/jobs/*`
- **Datasets**: `/api/v1/datasets/*`
- **Health**: `/health`

## Component Structure

```
src/
├── components/          # Reusable UI components
│   ├── Auth/           # Authentication components
│   ├── Dashboard/      # Dashboard views
│   ├── Search/         # Search interface
│   └── ui/            # shadcn/ui components
├── hooks/              # Custom React hooks
├── services/           # API service layer
└── __tests__/         # Test files
```

## Key Features

- **Enterprise Login**: WorkOS-powered authentication
- **Responsive Design**: Mobile-first with Tailwind CSS
- **Real-time Updates**: WebSocket integration for job status
- **Accessibility**: WCAG 2.1 AA compliant
- **Performance**: Code splitting and lazy loading

## Testing

```bash
# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Run accessibility tests
npm run test:a11y
```

## Deployment

The frontend is deployed as a static site served by Nginx with API proxying configured.

### Health Checks
- **Container**: `wget --spider http://localhost/`
- **Application**: Checks for successful page load

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure API Gateway allows frontend origin
2. **WorkOS Errors**: Verify client ID and redirect URI configuration
3. **Build Failures**: Check Node.js version (requires 20+)

### Logs
```bash
# Container logs
docker logs compose-web-ui-1

# Development server logs
npm run dev
```
