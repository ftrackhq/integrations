# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_{{cookiecutter.host_type}}.plugin import (
    {{cookiecutter.host_type|capitalize}}BasePlugin,
    {{cookiecutter.host_type|capitalize}}BasePluginWidget,
)


class {{cookiecutter.host_type|capitalize}}PublisherValidatorPlugin(
    plugin.PublisherValidatorPlugin, {{cookiecutter.host_type|capitalize}}BasePlugin
):
    '''Class representing a Validator Plugin

    .. note::

        _required_output a Boolean
    '''


class {{cookiecutter.host_type|capitalize}}PublisherValidatorPluginWidget(
    pluginWidget.PublisherValidatorPluginWidget, {{cookiecutter.host_type|capitalize}}BasePluginWidget
):
    '''Class representing a Validator widget

    .. note::

        _required_output a Boolean
    '''
