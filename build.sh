#!/bin/bash

# Build script for geo-frame-1
# Run this before docker-compose up --build

set -e

echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo "Building Docker images..."
docker-compose build --no-cache

echo "Done. Run 'docker-compose up' to start services."