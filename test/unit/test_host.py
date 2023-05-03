import functools
from ftrack_connect_pipeline import host
from ftrack_connect_pipeline import constants


def test_initialise_host(event_manager):
    # init host
    host_result = host.Host(event_manager)
    assert host_result.host_id
    assert host_result.host_types == [constants.HOST_TYPE]
