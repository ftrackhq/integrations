import functools
from ftrack_connect_pipeline import host
from ftrack_connect_pipeline import constants


def test_initialise_host(event_manager):
    # init host
    host_result = host.Host(event_manager)
    assert host_result.hostid
    assert host_result.host == [constants.HOST]


def test_initialise_multiple_host(event_manager):
    # init host
    host_result = host.Host(event_manager, host=['test'])
    assert host_result.hostid
    assert host_result.host == [constants.HOST, 'test']


def test_register_definitions(event_manager):

    def register_definitions(session, event):
        host = event['data']['pipeline']['host']
        assert host == constants.HOST

        data = {
            'schemas': [],
            'publishers': [],
            'loaders': [],
            'packages': []
        }
        return data

    callback = functools.partial(register_definitions, event_manager.session)

    event_manager.subscribe(
        '{} and data.pipeline.type=definition'.format(
            constants.PIPELINE_REGISTER_TOPIC
        ),
        callback
    )

    host.Host(event_manager)

