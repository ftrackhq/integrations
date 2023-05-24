import functools
from ftrack_framework_core import client
from ftrack_framework_core import constants


def test_initialise(event_manager):
    client_connection = client.Client(event_manager)
    assert client_connection.ui_types == [constants.UI_TYPE]


def test_discover_host(host, event_manager):
    client_connection = client.Client(event_manager)
    client_connection.discover_hosts()
    assert len(client_connection.hosts) >= 1


def test_discover_host_callback(host, event_manager):
    def callback(hosts):
        assert len(hosts) == 1

    client_connection = client.Client(event_manager)
    client_connection.on_ready(callback)
    assert client_connection.host_connections
