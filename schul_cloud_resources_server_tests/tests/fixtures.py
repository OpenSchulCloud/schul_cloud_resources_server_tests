import pytest
import time
import schul_cloud_resources_api_v1.auth as auth
from schul_cloud_resources_server_tests.app import data, app
from schul_cloud_resources_api_v1 import ApiClient, ResourceApi
from bottle import ServerAdapter
from threading import Thread


class StoppableWSGIRefServerAdapter(ServerAdapter):
    """A bottle adapter for tests which is stoppable.

    copied from bottle
    """

    def run(self, app):
        from wsgiref.simple_server import WSGIRequestHandler, WSGIServer
        from wsgiref.simple_server import make_server
        import socket

        class FixedHandler(WSGIRequestHandler):
            def address_string(self): # Prevent reverse DNS lookups please.
                return self.client_address[0]
            def log_request(*args, **kw):
                if not self.quiet:
                    return WSGIRequestHandler.log_request(*args, **kw)

        handler_cls = self.options.get('handler_class', FixedHandler)
        server_cls  = self.options.get('server_class', WSGIServer)

        if ':' in self.host: # Fix wsgiref for IPv6 addresses.
            if getattr(server_cls, 'address_family') == socket.AF_INET:
                class server_cls(server_cls):
                    address_family = socket.AF_INET6

        self.srv = make_server(self.host, self.port, app, server_cls, handler_cls)
        self.srv.serve_forever()
        while not self.get_port(): time.sleep(0.001)

    def shutdown(self, blocking=True):
        """Stop the server.
        
        If blocking is True, this returns when the server is shut down.
        If blocking is False, the server is notified to shut down.
        """
        thread=Thread(target=self.srv.shutdown)
        thread.start()
        if blocking:
            thread.join()

    def get_port(self):
        """Return the port of the server."""
        try:
            return self.srv.socket.getsockname()[1]
        except AttributeError:
            return None


class ParallelBottleServer(object):
    """A server that runs bottle in parallel"""

    url_prefix = ""

    def __init__(self, app, host="127.0.0.1", port=0):
        """Start the server with a bottle app."""
        self._server = StoppableWSGIRefServerAdapter(host=host, port=port)
        self._thread = Thread(target=app.run, kwargs=dict(server=self._server))
        self._thread.start()
        while not self._server.get_port(): time.sleep(0.0001)

    @property
    def url(self):
        return "http://localhost:{}{}".format(self._server.get_port(), self.url_prefix)

    def shutdown(self):
        """Shut down the server."""
        self._server.shutdown()
        self._thread.join()



class ResourcesApiTestServer(ParallelBottleServer):
    """Interface to get the objects."""

    url_prefix = "/v1"

    def __init__(self):
        """Create a new server serving the resources api."""
        ParallelBottleServer.__init__(self, app)

    def get_resources(self):
        """Return all currently saved resources."""
        return data.get_resources()

    def delete_resources(self):
        """Clean up all resources."""
        data.delete_resources()

    @property
    def api(self):
        """An resources api client connected to the server."""
        auth.none()
        client = ApiClient(self.url)
        return ResourceApi(client)


@pytest.fixture(scope="session")
def session_resources_server():
    """Return the server to store resources."""
    session_resources_server = ResourcesApiTestServer()
    yield session_resources_server
    session_resources_server.shutdown()


@pytest.fixture
def resources_server(session_resources_server):
    """Return a fresh server object with no resources."""
    session_resources_server.delete_resources()
    yield session_resources_server
    session_resources_server.delete_resources()


__all__  = ["StoppableWSGIRefServerAdapter", "ParallelBottleServer", "ResourcesApiTestServer",
            "session_resources_server", "resources_server"]
