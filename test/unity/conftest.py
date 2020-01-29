import os
import tempfile
import pytest
import shutil
import uuid
import ftrack_api
import json
import functools

from ftrack_connect_pipeline import event
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import host as test_host


def _temporary_file(request, **kwargs):
    '''Return temporary file.'''
    file_handle, path = tempfile.mkstemp(**kwargs)
    os.close(file_handle)

    def cleanup():
        '''Remove temporary file.'''
        try:
            os.remove(path)
        except OSError:
            pass

    request.addfinalizer(cleanup)
    return path


@pytest.fixture()
def temporary_file(request):
    '''Return temporary file.'''
    return _temporary_file(request)


@pytest.fixture()
def temporary_image(request):
    '''Return temporary file.'''
    return _temporary_file(request, suffix='.jpg')


@pytest.fixture()
def temporary_directory(request):
    '''Return temporary directory.'''
    path = tempfile.mkdtemp()

    def cleanup():
        '''Remove temporary directory.'''
        shutil.rmtree(path)

    request.addfinalizer(cleanup)

    return path


@pytest.fixture()
def unique_name():
    '''Return a unique name.'''
    return 'test-{0}'.format(uuid.uuid4())


@pytest.fixture()
def session():
    event_paths = [
        os.path.abspath(os.path.join(
            '..',
            'ftrack-connect-pipeline',
            'resource',
            'application_hook'))
    ]

    session = ftrack_api.Session(
        plugin_paths=event_paths,
        auto_connect_event_hub=False
    )

    return session


@pytest.fixture()
def test_event(unique_name):
    event = ftrack_api.event.base.Event(
        topic=unique_name
    )

    return event


@pytest.fixture()
def event_manager(session):
    event_manager = event.EventManager(
        session, mode=constants.LOCAL_EVENT_MODE
    )

    return event_manager


@pytest.fixture()
def host(request, event_manager):
    host_result = test_host.Host(event_manager)

    def cleanup():
        host_result.reset()

    request.addfinalizer(cleanup)
    return host_result


@pytest.fixture()
def definitions(event_manager):
    data_folder = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '..',
            'fixtures',
            'json_data'
        )
    )

    with open(os.path.join(data_folder, 'publisher_schema.json'), 'r') as datafile:
        publisher_schema = json.load(datafile)

    with open(os.path.join(data_folder, 'package_schema.json'), 'r') as datafile:
        package_schema = json.load(datafile)

    with open(os.path.join(data_folder, 'publisher.json'), 'r') as datafile:
        publisher = json.load(datafile)

    with open(os.path.join(data_folder, 'package.json'), 'r') as datafile:
        package = json.load(datafile)


    data = {
        'schemas': [publisher_schema, package_schema],
        'publishers': [publisher],
        'loaders': [],
        'packages': [package]
    }

    def register_definitions(session, event):
        host = event['data']['pipeline']['host']
        return data

    callback = functools.partial(register_definitions, event_manager.session)

    event_manager.subscribe(
        '{} and data.pipeline.type=definition'.format(
            constants.PIPELINE_REGISTER_TOPIC
        ),
        callback
    )

    return event_manager