from concurrent import futures

import grpc
from grpc_reflection.v1alpha import reflection

from .registries import get_default_registry


class Server:
    def __init__(self, host: str = '127.0.0.1', port: str = '50051', worker: int = 10):
        self.host = host
        self.port = port
        self.worker = worker
        self.load_config_from_env()
        self.server = None

    def load_config_from_env(self):
        pass

    def run(self):
        registry = get_default_registry()
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=self.worker))
        registry.add_to_server(self.server)
        SERVICE_NAMES = (
            *registry.service_names,
            reflection.SERVICE_NAME,
        )
        reflection.enable_server_reflection(SERVICE_NAMES, self.server)
        self.server.add_insecure_port(f'[::]:{self.port}')
        self.server.start()
        print('run server')
        print(f'# port : {self.port}')
        self.server.wait_for_termination()
