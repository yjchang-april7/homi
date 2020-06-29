from collections import abc
from functools import partial
from inspect import signature
from typing import Dict, Callable, TypeVar, List, Any

from google.protobuf import json_format

Package = TypeVar('Package')


class StreamMessage(Dict):
    raw_data = None


def stream_request(request_iterator):
    for req in request_iterator:
        msg = StreamMessage(**json_format.MessageToDict(req))
        msg.raw_data = req
        yield msg


class GrpcService:
    def __init__(self, pkg: Package, name: str):
        self.name = name
        self.add_service_func = getattr(pkg, f"add_{self.name}Servicer_to_server")
        self.__methods = {}

    def add_method(self, name: str, func: Callable):
        self.__methods[name] = func

    def warp_handler(self, func):
        sig = signature(func)
        parameters = [k for k, v in sig._parameters.items() if v.kind.value == 1]
        print(parameters)

        def decorator(self, request, context):
            if isinstance(request, abc.Iterable):
                return func(stream_request(request), context)
            else:
                request = json_format.MessageToDict(request)
                print(request)
                args = {}
                for p in parameters:
                    args[p] = request.get(p, None)
                print(args)

                return func(**args, request=request, context=context)

        return decorator

    def make_servicer(self):
        methods = {
            k: self.warp_handler(func)
            for k, func in self.__methods.items()
        }
        servicer = type(self.name, (), methods)
        return servicer()

    def add_to_server(self, server):
        self.add_service_func(self.make_servicer(), server)


class GrpcServiceRegister:
    def __init__(self):
        self.files: Dict[Package, Dict[str, GrpcService]] = {}

    def add(self, pkg, service, method, func):
        print(pkg, service, method)
        if not self.files.get(pkg):
            self.files[pkg] = {}
        if not self.files[pkg].get(service):
            self.files[pkg][service] = GrpcService(pkg, service)

        self.files[pkg][service].add_method(method, func)

    def add_to_server(self, server):
        for services in self.files.values():
            for service in services.values():
                service.add_to_server(server)

    @property
    def services(self) -> List[Any]:
        svcs = []
        for module, services in self.files.items():
            try:
                pb2_name = [k for k in module.__dict__.keys() if k[-5:] == '__pb2'][0]
                pb2 = getattr(module, pb2_name)
            except Exception as e:
                raise Exception(f"can't find pb2 file in {module} grpc file")
            for service in services.keys():
                svcs.append(pb2.DESCRIPTOR.services_by_name[service])
        return svcs

    @property
    def test_servicers(self) -> Dict[Any, Any]:  # for testcase
        servicers = {}
        for module, services in self.files.items():
            try:
                pb2_name = [k for k in module.__dict__.keys() if k[-5:] == '__pb2'][0]
                pb2 = getattr(module, pb2_name)
            except Exception as e:
                raise Exception(f"can't find pb2 file in {module} grpc file")
            for name, service in services.items():
                servicers[pb2.DESCRIPTOR.services_by_name[name]] = service.make_servicer()
        return servicers

    @property
    def service_names(self) -> List[str]:
        return [svc.full_name for svc in self.services]


_default_registry = None


def get_default_registry() -> GrpcServiceRegister:
    """
    Get the default registry to be used by the decorators and the reactor
    unless the explicit registry is provided to them.
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = GrpcServiceRegister()
    return _default_registry


class WrapHandler:
    def __init__(self, pkg, service, method, func: Callable = None):
        self.func = func
        self.method = method or self.func.__name__
        get_default_registry().add(pkg, service, self.method, self.func)


def register(pkg, service, method=None):
    return partial(WrapHandler, pkg, service, method)
