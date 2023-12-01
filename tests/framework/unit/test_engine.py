# test_standard_engine.py
import sys
import os

ROOT_INTEGRATIONS_FOLDER = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
)

INCLUDE_PACKAGES = [
    'libs/constants',
    'libs/framework-core',
    'libs/framework-engine',
    'libs/framework-plugin',
    # QT
    'libs/framework-widget',
    'libs/framework-qt',
    'libs/qt',
    'libs/qt-style',
    'libs/utils',
]

for _package in INCLUDE_PACKAGES:
    sys.path.append(os.path.join(ROOT_INTEGRATIONS_FOLDER, _package, "source"))

from ftrack_framework_core import registry

import pytest


@pytest.fixture
def plugin_instance():
    from ftrack_framework_plugin import BasePlugin

    class TestPlugin(BasePlugin):
        name = 'test_plugin'

        def ui_hook(self, payload):
            return (payload, self.options)

        def run(self, store):
            store['test_data'] = self.options

    return TestPlugin


@pytest.fixture
def registry_instance(plugin_instance):
    registry_instance = registry.Registry()
    registry_instance.add(
        'plugin', 'test_plugin', plugin_instance, 'test/path.py'
    )
    return registry_instance


@pytest.fixture
def session_instance():
    import ftrack_api

    session = ftrack_api.Session(auto_connect_event_hub=False)
    # Create a mock for the session dependency
    return session


@pytest.fixture
def test_engine_instance(registry_instance, session_instance):
    from ftrack_framework_engine import BaseEngine

    class TestEngine(BaseEngine):
        name = 'test_engine'

        def get_store(self) -> dict:
            return dict()

    return TestEngine(
        plugin_registry=registry_instance, session=session_instance
    )


def test_run_ui_hook(test_engine_instance):
    plugin = "test_plugin"
    payload = {"data": "test_data"}
    options = {"option1": "value1", "option2": "value2"}
    reference = None
    result = test_engine_instance.run_ui_hook(
        plugin, payload, options, reference
    )
    assert result == (payload, options)


def test_run_plugin(test_engine_instance):
    # Test case for the run_plugin method
    plugin = "test_plugin"
    store = {}
    options = {"option1": "value1", "option2": "value2"}
    reference = None

    # Call the method and assert the expected behavior
    result = test_engine_instance.run_plugin(plugin, store, options, reference)
    assert result['plugin_store'] == {'test_data': options}


def test_execute_engine(test_engine_instance):
    # Test case for the execute_engine method
    engine = [
        {
            "type": "group",
            "reference": "1234",
            "plugins": [
                {"type": "plugin", "plugin": "test_plugin", "reference": "123"}
            ],
        }
    ]
    user_options = {"123": {"option1": "value1"}}

    # Call the method and assert the expected behavior
    result = test_engine_instance.execute_engine(engine, user_options)
    assert result == {'test_data': user_options['123']}
