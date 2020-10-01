import os
from concurrent import futures

import grpc

from .app import App
from .exception import ServerSSLConfigError


class Server:
    def __init__(self,
                 app: App,
                 host: str = None,
                 port: str = '50051',
                 worker: int = 10,
                 debug: bool = False,
                 alts: bool = False,
                 private_key: bytes = None,
                 certificate: bytes = None,
                 ):
        self.host = host
        self.port = port
        self.worker = worker
        self.app = app
        self.debug = debug
        self.load_config_from_env()
        self.alts = alts
        self.private_key = private_key
        self.certificate = certificate
        self.server = None
        self._server_credentials = None
        self.thread_pool = futures.ThreadPoolExecutor(max_workers=self.worker)

    def load_config_from_env(self):
        pass

    @property
    def endpoint(self):
        host = self.host if self.host else "[::]"
        return f'{host}:{self.port}'

    @property
    def server_credentials(self):
        if not self._server_credentials:
            self._server_credentials = grpc.ssl_server_credentials(
                ((self.private_key, self.certificate,),))
        return self._server_credentials

    def _add_port(self):
        if self.alts:
            self.server.add_secure_port(self.endpoint, grpc.alts_server_credentials())
        elif self.private_key and self.certificate:
            self.server.add_secure_port(self.endpoint, self.server_credentials)
        elif self.private_key or self.certificate:
            # error
            raise ServerSSLConfigError('If you want enable ssl feature, You Must set tls_key, certificate config both ')
        else:
            self.server.add_insecure_port(self.endpoint)

    def run(self, wait=True):
        if self.debug:
            os.environ['GRPC_VERBOSITY'] = 'debug'
        self.server = grpc.server(self.thread_pool)
        self.app.bind_to_server(self.server)
        self._add_port()
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
