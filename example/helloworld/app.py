import homi

import helloworld_pb2
import helloworld_pb2_grpc


@homi.register(helloworld_pb2_grpc, 'Greeter')
def SayHello(name, **kwargs):
    print(f"{name} is request SayHello")
    return helloworld_pb2.HelloReply(message=f"Hello {name}!")


@homi.register(helloworld_pb2_grpc, 'Greeter')
def HelloEveryone(request_iterator, context):
    names = []
    for reqs in request_iterator:
        print('you can get raw request', reqs.raw_data)
        names.append(reqs['name'])
    return helloworld_pb2.HelloReply(message=f"Hello everyone {names}!")
