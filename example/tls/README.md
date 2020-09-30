## TLS Server Example

### create key
```bash
openssl req -newkey rsa:2048 -nodes -keyout server.key -x509 -days 365 -out server.crt

# Common Name (eg, fully qualified host name) : localhost
```
### run server
```bash
homi run --private_key server.key --certificate server.crt
```