# API Service

Node/TypeScript backend service.

## Quick Start

```bash
npm install
npm run dev
```

## Development

```bash
npm run dev     # Start with hot reload
npm run build  # Build + frontend
npm start      # Run production
```

## Configuration

Edit `.env`:

```env
PORT=3000
CORS_ORIGINS=*
MODEL_SERVICE_HOST=localhost
MODEL_SERVICE_PORT=50051
```

## Architecture

```
src/
├── routes/        # Express routes
├── services/      # gRPC client
├── main.ts        # Express app
└── config.ts     # Configuration
```

## REST API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/coordinates` | GET | List coordinates |

## gRPC

Communicates with model-service via gRPC.

## Features

- Express server
- gRPC client to model-service
- Static file serving (frontend)
- CORS support