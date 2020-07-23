from enum import Enum
from typing import TypeVar, NamedTuple, Any, Dict, Tuple

from google.protobuf import symbol_database
from google.protobuf.descriptor import ServiceDescriptor, MethodDescriptor
from google.protobuf.descriptor_pb2 import ServiceDescriptorProto, MethodDescriptorProto


class MethodType(Enum):
    UNARY_UNARY = 'unary_unary'
    STREAM_UNARY = 'stream_unary'
    UNARY_STREAM = 'unary_stream'
    STREAM_STREAM = 'stream_stream'

    @property
    def is_unary_request(self):
        return 'unary_' in self.value

    @property
    def is_unary_response(self):
        return '_unary' in self.value


IS_REQUEST_STREAM = TypeVar("IS_REQUEST_STREAM")
IS_RESPONSE_STREAM = TypeVar("IS_RESPONSE_STREAM")

MethodTypeMatch: Dict[Tuple[IS_REQUEST_STREAM, IS_RESPONSE_STREAM], MethodType] = {
    (False, False): MethodType.UNARY_UNARY,
    (True, False): MethodType.STREAM_UNARY,
    (False, True): MethodType.UNARY_STREAM,
    (True, True): MethodType.STREAM_STREAM,
}


class MethodMetaData(NamedTuple):
    input_type: Any
    output_type: Any
    method_type: MethodType


class ServiceMetaData(NamedTuple):
    full_name: str
    name: str
    methods: Dict[str, MethodMetaData]


def get_method_metadata(descriptor: MethodDescriptor, proto: MethodDescriptorProto) -> MethodMetaData:
    symbol_db = symbol_database.Default()
    return MethodMetaData(
        input_type=symbol_db.GetPrototype(descriptor.input_type),
        output_type=symbol_db.GetPrototype(descriptor.output_type),
        method_type=MethodTypeMatch[(proto.client_streaming, proto.server_streaming)],
    )


def service_metadata_from_descriptor(service_descriptor: ServiceDescriptor) -> ServiceMetaData:
    svc_desc_proto = ServiceDescriptorProto()
    service_descriptor.CopyToProto(svc_desc_proto)
    methods = {
        proto.name: get_method_metadata(service_descriptor.methods_by_name[proto.name], proto)
        for proto in svc_desc_proto.method
    }

    return ServiceMetaData(
        full_name=service_descriptor.full_name,
        name=service_descriptor.name,
        methods=methods
    )
