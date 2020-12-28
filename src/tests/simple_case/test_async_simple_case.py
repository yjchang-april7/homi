import unittest

import grpc

from . import helloworld_pb2_grpc
from .async_app import app
from .helloworld_pb2 import HelloRequest
from ...homi.test_case import HomiRealServerTestCase


class GreeterTestCase(HomiRealServerTestCase):
    app = app

    def setUp(self):
        super(GreeterTestCase, self).setUp()
        self.endpoint = f'{self.default_server_config["host"]}:{self.default_server_config["port"]}'

    def test_hello_say(self):

        channel = grpc.insecure_channel(self.endpoint)

        stub = helloworld_pb2_grpc.GreeterStub(channel)
        name = 'tom'
        response = stub.SayHello(HelloRequest(name=name))

        self.assertEqual(response.message, f'Hello {name}!')

    def test_hello_say_group(self):
        channel = grpc.insecure_channel(self.endpoint)

        stub = helloworld_pb2_grpc.GreeterStub(channel)
        name = "groupA"
        response = list(stub.SayHelloGroup(HelloRequest(name=name)))

        self.assertEqual(len(response), 4)
        return_names = ['a', 'b', 'c', 'd']
        for idx, rep in enumerate(response):
            self.assertEqual(rep.message, f"Hello {return_names[idx]}!")

    def test_hello_everyone(self):
        channel = grpc.insecure_channel(self.endpoint)

        stub = helloworld_pb2_grpc.GreeterStub(channel)
        names = ["tom", 'sam', 'wony', 'homi']

        response = stub.HelloEveryone((HelloRequest(name=name) for name in names))
        self.assertEqual(response.message, f'Hello everyone {names}!')

    def test_say_hello_one_by_one(self):
        channel = grpc.insecure_channel(self.endpoint)

        stub = helloworld_pb2_grpc.GreeterStub(channel)
        names = ["tom", 'sam', 'wony', 'homi']

        response = list(stub.SayHelloOneByOne((HelloRequest(name=name) for name in names)))

        self.assertEqual(len(response), len(names))

        for rep, name in zip(response, names):
            self.assertEqual(rep.message, f'Hello {name}!')


if __name__ == '__main__':
    unittest.main()
