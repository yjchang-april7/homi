from .helloworld_pb2 import _GREETER
from ...homi import App

app = App(
    services=[
        _GREETER,
    ]
)
service_name = 'helloworld.Greeter'


# unary-unary method
@app.method(service_name)
def SayHello(name, **kwargs):
    return {"message": f"Hello {name}!"}


# unary-stream method
@app.method(service_name)
def SayHelloGroup(name, **kwargs):
    names = ['a', 'b', 'c', 'd']
    for name in names:
        yield {"message": f"Hello {name}!"}


# stream-unary method
@app.method(service_name)
def HelloEveryone(request_iterator, context):
    names = []
    for reqs in request_iterator:
        names.append(reqs['name'])
    return {"message": f"Hello everyone {names}!"}


# stream-stream method
@app.method(service_name)
def SayHelloOneByOne(request_iterator, context):
    for req in request_iterator:
        yield {"message": f"Hello {req['name']}!"}
