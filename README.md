# homi
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/homi?style=flat-square)](https://pypi.org/project/homi)
[![PyPI](https://img.shields.io/pypi/v/homi?style=flat-square)](https://pypi.org/project/homi)
[![PyPI download month](https://img.shields.io/pypi/dm/homi?style=flat-square)](https://pypi.org/project/homi)
[![codecov](https://codecov.io/gh/spaceone-dev/homi/branch/master/graph/badge.svg)](https://codecov.io/gh/spaceone-dev/homi)
[![ViewCount](https://views.whatilearened.today/views/github/spaceone-dev/homi.svg?nocache=true)](https://github.com/wesky93/views)

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
from homi import App, Server
from homi.extend.service import reflection_service, health_service


from helloworld_pb2 import DESCRIPTOR

svc_desc = DESCRIPTOR.services_by_name['Greeter']

app = App(
    services=[
        svc_desc,
        reflection_service,
        health_service,
    ]
)

# unary-unary method
@app.method('helloworld.Greeter')
def SayHello(name, **kwargs):
    print(f"{name} is request SayHello")
    return {"message": f"Hello {name}!"}


# or 
@app.method('helloworld.Greeter','SayHello')
def hello(request,context):
    print(f"{request.name} is request SayHello")
    return {"message": f"Hello {request.name}!"}

# or
def hello_func(request,context):
    return {"message":"hi"}

app.register_method('helloworld.Greeter','SayHello',hello_func)

if __name__ == '__main__':
    server = Server(app)
    server.run()
```

## Service Example
The service class is similar to the blueprint of flask. You can separate files on a service basis or add services created by others.
Also, we will be able to override the method already registered in the future.

```python
from homi import App, Server,Service
from homi.extend.service import reflection_service, health_service

from helloworld_pb2 import DESCRIPTOR

app = App(services=[reflection_service,health_service,])

greeter = Service(DESCRIPTOR.services_by_name['Greeter'])

@greeter.method()
def SayHello(name, **kwargs):
    print(f"{name} is request SayHello")
    return {"message": f"Hello {name}!"}

# you can share service to pypi
app.add_service(greeter)
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


## Relation Project
- [grpc_requests](https://github.com/spaceone-dev/grpc_requests) : GRPC for Humans! python grpc reflection support client


## Change Logs

- 0.1.1
    - Fix Bugs
        - #23 : change support python version >= 3.8 (for TypedDict)
        - #22 : remove handler wrapper self arguments

- 0.1.0
    - Breaking Change!!! #19
        - Add App
            - now you must make server using App class!
        - Add Service
            - You can separate the code by service or method.
        - Add Config
            - now you can use service config and overwrite in app
 - 0.0.4.alpha
    - add real server testcase
    - support grpc-health
- 0.0.3
    - support all method type
    - add flak8 lint
    - add test case
    - \#9 auto parse response message
- 0.0.1 (init project)
    - run server using cli
    - helloworld example