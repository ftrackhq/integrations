# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack
import tempfile
from ftrack_connect_pipeline import plugin


class TestContext(plugin.ContextPlugin):
    plugin_name = 'test'

    def run(self, context=None, data=None, options=None):
        return options


class TestCollector(plugin.CollectorPlugin):
    plugin_name = 'test'

    def run(self, context=None, data=None, options=None):
        return [True]


class TestValidator(plugin.ValidatorPlugin):
    plugin_name = 'test'

    def run(self, context=None, data=None, options=None):
        return True


class TestOutput(plugin.OutputPlugin):
    plugin_name = 'test'

    def run(self, context=None, data=None, options=None):
        tmp = tempfile.NamedTemporaryFile().name
        return {'test': tmp}


class TestFinaliser(plugin.FinaliserPlugin):
    plugin_name = 'test'

    def run(self, context=None, data=None, options=None):
        tmp = tempfile.NamedTemporaryFile().name
        return {}


def register(api_object, **kw):

    plugins = [
        TestContext,
        TestCollector,
        TestValidator,
        TestOutput,
        TestFinaliser
    ]

    for plugin in plugins:
        plugin(api_object).register()
