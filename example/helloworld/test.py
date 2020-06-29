import unittest

import grpc
import grpc_testing
from homi import get_default_registry

import app
import helloworld_pb2
from helloworld_pb2 import HelloRequest


class GrpcTestCase(unittest.TestCase):
    app = None
    _test_server = None

    def get_test_server(self):
        if not self._test_server:
            register = get_default_registry()
            self._test_server = grpc_testing.server_from_dictionary(
                register.test_servicers, grpc_testing.strict_real_time())

        return self._test_server


class GreeterTestCase(GrpcTestCase):
    app = app

    def test_hello_say(self):
        server = self.get_test_server()
        name = "tom"
        request = HelloRequest(name=name)
        method = server.invoke_unary_unary(
            method_descriptor=(helloworld_pb2.DESCRIPTOR
                .services_by_name['Greeter']
                .methods_by_name['SayHello']),
            invocation_metadata={},
            request=request, timeout=1)

        response, metadata, code, details = method.termination()
        self.assertEqual(response.message, f'Hello {name}!')
        self.assertEqual(code, grpc.StatusCode.OK)

    def test_hello_everyone(self):
        server = self.get_test_server()
        method = server.invoke_stream_unary(
            method_descriptor=(helloworld_pb2.DESCRIPTOR
                .services_by_name['Greeter']
                .methods_by_name['HelloEveryone']),
            invocation_metadata={},
            timeout=1
        )

        names = ["tom", 'sam', 'wony', 'homi']
        for name in names:
            method.send_request(HelloRequest(name=name))
        method.requests_closed()

        response, metadata, code, details = method.termination()
        self.assertEqual(code, grpc.StatusCode.OK)
        self.assertEqual(response.message, f'Hello everyone {names}!')


if __name__ == '__main__':
    unittest.main()
