import functools
from ftrack_framework_core import host
from ftrack_framework_core import constants


def test_initialise_host(event_manager):
    # init host
    host_result = host.Host(event_manager)
    assert host_result.host_id
    assert host_result.host_types == [constants.HOST_TYPE]
