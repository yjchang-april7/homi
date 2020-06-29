import types
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


def parse_to_dict(item, message):
    return json_format.ParseDict(item, message) if isinstance(item, dict) else item


def parse_stream_return(results, message):
    for item in results:
        yield parse_to_dict(item, message)


class GrpcService:
    def __init__(self, pkg: Package, name: str, pb2: None):
        self.name = name
        self.pb2 = pb2
        self._descriptor = None
        self.add_service_func = getattr(pkg, f"add_{self.name}Servicer_to_server")
        self.__methods = {}

    def add_method(self, name: str, func: Callable):
        self.__methods[name] = func

    def warp_handler(self, func, message):
        sig = signature(func)
        parameters = [k for k, v in sig._parameters.items() if v.kind.value == 1]
        print(parameters)

        def decorator(self, request, context):
            # parse request
            if isinstance(request, abc.Iterable):  # request stream
                result = func(stream_request(request), context)
            else:  # request unary
                request_dict = json_format.MessageToDict(request)
                args = {}
                for p in parameters:
                    args[p] = request_dict.get(p, None)

                result = func(**args, request=request, context=context)

            # parse response
            if isinstance(result, types.GeneratorType):  # return stream
                return parse_stream_return(result, message)
            else:  # return anary
                return parse_to_dict(result, message)

        return decorator

    @property
    def descriptor(self):
        if not self._descriptor:
            self._descriptor = self.pb2.DESCRIPTOR.services_by_name[self.name]
        return self._descriptor

    def get_response_msg_type(self, name):
        return self.descriptor.methods_by_name[name].output_type._concrete_class

    def make_servicer(self):
        methods = {
            k: self.warp_handler(func, self.get_response_msg_type(k)())
            for k, func in self.__methods.items()
        }
        servicer = type(self.name, (), methods)
        return servicer()

    def add_to_server(self, server):
        self.add_service_func(self.make_servicer(), server)


def find_pb2_module(pkg) -> List[types.ModuleType]:
    return [v for k, v in pkg.__dict__.items() if isinstance(v, types.ModuleType) and hasattr(v, 'DESCRIPTOR')]


def find_module_by_has_service_name(modules: List[types.ModuleType], name: str) -> types.ModuleType:
    for module in modules:
        if module.DESCRIPTOR.services_by_name.get(name):
            return module


class GrpcServiceRegister:
    def __init__(self):
        self.files: Dict[Package, Dict[str, GrpcService]] = {}
        self.pkg_pb2: Dict[Package, List[types.ModuleType]] = {}

    def add(self, pkg, service, method, func):
        print(pkg, service, method)
        if not self.files.get(pkg):
            self.files[pkg] = {}
            self.pkg_pb2[pkg] = find_pb2_module(pkg)
        if not self.files[pkg].get(service):
            pb2 = find_module_by_has_service_name(self.pkg_pb2[pkg], service)
            self.files[pkg][service] = GrpcService(pkg, service, pb2)

        self.files[pkg][service].add_method(method, func)

    def add_to_server(self, server):
        for services in self.files.values():
            for service in services.values():
                service.add_to_server(server)

    @property
    def services(self) -> List[Any]:
        svcs = []
        for module, services in self.files.items():
            for name, service in services.items():
                svcs.append(service.descriptor)
        return svcs

    @property
    def test_servicers(self) -> Dict[Any, Any]:  # for testcase
        servicers = {}
        for module, services in self.files.items():

            for name, service in services.items():
                servicers[service.descriptor] = service.make_servicer()
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
