from typing import Iterator, List


class HomiException(Exception):
    pass


class RegisterError(HomiException):
    pass


class ServerConfigError(HomiException):
    pass


class ServerSSLConfigError(ServerConfigError):
    pass


class ProtobufError(HomiException):
    pass


class ServiceNotFound(ProtobufError):
    def __init__(self, service_name, available_services: Iterator[str] = None, **kwargs):
        self.fail_service = service_name
        self.services = available_services

    def __str__(self):
        msg = f"Can not find {self.fail_service} in app. you must add service"
        return f"{msg} or you can use this services {', '.join(self.services)}" if self.services else self.msg


class MethodNotFound(ProtobufError):
    def __init__(self, method_name, service_name=None, available_methods: List[str] = None, **kwargs):
        self.fail_method = method_name
        self.service_name = service_name or ''
        self.methods = available_methods

    def __str__(self):
        msg = f"Can not find {self.fail_method} in {self.service_name}."
        return f"{msg} available methods is {', '.join(self.methods)}" if self.methods else self.msg
