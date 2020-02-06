import functools
from ftrack_connect_pipeline import client
from ftrack_connect_pipeline import constants


def test_initialise(event_manager):
    client_connection = client.Client(event_manager)
    assert client_connection.ui == [constants.UI]


def test_discover_host(host, event_manager):

    client_connection = client.Client(event_manager)
    hosts = client_connection.discover_hosts()
    assert len(hosts) == 1


def test_discover_host_callback(host, event_manager):

    def callback(hosts):
        assert len(hosts) == 1

    client_connection = client.Client(event_manager)
    client_connection.on_ready(callback)
    assert client_connection.hosts


def test_run_host_callback(host, event_manager, temporary_image, new_project):

    def callback(hosts):
        host = hosts[0]
        assert host.state is False
        task = host.session.query(
            'select name from Task where project.name is "{}"'.format(
                new_project['name']
            )
        ).first()

        schema = new_project['project_schema']
        task_status = schema.get_statuses('Task')[0]

        publisher = host.definitions['publisher'][0]

        publisher['contexts']['plugins'][0]['options']['context_id'] = task['id']
        publisher['contexts']['plugins'][0]['options']['asset_name'] = 'PipelineAsset'
        publisher['contexts']['plugins'][0]['options']['comment'] = 'A new hope'
        publisher['contexts']['plugins'][0]['options']['status_id'] = task_status['id']
        publisher['components'][0]['stages'][0]['plugins'][0]['options']['path'] = temporary_image
        host.run(publisher)
        assert host.state is True

    client_connection = client.Client(event_manager)
    client_connection.on_ready(callback)


def test_run_host_fail_callback(host, event_manager, temporary_image, new_project):

    def callback(hosts):
        host = hosts[0]
        assert host.state is False
        publisher = host.definitions['publisher'][0]
        publisher['components'][0]['stages'][0]['plugins'][0]['options']['path'] = temporary_image
        host.run(publisher)
        assert host.state is False

    client_connection = client.Client(event_manager)
    client_connection.on_ready(callback)



