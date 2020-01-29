import functools
from ftrack_connect_pipeline import client
from ftrack_connect_pipeline import constants


def test_initialise(event_manager):
    client_connection = client.Client(event_manager)
    assert client_connection.ui == [constants.UI]


def test_initialise_mutiple_ui(event_manager):
    client_connection = client.Client(event_manager, ui=['test'])
    assert client_connection.ui == [constants.UI, 'test']


def test_discover_host(event_manager, host, definitions):

    client_connection = client.Client(event_manager)
    hosts = client_connection.discover_hosts(time_out=10)
    assert client_connection.hosts

    assert len(hosts) >= 1


def test_discover_host_callback(event_manager, host, definitions):

    def callback(hosts):
        print 'hosts', hosts
        assert len(hosts) >= 3

    client_connection = client.Client(event_manager)
    client_connection.on_ready(callback, time_out=10)
    assert client_connection.hosts

