# homi
micro grpc framework like flask

## Feature
- [x] config less to run server
- [x] use decorator pattern to connect service method
- [x] auto parse request data to dict, you don't use grpc request object
- [x] auto set argument what you want
- [x] support all grpc service type(unary-unary,unary-stream,stream-unary,stream-stream)
- [ ] you just return dict type, not grpc object


## Example
check [example](/example)

```python
import homi

import helloworld_pb2
import helloworld_pb2_grpc


@homi.register(helloworld_pb2_grpc, 'Greeter')
def SayHello(name, **kwargs):
    print(f"{name} is request SayHello")
    return helloworld_pb2.HelloReply(message=f"Hello {name}!")
```

## Change Logs
- 0.0.1 (init project)
    - run server using cli
    - helloworld example
- 0.0.3
    - support all method type
    - add flak8 lint
    - add test case
    - \#9 auto parse response message
  

