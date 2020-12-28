import asyncio
import sys
from os.path import dirname

import click

from homi import AsyncServer
from . import AsyncApp
from .exception import ServerSSLConfigError


@click.group()
def cli():
    pass


@click.command("run", short_help="Run a development server.")
@click.argument('file', type=click.Path(exists=True, resolve_path=True), default="app.py")
@click.option("--host", "-h", help="The interface to bind to.")
@click.option("--port", "-p", default='50051', help="The port to bind to.")
@click.option('--worker', '-w', default=10, type=int)
@click.option('--use_uvloop', default=True, type=bool, help="If you don't want uvloop `--uvloop false`")
@click.option('--alts', type=bool, default=False, help='[Experimental] enable alts')
@click.option('--private_key', '-k', type=click.Path(exists=True, resolve_path=True), help='tls private key')
@click.option('--certificate', '-c', type=click.Path(exists=True, resolve_path=True), help='tls root certificate')
# @click.option(
#     "--reload/--no-reload",
#     default=None,
#     help="Enable or disable the reloader. By default the reloader "
#          "is active if debug is enabled.",
# )
@click.option(
    "--debug",
    default=False,
    type=bool,
    help="Server Debug Mode",
)
def run_command(file, port, worker, debug, alts, host=None, private_key=None, certificate=None, use_uvloop=True):
    sys.path.append(dirname(file))
    import importlib.util

    spec = importlib.util.spec_from_file_location("app", file)
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)

    from .server import Server
    if private_key and certificate:
        with open(private_key, 'rb') as f:
            private_key = f.read()
        with open(certificate, 'rb') as f:
            certificate = f.read()
    elif private_key or certificate:
        raise ServerSSLConfigError('if you want use tls mode, you must set both private_key & certificate value')
    if isinstance(app_module.app, AsyncApp):
        if use_uvloop:
            import uvloop
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        else:
            print('use asyncio loop (uvloop off)')
        server = AsyncServer(
            app_module.app,
            host, port,
            debug=debug,
            alts=alts,
            private_key=private_key,
            certificate=certificate
        )
        asyncio.run(server.run())
    else:
        Server(
            app_module.app,
            host, port, worker,
            debug=debug,
            alts=alts,
            private_key=private_key,
            certificate=certificate
        ).run()


cli.add_command(run_command)

if __name__ == '__main__':
    cli()
