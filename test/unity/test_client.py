from ftrack_connect_pipeline import client
from ftrack_connect_pipeline import constants


def test_initialise(event_manager):
    client_connection = client.Client(event_manager)
    assert client_connection.ui == [constants.UI]


def test_initialise_mutiple_ui(event_manager):
    client_connection = client.Client(event_manager, ui=['test'])
    assert client_connection.ui == [constants.UI, 'test']
