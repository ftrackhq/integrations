# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from {{cookiecutter.package_name}}.plugin import (
    {{cookiecutter.host_type_capitalized}}BasePlugin,
    {{cookiecutter.host_type_capitalized}}BasePluginWidget,
)


class {{cookiecutter.host_type_capitalized}}LoaderContextPlugin(plugin.LoaderContextPlugin, {{cookiecutter.host_type_capitalized}}BasePlugin):
    '''Class representing a Context Plugin
    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'comment' and 'status_id' of the current asset
    '''


class {{cookiecutter.host_type_capitalized}}LoaderContextPluginWidget(
    pluginWidget.LoaderContextPluginWidget, {{cookiecutter.host_type_capitalized}}BasePluginWidget
):
    '''Class representing a Context Widget
    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'comment' and 'status_id' of the current asset
    '''
