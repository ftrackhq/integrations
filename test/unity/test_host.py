from ftrack_connect_pipeline import host


def test_initialise_host(event_manager):
    # init host
    host_result = host.Host(event_manager)
    assert host_result