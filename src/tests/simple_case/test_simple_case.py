import unittest

import grpc

from . import app, helloworld_pb2
from .helloworld_pb2 import HelloRequest
from ...homi import HomiTestCase


class GreeterTestCase(HomiTestCase):
    app = app

    def test_hello_say(self):
        server = self.get_test_server()
        name = "tom"
        request = HelloRequest(name=name)
        method = server.invoke_unary_unary(
            method_descriptor=(helloworld_pb2.DESCRIPTOR.services_by_name['Greeter'].methods_by_name['SayHello']),
            invocation_metadata={},
            request=request, timeout=1)

        response, metadata, code, details = method.termination()
        self.assertEqual(response.message, f'Hello {name}!')
        self.assertEqual(code, grpc.StatusCode.OK)

    def test_hello_say_group(self):
        server = self.get_test_server()
        name = "groupA"
        request = HelloRequest(name=name)
        method = server.invoke_unary_stream(
            method_descriptor=(helloworld_pb2.DESCRIPTOR.services_by_name['Greeter'].methods_by_name['SayHelloGroup']),
            invocation_metadata={},
            request=request, timeout=1)

        reps = self.get_all_response(method)

        self.assertEqual(len(reps), 4)
        return_names = ['a', 'b', 'c', 'd']
        for idx, rep in enumerate(reps):
            self.assertEqual(rep.message, f"Hello {return_names[idx]}!")

        metadata, code, details = method.termination()
        self.assertEqual(code, grpc.StatusCode.OK)

    def test_hello_everyone(self):
        server = self.get_test_server()
        method = server.invoke_stream_unary(
            method_descriptor=(helloworld_pb2.DESCRIPTOR.services_by_name['Greeter'].methods_by_name['HelloEveryone']),
            invocation_metadata={},
            timeout=1
        )

        names = ["tom", 'sam', 'wony', 'homi']
        self.send_request_all(method, (HelloRequest(name=name) for name in names))

        response, metadata, code, details = method.termination()
        self.assertEqual(code, grpc.StatusCode.OK)
        self.assertEqual(response.message, f'Hello everyone {names}!')

    def test_say_hello_one_by_one(self):
        server = self.get_test_server()
        method = server.invoke_stream_stream(
            method_descriptor=(
                helloworld_pb2.DESCRIPTOR.services_by_name['Greeter'].methods_by_name['SayHelloOneByOne']),
            invocation_metadata={},
            timeout=1
        )

        names = ["tom", 'sam', 'wony', 'homi']
        self.send_request_all(method, (HelloRequest(name=name) for name in names))

        reps = self.get_all_response(method)
        self.assertEqual(len(reps), len(names))

        for rep, name in zip(reps, names):
            self.assertEqual(rep.message, f'Hello {name}!')

        metadata, code, details = method.termination()
        self.assertEqual(code, grpc.StatusCode.OK)


if __name__ == '__main__':
    unittest.main()
