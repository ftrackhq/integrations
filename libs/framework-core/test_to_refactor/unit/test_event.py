import pytest
import ftrack_constants.framework as constants
from ftrack_framework_core import event


@pytest.mark.parametrize(
    'manager_mode',
    [constants.LOCAL_EVENT_MODE, constants.REMOTE_EVENT_MODE],
    ids=['local mode', 'remote mode'],
)
def test_event_manager_initialise(session, test_event, manager_mode):
    def event_data(event):
        return {'test': 'data'}

    def callback(event):
        assert event['data'] == {'test': 'data'}

    event_manager = event.EventManager(session, mode=manager_mode)
    assert event_manager.connected
    event_manager.subscribe(test_event['topic'], event_data)
    event_manager.publish(test_event, callback)


@pytest.mark.parametrize(
    'manager_modes',
    [
        (constants.LOCAL_EVENT_MODE, constants.REMOTE_EVENT_MODE),
        (constants.REMOTE_EVENT_MODE, constants.LOCAL_EVENT_MODE),
        (constants.LOCAL_EVENT_MODE, constants.LOCAL_EVENT_MODE),
        (constants.REMOTE_EVENT_MODE, constants.REMOTE_EVENT_MODE),
    ],
    ids=[
        'remote override on local mode',
        'local override on remote mode',
        'local override on local mode',
        'remote override on remote mode',
    ],
)
def test_event_manager_publish_mode_overrides(
    session, test_event, manager_modes
):
    manager_mode, mode_override = manager_modes

    def event_data(event):
        return {'test': 'data'}

    def callback(event):
        assert event['data'] == {'test': 'data'}

    event_manager = event.EventManager(session, mode=manager_mode)
    assert event_manager.connected
    event_manager.subscribe(test_event['topic'], event_data)
    event_manager.publish(test_event, callback, mode=mode_override)
