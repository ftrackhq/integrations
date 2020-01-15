import pytest
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import event


def test_event_manager_initalise_local(shared_session):
    event_manager = event.EventManager(
        shared_session, mode=constants.LOCAL_EVENT_MODE
    )

    assert event_manager

