# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_{{cookiecutter.host_type}}.plugin import (
    {{cookiecutter.host_type|capitalize}}BasePlugin,
    {{cookiecutter.host_type|capitalize}}BasePluginWidget,
)


class {{cookiecutter.host_type|capitalize}}PublisherExporterPlugin(
    plugin.PublisherExporterPlugin, {{cookiecutter.host_type|capitalize}}BasePlugin
):
    '''Class representing an Exporter Plugin
    .. note::

        _required_output a Dictionary
    '''


class {{cookiecutter.host_type|capitalize}}PublisherExporterPluginWidget(
    pluginWidget.PublisherExporterPluginWidget, {{cookiecutter.host_type|capitalize}}BasePluginWidget
):
    '''Class representing an Eporter Widget
    .. note::

        _required_output a Dictionary
    '''
