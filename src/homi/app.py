import logging
from abc import ABC, abstractmethod
from typing import Callable, Dict, Generic, List, TypeVar, Union

import grpc
from google.protobuf.descriptor import ServiceDescriptor

from .config import MergeConfig
from .exception import MethodNotFound, RegisterError, ServiceNotFound
from .proto_meta import ServiceMetaData, make_grpc_method_handler, service_metadata_from_descriptor, warp_handler


def NotImplementedMethod(request, context):
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


class BaseApp:
    def __init__(self, config: dict = None, **kwargs):
        self._config: dict = config or {}

    @property
    def config(self):
        return self._config


ConfigType = TypeVar('ConfigType')


class BaseService(Generic[ConfigType], ABC):
    def __init__(
            self,
            service_descriptor: ServiceDescriptor,
            config_class=MergeConfig,
            default_config: ConfigType = None,
            config_name=None,
            **kwargs
    ):
        self._register_methods = {}
        self._app: BaseApp = None
        self._is_registered = False

        self._descriptor = service_descriptor
        self._meta: ServiceMetaData = service_metadata_from_descriptor(service_descriptor)
        self._config: config_class

        self._prepare_config(config_class, config_name, default_config)

        # lifecycle method
        self._after_registered_handler = None
        self._before_server_start_handler = None

    @property
    def descriptor(self):
        return self._descriptor

    @property
    def meta(self):
        return self._meta

    @property
    def full_name(self):
        return self.meta.full_name

    @property
    def name(self):
        return self.meta.name

    @property
    def method_names(self):
        return self.meta.methods.keys()

    def _prepare_config(self, klass, name, default):
        config_name = name or self.full_name
        default_config = default or {}
        self._config = klass(config_name, default_config)

    @property
    def config(self) -> ConfigType:
        if not self.is_registered:
            logging.warning('your get config data before extend registered')
        return self._config.get_config()

    @property
    def app(self):
        if not self.is_registered:
            raise ValueError('you can not get app object before extend registered')
        return self._app

    @property
    def is_registered(self) -> bool:
        if not self._is_registered and self._app:
            self._is_registered = True
        return self._is_registered

    def register_app(self, app):
        self._app = app
        self._config.register_app(app)
        if self._after_registered_handler:
            self._after_registered_handler(self)

    def before_server_start_handler(self):
        if self._before_server_start_handler:
            self._before_server_start_handler(self)

    def after_registered(self, func):
        self._after_registered_handler = func
        return func

    def before_server_start(self, func):
        self._before_server_start_handler = func
        return func

    @abstractmethod
    def add_to_server(self, server):
        raise NotImplementedError('YOU MUST OVERWRITE THIS METHOD!!')
        pass


class Service(Generic[ConfigType], BaseService[ConfigType]):

    def __init__(self, service_descriptor: ServiceDescriptor, config_class=MergeConfig, default_config=None,
                 config_name=None, **kwargs):
        super().__init__(service_descriptor, config_class, default_config, config_name, **kwargs)

        self._method_handler: Dict[str, Callable] = {}

    # method func register decorator
    def method(self, method_name=None, **kwargs):
        def wrapped(func: Callable):
            name = method_name or func.__name__
            if name not in self.meta.methods:
                raise MethodNotFound(name, self.meta.full_name, available_methods=self.meta.methods.keys())
            self._method_handler[name] = func
            return func

        return wrapped

    def register_method(self, method_name, func: Callable, **kwargs):
        self.method(method_name, **kwargs)(func)

    def make_servicer_class(self):
        methods = {}
        for name, method_meta in self.meta.methods.items():
            if name in self._method_handler:
                func = warp_handler(method_meta, self._method_handler[name])
            else:
                func = NotImplementedMethod
            methods[name] = func
        servicer = type(self.full_name, (), methods)
        return servicer

    def _make_generic_handler(self) -> Dict[str, Callable]:
        generic_handler = {}
        for name, method_meta in self.meta.methods.items():
            if name in self._method_handler:
                func = warp_handler(method_meta, self._method_handler[name])
            else:
                func = NotImplementedMethod
            generic_handler[name] = make_grpc_method_handler(method_meta, func, )
        return grpc.method_handlers_generic_handler(self.full_name, generic_handler)

    def add_to_server(self, server):
        server.add_generic_rpc_handlers((self._make_generic_handler(),))


class App(BaseApp):
    def __init__(self, services: List[Union[Service, ServiceDescriptor]] = None, **kwargs):
        super().__init__(**kwargs)

        self._services: Dict[str, Service] = {}

        _services = services or []
        for svc in _services:
            if isinstance(svc, ServiceDescriptor):
                self.add_service_from_descriptor(svc)
            else:
                self.add_service(svc)

    @property
    def service_names(self):
        return self._services.keys()

    @property
    def services(self):
        return self._services.values()

    def get_service_by_full_name(self, full_name: str) -> Service:
        try:
            return self._services[full_name]
        except KeyError:
            raise ServiceNotFound(full_name, available_services=self.service_names)

    def add_service(self, service: Service):
        if not isinstance(service, BaseService):
            raise RegisterError('you must register Service class object')
        self._services[service.full_name] = service
        service.register_app(self)

    def add_service_from_descriptor(self, descriptor: ServiceDescriptor):
        self.add_service(Service(descriptor))

    def method(self, service_full_name: str, method_name: str = None, **kwargs):
        svc = self.get_service_by_full_name(service_full_name)

        def wrapped(func: Callable):
            name = method_name or func.__name__
            svc.register_method(name, func, **kwargs)
            return func

        return wrapped

    def register_method(self, service_full_name: str, method_name: str, func: Callable, **kwargs):
        self.method(service_full_name, method_name, **kwargs)(func)

    def bind_to_server(self, server):
        for svc in self.services:
            svc.before_server_start_handler()

        for svc in self.services:
            svc.add_to_server(server)
