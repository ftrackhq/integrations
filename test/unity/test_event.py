import pytest
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import event


def test_event_manager_initalise_local(session, new_event):

    def callback(event):
        assert event

    event_manager = event.EventManager(
        session, mode=constants.LOCAL_EVENT_MODE
    )
    event_manager.publish(new_event, callback)
    assert event_manager


def test_event_manager_initalise_local_override(session, new_event):

    def callback(event):
        assert event

    event_manager = event.EventManager(
        session, mode=constants.LOCAL_EVENT_MODE
    )
    event_manager.publish(new_event, callback, mode=constants.REMOTE_EVENT_MODE)
    assert event_manager
