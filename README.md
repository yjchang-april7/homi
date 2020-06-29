# homi
micro grpc framework like flask

## install
```shell script
pip install homi
```

## Feature
- [x] config less to run server
- [x] use decorator pattern to connect service method
- [x] auto parse request data to dict, you don't use grpc request object
- [x] auto set argument what you want
- [x] support all grpc service type(unary-unary,unary-stream,stream-unary,stream-stream)
- [ ] you just return dict type, not grpc object


## Example
check more [example](https://github.com/spaceone-dev/homi/tree/master/example)

```python
import homi

import helloworld_pb2
import helloworld_pb2_grpc


@homi.register(helloworld_pb2_grpc, 'Greeter',method='SayHello')
def hello(request,context):
    print(f"{request.name} is request SayHello")
    return helloworld_pb2.HelloReply(message=f"Hello {request.name}!")

# or you can do just like this! It's easy!!

@homi.register(helloworld_pb2_grpc, 'Greeter') # auto find same method name
def SayHello(name,**kwargs): # auto deserialize request to dict
    print(f"{name} is request SayHello")
    return {"message":f"Hello {name}!"} # auto serialize dict to response

```

## run server
```shell script
# if app file name is app.py
homi run

# run ohter app file
homi run other_app.py

# change port
homi run -p 50055

# change total worker
homi run -w 5
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
  

