from enum import Enum
from functools import partial
from inspect import signature
from typing import Any, Dict, NamedTuple, Tuple, TypeVar

import grpc
from google.protobuf import json_format, symbol_database
from google.protobuf.descriptor import MethodDescriptor, ServiceDescriptor
from google.protobuf.descriptor_pb2 import MethodDescriptorProto, ServiceDescriptorProto


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
    request_dict = json_format.MessageToDict(request, preserving_proto_field_name=True)
    args = {}
    for p in parameters:
        args[p] = request_dict.get(p)
    args['request'] = request
    return args


def parse_stream_request(request_iterator) -> Dict:
    for req in request_iterator:
        msg = StreamMessage(**json_format.MessageToDict(req, preserving_proto_field_name=True))
        msg.raw_data = req
        yield msg


async def parse_async_stream_request(request_iterator):
    async for req in request_iterator:
        msg = StreamMessage(**json_format.MessageToDict(req, preserving_proto_field_name=True))
        msg.raw_data = req
        yield msg


def parse_to_dict(input_type, item):
    return json_format.ParseDict(item, input_type()) if isinstance(item, dict) else item


def parse_stream_return(input_type, items):
    for item in items:
        yield parse_to_dict(input_type, item)


async def parse_async_stream_return(input_type, items):
    async for item in items:
        yield parse_to_dict(input_type, item)


def warp_handler(method_meta: MethodMetaData, func):
    sig = signature(func)
    parameters = tuple(k for k, v in sig._parameters.items() if v.kind.value == 1)

    if method_meta.method_type.is_unary_response:
        return_func = partial(parse_to_dict, method_meta.output_type)
    else:
        return_func = partial(parse_stream_return, method_meta.output_type)

    if method_meta.method_type.is_unary_request:
        request_parser = partial(parse_request, parameters)

        def wrapper(request, context):
            result = func(**request_parser(request), context=context)
            return return_func(result)
    else:
        def wrapper(request, context):
            result = func(parse_stream_request(request), context=context)
            return return_func(result)

    return wrapper


def warp_async_handler(method_meta: MethodMetaData, func):
    sig = signature(func)
    parameters = tuple(k for k, v in sig._parameters.items() if v.kind.value == 1)

    is_unary_response = method_meta.method_type.is_unary_response
    is_unary_request = method_meta.method_type.is_unary_request

    if is_unary_response:
        return_func = partial(parse_to_dict, method_meta.output_type)
    else:
        return_func = partial(parse_async_stream_return, method_meta.output_type)

    if is_unary_request:
        request_parser = partial(parse_request, parameters)
        if is_unary_response:
            async def wrapper(request, context):
                result = func(**request_parser(request), context=context)
                return return_func(await result)
        else:
            async def wrapper(request, context):
                result = func(**request_parser(request), context=context)
                async for msg in return_func(result):
                    yield msg

    else:
        if is_unary_response:
            async def wrapper(request, context):
                result = func(parse_async_stream_request(request), context=context)
                return return_func(await result)
        else:
            async def wrapper(request, context):
                result = func(parse_async_stream_request(request), context=context)
                async for msg in return_func(result):
                    yield msg

    return wrapper


def warp_handler_for_method(method_meta: MethodMetaData, func):
    handler = warp_handler(method_meta, func)

    def decorator(request, context):
        return handler(request, context)

    return decorator
