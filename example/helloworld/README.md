## Install Homi
```shell script
pip install homi
# if you want generate other proto file
pip install grpc_tools

# if you want request to server
brew install grpcurl
```

## Tutorial
1. write proto file(helloworld.proto)
```proto
syntax = "proto3";

package helloworld;

// Service Definition
service Greeter {
  rpc SayHello (HelloRequest) returns (HelloReply) {}
  rpc SayHelloGroup (HelloRequest) returns (stream HelloReply) {}
  rpc HelloEveryone(stream HelloRequest) returns (HelloReply) {}
  rpc SayHelloOneByOne(stream HelloRequest) returns (stream HelloReply) {}
}

// Message Definition
message HelloRequest {
  string name = 1;
}

message HelloReply {
  string message = 1;
}
```

2. generated Python Stub
```shell script
python -m grpc_tools.protoc -I. --python_out=.  --grpc_python_out=. helloworld.proto
```

3. make app.py file
```python
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
service_name = _GREETER.full_name # 'helloworld.Greeter'


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
app.add_service()

# stream-unary method
@app.method(service_name)
def HelloEveryone(request_iterator, **kwargs):
    names = []
    for reqs in request_iterator:
        print('you can get raw request', reqs.raw_data)
        names.append(reqs['name'])
    return {"message": f"Hello everyone {names}!"}


# stream-stream method
@app.method(service_name, 'SayHelloOneByOne') # you can change func name
def one_by_one(request_iterator, **kwargs):
    for req in request_iterator:
        name = req['name']
        print(f"{name} say to you hello")
        yield {'message': f"Hello {name}!"}

if __name__ == '__main__':
    server = Server(app)
    server.run()
```

4. run server
```shell script
homi run
```

5. use it!
```shell script
# show all extend
grpcurl -plaintext localhost:50051 list
# print like this
# grpc.reflection.v1alpha.ServerReflection
# helloworld.Greeter

# get server info
grpcurl -plaintext  localhost:50051 describe


# request hello
grpcurl -plaintext -d '{"name":"woni"}'  localhost:50051 helloworld.Greeter/SayHello

# result is look like this
# {
#  "message": "Hello woni!"
# }
```

6. all test server
```shell script
python -m unittest
```