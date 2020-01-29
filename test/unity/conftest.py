import os
import tempfile
import pytest
import shutil
import uuid
import ftrack_api

from ftrack_connect_pipeline import event
from ftrack_connect_pipeline import constants


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
