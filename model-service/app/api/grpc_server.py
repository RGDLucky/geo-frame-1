import grpc
from concurrent import futures
from app import service_pb2
from app import service_pb2_grpc
from app.config import settings


class ModelServiceServicer(service_pb2_grpc.ModelServiceServicer):
    def ProcessRequest(self, request, context):
        result = f"Processed: {request.input}"
        return service_pb2.Response(
            result=result,
            success=True,
            metadata=dict(request.metadata) if request.metadata else {},
        )

    def HealthCheck(self, request, context):
        return service_pb2.HealthResponse(status="healthy")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_ModelServiceServicer_to_server(
        ModelServiceServicer(), server
    )

    server.add_insecure_port(f"[::]:{settings.api_port}")
    server.start()
    print(f"Model service running on port {settings.api_port}")
    server.wait_for_termination()