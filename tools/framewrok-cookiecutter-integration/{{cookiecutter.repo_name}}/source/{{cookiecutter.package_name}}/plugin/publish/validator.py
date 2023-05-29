# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from {{cookiecutter.package_name}}.plugin import (
    {{cookiecutter.host_type_capitalized}}BasePlugin,
    {{cookiecutter.host_type_capitalized}}BasePluginWidget,
)


class {{cookiecutter.host_type_capitalized}}PublisherValidatorPlugin(
    plugin.PublisherValidatorPlugin, {{cookiecutter.host_type_capitalized}}BasePlugin
):
    '''Class representing a Validator Plugin

    .. note::

        _required_output a Boolean
    '''


class {{cookiecutter.host_type_capitalized}}PublisherValidatorPluginWidget(
    pluginWidget.PublisherValidatorPluginWidget, {{cookiecutter.host_type_capitalized}}BasePluginWidget
):
    '''Class representing a Validator widget

    .. note::

        _required_output a Boolean
    '''
