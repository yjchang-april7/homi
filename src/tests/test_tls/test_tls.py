import unittest

import grpc

from . import helloworld_pb2_grpc
from .app import app
from .helloworld_pb2 import HelloRequest
from ...homi.test_case import HomiRealServerTestCase


class TlsTestCase(HomiRealServerTestCase):
    app = app
    tls = True

    def test_hello_say(self):

        channel = grpc.secure_channel(f'{self.default_server_config["host"]}:{self.default_server_config["port"]}',
                                      self.channel_credentials)

        stub = helloworld_pb2_grpc.GreeterStub(channel)
        name = 'tom'
        response = stub.SayHello(HelloRequest(name=name))

        self.assertEqual(response.message, f'Hello {name}!')

    def test_hello_say_group(self):
        channel = grpc.secure_channel(f'{self.default_server_config["host"]}:{self.default_server_config["port"]}',
                                      self.channel_credentials)

        stub = helloworld_pb2_grpc.GreeterStub(channel)
        name = "groupA"
        response = list(stub.SayHelloGroup(HelloRequest(name=name)))

        self.assertEqual(len(response), 4)
        return_names = ['a', 'b', 'c', 'd']
        for idx, rep in enumerate(response):
            self.assertEqual(rep.message, f"Hello {return_names[idx]}!")

    def test_hello_everyone(self):
        channel = grpc.secure_channel(f'{self.default_server_config["host"]}:{self.default_server_config["port"]}',
                                      self.channel_credentials)

        stub = helloworld_pb2_grpc.GreeterStub(channel)
        names = ["tom", 'sam', 'wony', 'homi']

        response = stub.HelloEveryone((HelloRequest(name=name) for name in names))
        self.assertEqual(response.message, f'Hello everyone {names}!')

    def test_say_hello_one_by_one(self):
        channel = grpc.secure_channel(f'{self.default_server_config["host"]}:{self.default_server_config["port"]}',
                                      self.channel_credentials)

        stub = helloworld_pb2_grpc.GreeterStub(channel)
        names = ["tom", 'sam', 'wony', 'homi']

        response = list(stub.SayHelloOneByOne((HelloRequest(name=name) for name in names)))

        self.assertEqual(len(response), len(names))

        for rep, name in zip(response, names):
            self.assertEqual(rep.message, f'Hello {name}!')

    def test_fail_try_connect_insecure_channel(self):
        channel = grpc.insecure_channel(f'{self.default_server_config["host"]}:{self.default_server_config["port"]}')

        stub = helloworld_pb2_grpc.GreeterStub(channel)
        name = 'tom'
        with self.assertRaises(grpc._channel._InactiveRpcError) as _:
            stub.SayHello(HelloRequest(name=name))

    def test_fail_try_wrong_credentials(self):
        cert = b'abcd'
        wrong_credentials = grpc.ssl_channel_credentials(cert)
        channel = grpc.secure_channel(f'{self.default_server_config["host"]}:{self.default_server_config["port"]}',
                                      wrong_credentials)
        stub = helloworld_pb2_grpc.GreeterStub(channel)
        name = 'tom'
        with self.assertRaises(grpc._channel._InactiveRpcError) as _:
            stub.SayHello(HelloRequest(name=name))


if __name__ == '__main__':
    unittest.main()
