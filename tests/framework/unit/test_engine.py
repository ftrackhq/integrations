# test_standard_engine.py
import pytest
from ftrack_framework_core import registry


@pytest.fixture
def plugin_instance():
    '''Return a TestPlugin instance.'''
    from ftrack_framework_core.plugin import BasePlugin

    class TestPlugin(BasePlugin):
        name = 'test_plugin'

        def ui_hook(self, payload):
            '''Return payload and options.'''
            return (payload, self.options)

        def run(self, store):
            '''Set test_data in store.'''
            store['test_data'] = self.options

    return TestPlugin


@pytest.fixture
def registry_instance(plugin_instance):
    '''Return a registry instance with test_plugin added.'''
    registry_instance = registry.Registry()
    registry_instance.add(
        'plugin', 'test_plugin', plugin_instance, 'test/path.py'
    )
    return registry_instance


@pytest.fixture
def session_instance(mocker):
    '''Return a mocked session instance with auto_connect_event_hub set to False.'''
    import ftrack_api

    # Create a mock for the session dependency
    session = mocker.Mock(spec=ftrack_api.Session)
    session.auto_connect_event_hub = False
    return session


@pytest.fixture
def test_engine_instance(registry_instance, session_instance):
    '''Return a TestEngine instance with plugin_registry and session set.'''
    from ftrack_framework_core.engine import BaseEngine

    class TestEngine(BaseEngine):
        name = 'test_engine'

        def get_store(self) -> dict:
            '''Return an empty dictionary.'''
            return dict()

    return TestEngine(
        plugin_registry=registry_instance, session=session_instance
    )


def test_run_ui_hook(test_engine_instance):
    '''Test run_ui_hook method.'''
    plugin = "test_plugin"
    payload = {"data": "test_data"}
    options = {"option1": "value1", "option2": "value2"}
    reference = None
    result = test_engine_instance.run_ui_hook(
        plugin, payload, options, reference
    )
    assert result == (payload, options)


def test_run_plugin(test_engine_instance):
    '''Test run_plugin method.'''
    # Test case for the run_plugin method
    plugin = "test_plugin"
    store = {}
    options = {"option1": "value1", "option2": "value2"}
    reference = None

    # Call the method and assert the expected behavior
    result = test_engine_instance.run_plugin(plugin, store, options, reference)
    assert result['plugin_store'] == {'test_data': options}


@pytest.mark.parametrize(
    "engine, user_options, expected_result",
    [
        (
            [
                {
                    "type": "group",
                    "reference": "1234",
                    "plugins": [
                        {
                            "type": "plugin",
                            "plugin": "test_plugin",
                            "reference": "123",
                        }
                    ],
                }
            ],
            {"123": {"option1": "value1"}},
            {'test_data': {"option1": "value1"}},
        ),
        (
            [{"type": "plugin", "plugin": "test_plugin", "reference": "123"}],
            {"123": {"option1": "value1"}},
            {'test_data': {"option1": "value1"}},
        ),
    ],
)
def test_execute_engine(
    test_engine_instance, engine, user_options, expected_result
):
    '''Test execute_engine method.'''
    # Call the method and assert the expected behavior
    result = test_engine_instance.execute_engine(engine, user_options)
    assert result == expected_result
