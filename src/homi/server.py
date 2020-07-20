from concurrent import futures

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from .registries import get_default_registry


class Server:
    def __init__(self, host: str = '127.0.0.1', port: str = '50051', worker: int = 10, health: bool = True):
        self.host = host
        self.port = port
        self.worker = worker
        self.load_config_from_env()
        self.server = None
        self.health = health
        self.thread_pool = futures.ThreadPoolExecutor(max_workers=self.worker)
        self.reflection_service_names = [reflection.SERVICE_NAME, ]

    def load_config_from_env(self):
        pass

    def run(self, wait=True):
        registry = get_default_registry()
        self.server = grpc.server(self.thread_pool)
        registry.add_to_server(self.server)
        self.reflection_service_names += registry.service_names

        if self.health:
            self.add_health_service()

        reflection.enable_server_reflection(self.reflection_service_names, self.server)
        self.server.add_insecure_port(f'[::]:{self.port}')
        self.server.start()
        print('run server')
        print(f'# port : {self.port}')
        if wait:
            self.wait_for_termination()

    def stop(self, grace=None):
        if self.server:
            self.server.stop(grace)

    def wait_for_termination(self):
        if self.server:
            self.server.wait_for_termination()

    def add_health_service(self):
        health_servicer = health.HealthServicer(
            experimental_non_blocking=True,
            experimental_thread_pool=self.thread_pool)
        health_servicer.set('', health_pb2.HealthCheckResponse.SERVING)
        for service in self.reflection_service_names:
            health_servicer.set(service, health_pb2.HealthCheckResponse.SERVING)

        health_pb2_grpc.add_HealthServicer_to_server(health_servicer, self.server)
        self.reflection_service_names.append(health.SERVICE_NAME)
