import pytest
import time
import schul_cloud_ressources_api_v1.auth as auth
from schul_cloud_ressources_server_tests.app import data, app
from schul_cloud_ressources_api_v1 import ApiClient, RessourceApi
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

        self.srv = make_server(self.host, 0, app, server_cls, handler_cls)
        self.srv.serve_forever()
        while not self.get_port(): time.sleep(0.001)

    def shutdown(self):
        """Stop the server."""
        self.srv.shutdown()

    def get_port(self):
        """Return the port of the server."""
        try:
            return self.srv.socket.getsockname()[1]
        except AttributeError:
            return None


class ParallelBottleServer(object):
    """A server that runs bottle in parallel"""

    url_prefix = ""

    def __init__(self, app):
        """Start the server with a bottle app."""
        self._server = StoppableWSGIRefServerAdapter()
        self._thread = Thread(target=app.run, kwargs=dict(host="127.0.0.1", server=self._server))
        self._thread.start()
        while not self._server.get_port(): time.sleep(0.0001)

    @property
    def url(self):
        return "http://localhost:{}{}".format(self._server.get_port(), self.url_prefix)

    def shutdown(self):
        """Shut down the server."""
        self._server.shutdown()
        self._thread.join()



class RessourcesApiTestServer(ParallelBottleServer):
    """Interface to get the objects."""

    url_prefix = "/v1"

    def __init__(self):
        """Create a new server serving the ressources api."""
        ParallelBottleServer.__init__(self, app)

    def get_ressources(self):
        """Return all currently saved ressources."""
        return data.get_ressources()

    def delete_ressources(self):
        """Clean up all ressources."""
        data.delete_ressources()

    @property
    def api(self):
        """An ressources api client connected to the server."""
        auth.none()
        client = ApiClient(self.url)
        return RessourceApi(client)


@pytest.fixture(scope="session")
def session_ressources_server():
    """Return the server to store ressources."""
    session_ressources_server = RessourcesApiTestServer()
    yield session_ressources_server
    session_ressources_server.shutdown()


@pytest.fixture
def ressources_server(session_ressources_server):
    """Return a fresh server object with no ressources."""
    session_ressources_server.delete_ressources()
    yield session_ressources_server
    session_ressources_server.delete_ressources()


__all__  = ["StoppableWSGIRefServerAdapter", "ParallelBottleServer", "RessourcesApiTestServer",
            "session_ressources_server", "ressources_server"]