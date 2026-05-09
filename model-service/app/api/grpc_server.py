import grpc
from concurrent import futures
from app.api import service_pb2
from app.api import service_pb2_grpc
from app.config import settings
from app.clients import get_s3_client
from app.model import ModelLoader, convert_image_bytes_to_png


class ModelServiceServicer(service_pb2_grpc.ModelServiceServicer):
    def __init__(self):
        self._model_loader = None
        self._s3_client = get_s3_client()

    @property
    def model_loader(self):
        if self._model_loader is None:
            self._model_loader = ModelLoader()
        return self._model_loader

    def ProcessRequest(self, request, context):
        result = f"Processed: {request.input}"
        return service_pb2.Response(
            result=result,
            success=True,
            metadata=dict(request.metadata) if request.metadata else {},
        )

    def HealthCheck(self, request, context):
        return service_pb2.HealthResponse(status="healthy")

    def ProcessImage(self, request, context):
        results = []
        bucket = request.bucket or settings.s3_bucket_name
        target_size = request.options.target_size if request.options else 260

        for key in request.image_keys:
            try:
                image_bytes = self._s3_client.download_bytes(bucket=bucket, key=key)
                png_bytes = convert_image_bytes_to_png(image_bytes)
                result = self.model_loader.predict(png_bytes)

                results.append(service_pb2.ImageResult(
                    image_key=key,
                    processed_path=f"s3://{bucket}/{key}",
                    success=True,
                ))
            except Exception as e:
                results.append(service_pb2.ImageResult(
                    image_key=key,
                    success=False,
                    error=str(e),
                ))

        return service_pb2.ImageProcessResponse(
            results=results,
            success=all(r.success for r in results),
            error=None if all(r.success for r in results) else "Some images failed",
        )

    def ClassifyDock(self, request, context):
        predictions = []
        bucket = request.bucket or settings.s3_bucket_name

        for key in request.image_keys:
            try:
                image_bytes = self._s3_client.download_bytes(bucket=bucket, key=key)
                png_bytes = convert_image_bytes_to_png(image_bytes)
                result = self.model_loader.predict(png_bytes)

                predictions.append(service_pb2.DockPrediction(
                    image_key=key,
                    class_name=result["class_name"],
                    confidence=result["confidence"],
                    probabilities=result["probabilities"],
                ))
            except Exception as e:
                predictions.append(service_pb2.DockPrediction(
                    image_key=key,
                    class_name="error",
                    confidence=0.0,
                    probabilities=[],
                ))

        return service_pb2.DockClassifyResponse(
            predictions=predictions,
            success=all(p.class_name != "error" for p in predictions),
            error=None,
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_ModelServiceServicer_to_server(
        ModelServiceServicer(), server
    )

    server.add_insecure_port(f"[::]:{settings.api_port}")
    server.start()
    print(f"Model service running on port {settings.api_port}")
    server.wait_for_termination()