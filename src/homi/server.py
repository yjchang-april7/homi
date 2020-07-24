from concurrent import futures

import grpc

from .app import App


class Server:
    def __init__(self, app: App, host: str = '127.0.0.1', port: str = '50051', worker: int = 10):
        self.host = host
        self.port = port
        self.worker = worker
        self.app = app
        self.load_config_from_env()
        self.server = None
        self.thread_pool = futures.ThreadPoolExecutor(max_workers=self.worker)

    def load_config_from_env(self):
        pass

    def run(self, wait=True):
        self.server = grpc.server(self.thread_pool)
        self.app.bind_to_server(self.server)

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
