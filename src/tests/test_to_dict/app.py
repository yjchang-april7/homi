from . import helloworld_pb2_grpc
from ... import homi


# unary-unary method
@homi.register(helloworld_pb2_grpc, 'Greeter')
def SayHello(name, **kwargs):
    return {"message": f"Hello {name}!"}


# unary-stream method
@homi.register(helloworld_pb2_grpc, 'Greeter')
def SayHelloGroup(name, **kwargs):
    names = ['a', 'b', 'c', 'd']
    for name in names:
        yield {"message": f"Hello {name}!"}


# stream-unary method
@homi.register(helloworld_pb2_grpc, 'Greeter')
def HelloEveryone(request_iterator, context):
    names = []
    for reqs in request_iterator:
        names.append(reqs['name'])
    return {"message": f"Hello everyone {names}!"}


# stream-stream method
@homi.register(helloworld_pb2_grpc, 'Greeter')
def SayHelloOneByOne(request_iterator, context):
    for req in request_iterator:
        yield {"message": f"Hello {req['name']}!"}
