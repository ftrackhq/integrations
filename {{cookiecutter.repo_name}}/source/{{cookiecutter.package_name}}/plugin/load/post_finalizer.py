# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_{{cookiecutter.host_type}}.plugin import (
    {{cookiecutter.host_type|capitalize}}BasePlugin,
    {{cookiecutter.host_type|capitalize}}BasePluginWidget,
)


class {{cookiecutter.host_type|capitalize}}LoaderPostFinalizerPlugin(
    plugin.LoaderPostFinalizerPlugin, {{cookiecutter.host_type|capitalize}}BasePlugin
):
    '''Class representing a Post Finalizer Plugin

    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
        current asset
    '''


class {{cookiecutter.host_type|capitalize}}LoaderPostFinalizerPluginWidget(
    pluginWidget.LoaderPostFinalizerPluginWidget, {{cookiecutter.host_type|capitalize}}BasePluginWidget
):
    '''Class representing a Post Finalizer Widget

    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
        current asset
    '''
