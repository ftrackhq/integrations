# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from {{cookiecutter.package_name}}.plugin import (
    {{cookiecutter.host_type_capitalized}}BasePlugin,
    {{cookiecutter.host_type_capitalized}}BasePluginWidget,
)


class {{cookiecutter.host_type_capitalized}}OpenerPostImporterPlugin(
    plugin.OpenerPostImporterPlugin, {{cookiecutter.host_type_capitalized}}BasePlugin
):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''


class {{cookiecutter.host_type_capitalized}}OpenerPostImporterPluginWidget(
    pluginWidget.OpenerPostImporterPluginWidget, {{cookiecutter.host_type_capitalized}}BasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
