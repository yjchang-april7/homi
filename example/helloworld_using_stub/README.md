## Retrun Dict example

```python
from .helloworld_pb2 import _GREETER,HelloReply
from homi import App

app = App(
    services=[
        _GREETER,
    ]
)
service_name = 'helloworld.Greeter'


# unary-unary method
@app.method(service_name)
def SayHello(name, **kwargs):
    print(f"{name} is request SayHello")
    return HelloReply(message=f"Hello {name}!")


# unary-stream method
@app.method(service_name)
def SayHelloGroup(name, **kwargs):
    print(f"{name} is request SayHelloGroup")
    names = ['a', 'b', 'c', 'd']
    for name in names:
        yield HelloReply(message=f"Hello {name}!")


# stream-unary method
@app.method(service_name)
def HelloEveryone(request_iterator, context):
    names = []
    for reqs in request_iterator:
        print('you can get raw request', reqs.raw_data)
        names.append(reqs['name'])
    return HelloReply(message=f"Hello everyone {names}!")


# stream-stream method
@app.method(service_name)
def SayHelloOneByOne(request_iterator, context):
    for req in request_iterator:
        name = req['name']
        print(f"{name} say to you hello")
        yield HelloReply(message=f"Hello {name}!")

```