from typing import List, Optional

from grpc_health.v1 import health, health_pb2_grpc
from grpc_health.v1.health_pb2 import HealthCheckResponse, _HEALTH
from grpc_reflection.v1alpha import reflection
from grpc_reflection.v1alpha.reflection_pb2 import _SERVERREFLECTION
from typing_extensions import TypedDict

from ..app import BaseService


class ReflectionConfig(TypedDict):
    enable: Optional[bool]
    ignore_service: Optional[List[str]]


class ReflectionService(BaseService[ReflectionConfig]):

    def __init__(self, **kwargs):
        service_descriptor = _SERVERREFLECTION
        default_config: ReflectionConfig = ReflectionConfig(
            enable=True,
            ignore_service=[]
        )

        super().__init__(
            service_descriptor=service_descriptor,
            default_config=default_config,
            config_name='reflection',
            **kwargs
        )

    @property
    def reflection_services(self):
        return [name for name in self.app.service_names if name not in self.config['ignore_service']]

    def add_to_server(self, server):
        if self.config['enable']:
            reflection.enable_server_reflection(self.reflection_services, server)


reflection_service = ReflectionService()


class HealthConfig(TypedDict):
    enable: Optional[bool]
    not_serving: Optional[List[str]]


class HealthService(BaseService[HealthConfig]):

    def __init__(self, **kwargs):
        service_descriptor = _HEALTH
        default_config = HealthConfig(
            enable=True,
            not_serving=[]
        )

        super().__init__(
            service_descriptor=service_descriptor,
            default_config=default_config,
            config_name='health',
            **kwargs
        )

    def add_to_server(self, server):
        if self.config['enable']:
            health_servicer = health.HealthServicer(experimental_non_blocking=True)
            health_servicer.set('', HealthCheckResponse.SERVING)
            for svc in self.app.service_names:
                if svc in self.config['not_serving']:
                    status = HealthCheckResponse.NOT_SERVING
                else:
                    status = HealthCheckResponse.SERVING
                health_servicer.set(svc, status)
            health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)


health_service = HealthService()
