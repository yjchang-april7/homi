from homi import App, Server
from homi.extend.service import reflection_service, health_service

from helloworld_pb2 import _GREETER

app = App(
    services=[
        _GREETER,
        reflection_service,
        health_service,
    ]
)
service_name = 'helloworld.Greeter'


# unary-unary method
@app.method(service_name)
def SayHello(name, **kwargs):
    print(f"{name} is request SayHello")
    return {"message": f"Hello {name}!"}


# unary-stream method
@app.method(service_name)
def SayHelloGroup(name, **kwargs):
    print(f"{name} is request SayHelloGroup")
    names = ['a', 'b', 'c', 'd']
    for name in names:
        yield {"message": f"Hello {name}!"}


# stream-unary method
@app.method(service_name)
def HelloEveryone(request_iterator, **kwargs):
    names = []
    for reqs in request_iterator:
        print('you can get raw request', reqs.raw_data)
        names.append(reqs['name'])
    return {"message": f"Hello everyone {names}!"}


# stream-stream method
@app.method(service_name, 'SayHelloOneByOne')
def one_by_one(request_iterator, **kwargs):
    for req in request_iterator:
        name = req['name']
        print(f"{name} say to you hello")
        yield {'message': f"Hello {name}!"}


if __name__ == '__main__':
    server = Server(app)
    server.run()
