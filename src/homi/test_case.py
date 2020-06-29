import unittest

import grpc_testing

from .registries import get_default_registry


class HomiTestCase(unittest.TestCase):
    app = None
    _test_server = None

    def get_test_server(self):
        if not self._test_server:
            register = get_default_registry()
            self._test_server = grpc_testing.server_from_dictionary(
                register.test_servicers, grpc_testing.strict_real_time())

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
