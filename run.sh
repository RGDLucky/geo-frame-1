#!/bin/bash

# Run all services for geo-frame-1
# Usage: ./run.sh

set -e

echo "Starting model-service (gRPC) on port 50051..."
cd model-service
python -c "
import grpc
from concurrent import futures
from app import service_pb2
from app import service_pb2_grpc
from app.config import settings

class ModelServiceServicer(service_pb2_grpc.ModelServiceServicer):
    def ProcessRequest(self, request, context):
        result = f'Processed: {request.input}'
        return service_pb2.Response(
            result=result,
            success=True,
            metadata=dict(request.metadata) if request.metadata else {},
        )

    def HealthCheck(self, request, context):
        return service_pb2.HealthResponse(status='healthy')

server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
service_pb2_grpc.add_ModelServiceServicer_to_server(
    ModelServiceServicer(), server
)
server.add_insecure_port(f'[::]:{settings.api_port}')
server.start()
print(f'Model service running on port {settings.api_port}')
import time
time.sleep(30)
" &
cd ..

echo "Starting api-service on port 8000..."
cd api-service
npm run dev &
cd ..

echo "Starting frontend on port 3000..."
cd frontend
npm run dev &
cd ..

sleep 2

echo ""
echo "Services running:"
echo "  Frontend (hot reload): http://localhost:3000"
echo "  API + Frontend:         http://localhost:8000"
echo "  Model service (gRPC):   localhost:50051"
echo ""
echo "To stop all: lsof -i :3000,8000,50051 -t | xargs kill"