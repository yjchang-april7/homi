import unittest
from typing import Any, Dict

import grpc_testing

from . import Server, App, Service


class HomiTestCase(unittest.TestCase):
    app: App = None
    _test_server = None

    def get_test_server(self):
        if not self._test_server:
            servicers = {}
            for svc in self.app.services:
                if isinstance(svc, Service):
                    servicers[svc.descriptor] = svc.make_servicer_class()

            self._test_server = grpc_testing.server_from_dictionary(
                servicers, grpc_testing.strict_real_time()
            )
        return self._test_server

    @staticmethod
    def get_all_response(method):
        finish = False
        result = []
        while not finish:
            try:
                result.append(method.take_response())
            except Exception:
                finish = True
        return result

    @staticmethod
    def send_request_all(method, requests):
        [method.send_request(req) for req in requests]
        method.requests_closed()


class HomiRealServerTestCase(unittest.TestCase):
    app = None
    default_server_config = {
        "host": "localhost",
        "port": '5999'
    }
    test_server_config: Dict[str, Any] = {}
    test_server = None

    def get_server_config(self, merge_config: dict = None):
        config = merge_config or {}
        return {
            **self.default_server_config,
            **self.test_server_config,
            **config,
        }

    def server_restart(self, merge_config: dict = None):
        self.run_real_server(merge_config)

    def run_real_server(self, merge_config: dict = None):
        config = merge_config or {}
        if self.test_server:
            try:
                self.test_server.stop()
            except Exception:
                pass
        self.test_server = Server(**self.get_server_config(config))
        self.test_server.run(wait=False)

    def setUp(self):
        self.run_real_server()

    def tearDown(self):
        self.test_server.stop()
