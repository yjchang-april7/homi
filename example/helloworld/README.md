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
import homi

import helloworld_pb2
import helloworld_pb2_grpc

@homi.register(helloworld_pb2_grpc, 'Greeter')
def SayHello(name, **kwargs):
    print(f"{name} is request SayHello")
    return helloworld_pb2.HelloReply(message=f"Hello {name}!")

```

4. run server
```shell script
homi run
```

5. use it!
```shell script
# show all service
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