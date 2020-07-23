import logging
from abc import ABC, abstractmethod
from typing import List, Callable

from google.protobuf.descriptor import ServiceDescriptor

from src.homi.proto_meta import ServiceMetaData, service_metadata_from_descriptor


def NotImplementedMethod(request, context):
    pass


class BaseApp:
    def __init__(self, config: dict = None, **kwargs):
        self._config: dict = config or {}
        pass

    @property
    def config(self):
        return self._config


class BaseServiceConfig(ABC):
    def __init__(self, name: str, default: dict = None):
        self._default = default
        self.name = name
        self.app: BaseApp = None

    def register_app(self, app: BaseApp):
        self.app = app

    def get_config(self) -> dict:
        return self._default


class MergeConfig(BaseServiceConfig):

    def register_app(self, app: BaseApp):
        super().register_app(app)
        app_config = self.app.config.get(self.name)
        if app_config:
            self._default.update(app_config)


class BaseService(ABC):
    def __init__(
            self,
            service_descriptor: ServiceDescriptor,
            config_class=MergeConfig,
            default_config=None,
            config_name=None,
            **kwargs
    ):
        self._register_methods = {}
        self._app: BaseApp = None
        self._is_registered = False

        self._meta: ServiceMetaData = service_metadata_from_descriptor(service_descriptor)
        self._config: config_class

        self._prepare_config(config_class, config_name, default_config)

        # lifecycle method
        self._after_registered_handler = None
        self._before_server_start_handler = None

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
    def config(self) -> dict:
        if not self.is_registered:
            logging.warning('your get config data before service registered')
        return self._config.get_config()

    @property
    def app(self):
        if not self.is_registered:
            raise ValueError('you can not get app object before service registered')
        return self._app

    @property
    def is_registered(self) -> bool:
        if not self._is_registered and self.app:
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


class Service(BaseService):

    def __init__(self, service_descriptor: ServiceDescriptor, config_class=MergeConfig, default_config=None,
                 config_name=None, **kwargs):
        super().__init__(service_descriptor, config_class, default_config, config_name, **kwargs)

        self.method_handler = {}

    # method func register decorator
    def method(self, name=None, **kwargs):
        pass

    def register_method(self, name, func: Callable, **kwargs):
        # manual register method
        pass

    def add_to_server(self, server):
        pass


class App(BaseApp):
    def __init__(self, services: List[Service] = None, **kwargs):
        super().__init__(**kwargs)
        self._services: List[Service] = services

    def add_service(self, service: Service):
        self._services.append(service)
        service.register_app(self)

    @property
    def services(self):
        return self._services

    def bind_to_server(self, server):
        for svc in self.services:
            svc.add_to_server(server)
