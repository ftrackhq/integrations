import pytest
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import event


@pytest.mark.parametrize('manager_mode', [
    constants.LOCAL_EVENT_MODE,
    constants.REMOTE_EVENT_MODE
], ids=[
    'local mode',
    'remote mode'
])
def test_event_manager_initalise(session, new_event, manager_mode):

    def event_data(event):
        return {'test': 'data'}

    def callback(event):
        assert event['data'] == {'test': 'data'}

    event_manager = event.EventManager(
        session, mode=manager_mode
    )
    event_manager.subscribe('test-event', event_data)
    event_manager.publish(new_event, callback)


@pytest.mark.parametrize('manager_mode', [
    (constants.LOCAL_EVENT_MODE, constants.REMOTE_EVENT_MODE),
    (constants.REMOTE_EVENT_MODE, constants.LOCAL_EVENT_MODE)
], ids=[
    'remote override local mode',
    'local override remote mode'
])
def test_event_manager_initalise_overrides(session, new_event, manager_mode):
    mode, mode_override = manager_mode

    def event_data(event):
        return {'test': 'data'}

    def callback(event):
        assert event['data'] == {'test': 'data'}

    event_manager = event.EventManager(
        session, mode=mode
    )
    event_manager.subscribe('test-event', event_data)
    event_manager.publish(new_event, callback, mode=mode_override)
