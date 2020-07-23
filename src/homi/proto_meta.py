from enum import Enum
from functools import partial
from inspect import signature
from typing import TypeVar, NamedTuple, Any, Dict, Tuple

import grpc
from google.protobuf import symbol_database, json_format
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
    name: str
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
        name=descriptor.name,
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


def make_grpc_method_handler(method_meta: MethodMetaData, func):
    handler = getattr(grpc, f"{method_meta.method_type.value}_rpc_method_handler")
    return handler(
        func,
        request_deserializer=method_meta.input_type.FromString,
        response_serializer=method_meta.output_type.SerializeToString,
    )


class StreamMessage(Dict):
    _raw_data = None


def parse_request(parameters, request) -> Dict:
    request_dict = json_format.MessageToDict(request)
    args = {}
    for p in parameters:
        args[p] = request_dict.get(p)
    args['request'] = request
    return args


def _request_stream(request_iterator):
    for req in request_iterator:
        msg = StreamMessage(**json_format.MessageToDict(req))
        msg.raw_data = req
        yield msg


def parse_stream_request(request_iterator) -> Dict:
    return {
        "request": _request_stream(request_iterator)
    }


def parse_to_dict(input_type, item):
    return json_format.ParseDict(item, input_type()) if isinstance(item, dict) else item


def parse_stream_return(input_type, items):
    for item in items:
        yield parse_to_dict(input_type, item)


def warp_handler(method_meta: MethodMetaData, func):
    sig = signature(func)
    parameters = tuple(k for k, v in sig._parameters.items() if v.kind.value == 1)

    if method_meta.method_type.is_unary_request:
        argument_func = partial(parse_request, parameters)
    else:
        argument_func = parse_stream_request

    if method_meta.method_type.is_unary_response:
        return_func = partial(parse_to_dict, method_meta.output_type)
    else:
        return_func = partial(parse_stream_return, method_meta.output_type)

    def decorator(self, request, context):
        result = func(**argument_func(request), request=request, context=context)
        return return_func(result)

    return decorator
