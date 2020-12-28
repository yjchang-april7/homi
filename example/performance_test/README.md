## Performance Test App
test using [ghz](https://github.com/bojand/ghz)

```shell script
# sync server
homi run app.py -w 100
ghz --insecure --proto=helloworld.proto -n 200 --call=helloworld.Greeter.SayHello -d '{"name":"test"}' localhost:50051

homi run app.py -w 200
ghz --insecure --proto=helloworld.proto -n 200 --call=helloworld.Greeter.SayHello -d '{"name":"test"}' localhost:50051



# async server(use uvloop default)
homi run async_app.py 
ghz --insecure --proto=helloworld.proto -n 200 --call=helloworld.Greeter.SayHello -d '{"name":"test"}' localhost:50051

# async server(no uvloop)
homi run async_app.py --use_uvloop=false
ghz --insecure --proto=helloworld.proto -n 200 --call=helloworld.Greeter.SayHello -d '{"name":"test"}' localhost:50051

```

# Result
|               | sync(worker 100) | sync(worker 200) | async     | async(no uvloop) |
|---------------|------------------|------------------|-----------|------------------|
| total request | 200              | 200              | 200       | 200              |
| OK            | 200              | 200              | 200       | 200              |
| Unavailable   | 0                | 0                | 0         | 0                |
| Total         | 4.64 s           | 4.28 s           | 3.89 s    | 3.71 s           |
| Slowest       | 1.85 s           | 1.55 s           | 1.35 s    | 1.09 s           |
| Fastest       | 796.75 ms        | 765.64 ms        | 799.23 ms | 808.19 ms        |
| Average       | 945.88 ms        | 937.54 ms        | 876.36 ms | 867.81 ms        |
| Requests/sec  | 43.07            | 46.74            | 51.40     | 53.86            |