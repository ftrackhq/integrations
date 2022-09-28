# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from {{cookiecutter.package_name}}.plugin import (
    {{cookiecutter.host_type_capitalized}}BasePlugin,
    {{cookiecutter.host_type_capitalized}}BasePluginWidget,
)


class {{cookiecutter.host_type_capitalized}}OpenerPreFinalizerPlugin(
    plugin.OpenerPreFinalizerPlugin, {{cookiecutter.host_type_capitalized}}BasePlugin
):
    '''Class representing a Pre Finalizer Plugin

    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
        current asset
    '''


class {{cookiecutter.host_type_capitalized}}OpenerPreFinalizerPluginWidget(
    pluginWidget.OpenerPreFinalizerPluginWidget, {{cookiecutter.host_type_capitalized}}BasePluginWidget
):
    '''Class representing a Pre Finalizer Widget

    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
        current asset
    '''
