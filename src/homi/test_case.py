import asyncio
import datetime
import logging
import threading
import unittest
from asyncio import Queue as AsyncQueue
from time import sleep
from typing import Any, Dict

import grpc
import grpc_testing
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from . import App, AsyncApp, AsyncServer, Server, Service


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
    alts = False
    tls = False
    _tls_key = None
    _certificate = None
    test_server_config: Dict[str, Any] = {}
    test_server = None

    @property
    def tls_key(self):
        if not self._tls_key:
            self._tls_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        return self._tls_key

    @property
    def certificate(self):
        if not self._certificate:
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"California"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "My Company"),
                x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            ])
            self._certificate = x509.CertificateBuilder() \
                .subject_name(subject) \
                .issuer_name(issuer) \
                .public_key(self.tls_key.public_key()) \
                .serial_number(x509.random_serial_number()) \
                .not_valid_before(datetime.datetime.utcnow()) \
                .not_valid_after(
                # Our certificate will be valid for 10 days
                datetime.datetime.utcnow() + datetime.timedelta(days=10)
            ) \
                .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]),
                               critical=False, ).sign(self.tls_key, hashes.SHA256())
        return self._certificate

    @property
    def channel_credentials(self):
        if self.alts:
            return grpc.alts_channel_credentials()
        elif self.tls:
            cert = self.certificate.public_bytes(serialization.Encoding.PEM)
            return grpc.ssl_channel_credentials(cert)
        return None

    @property
    def tls_config(self):
        if not self.tls:
            return {}
        else:
            return {
                "private_key": self.tls_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                ),
                "certificate": self.certificate.public_bytes(serialization.Encoding.PEM),
            }

    def get_server_config(self, merge_config: dict = None):
        config = merge_config or {}

        return {
            **self.default_server_config,
            **self.test_server_config,
            **self.tls_config,
            **config,
        }

    def server_restart(self, merge_config: dict = None):
        self.run_real_server(merge_config)

    def _run_async_server(self, config):
        self.test_server = AsyncServer(self.app, **self.get_server_config(config))
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.que = AsyncQueue()

        def run_server(loop, server, q):
            async def operator(server, q):
                await server.run(wait=False)
                await q.get()
                await server.stop()
                logging.debug('test server stopped')

            loop.run_until_complete(operator(server, q))

        self.thread = threading.Thread(target=run_server, args=(self.loop, self.test_server, self.que))
        self.thread.start()
        # todo: find how to wait until on server
        sleep(0.02)

    def run_real_server(self, merge_config: dict = None):
        config = merge_config or {}
        if self.test_server:
            try:
                self.test_server.stop()
            except Exception:
                pass
        if isinstance(self.app, AsyncApp):
            self._run_async_server(config)
        else:
            self.test_server = Server(self.app, **self.get_server_config(config))
            self.test_server.run(wait=False)

    def setUp(self):
        super().setUp()
        self.run_real_server()

    def server_stop(self):
        if isinstance(self.app, AsyncApp):
            self.loop.call_soon_threadsafe(self.que.put_nowait, 'stop')
            self.thread.join()
            del self.thread
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()
        else:
            self.test_server.stop()

    def tearDown(self):
        super().tearDown()
        self.server_stop()
