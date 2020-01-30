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
from ftrack_connect_pipeline.definition import collect_and_validate


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
        os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                '..',
                'fixtures',
                'resource',
                'application_hook'
            )
        )
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
def new_project(request, session):
    project_schema = session.query('ProjectSchema').first()
    default_shot_status = project_schema.get_statuses('Shot')[0]
    default_task_type = project_schema.get_types('Task')[0]
    default_task_status = project_schema.get_statuses(
        'Task', default_task_type['id']
    )[0]


    project_name = 'pipeline_test_{0}'.format(uuid.uuid1().hex)
    project = session.create('Project', {
        'name': project_name,
        'full_name': project_name + '_full',
        'project_schema': project_schema
    })

    for sequence_number in range(1):
        sequence = session.create('Sequence', {
            'name': 'sequence_{0:03d}'.format(sequence_number),
            'parent': project
        })

        for shot_number in range(1):
            shot = session.create('Shot', {
                'name': 'shot_{0:03d}'.format(shot_number * 10),
                'parent': sequence,
                'status': default_shot_status
            })

            for task_number in range(1):
                task = session.create('Task', {
                    'name': 'task_{0:03d}'.format(task_number),
                    'parent': shot,
                    'status': default_task_status,
                    'type': default_task_type
                })

    session.commit()

    def cleanup():
        '''Remove created entity.'''
        session.delete(project)
        session.commit()

    request.addfinalizer(cleanup)

    return project


@pytest.fixture()
def host(request, event_manager):
    host_result = test_host.Host(event_manager)

    def cleanup():
        host_result.reset()

    request.addfinalizer(cleanup)
    return host_result


@pytest.fixture()
def event_manager(session):
    event_manager = event.EventManager(
        session, mode=constants.LOCAL_EVENT_MODE
    )

    def register_definitions(session, event):
        host = event['data']['pipeline']['host']

        dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                '..',
                'fixtures',
                'definitions'
            )
        )

        print dir
        # collect definitions
        data = collect_and_validate(
            session, dir, host
        )
        return data

    callback = functools.partial(register_definitions, event_manager.session)

    event_manager.subscribe(
        '{} and data.pipeline.type=definition'.format(
            constants.PIPELINE_REGISTER_TOPIC
        ),
        callback
    )

    return event_manager
