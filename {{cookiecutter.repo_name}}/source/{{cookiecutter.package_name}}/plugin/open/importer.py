# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

import {{cookiecutter.host_type}}

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_{{cookiecutter.host_type}}.plugin import (
    {{cookiecutter.host_type|capitalize}}BasePlugin,
    {{cookiecutter.host_type|capitalize}}BasePluginWidget,
)

from ftrack_connect_pipeline_{{cookiecutter.host_type}}.utils import custom_commands as {{cookiecutter.host_type}}_utils
from ftrack_connect_pipeline_{{cookiecutter.host_type}}.constants.asset import modes as load_const
from ftrack_connect_pipeline_{{cookiecutter.host_type}}.constants import asset as asset_const


class {{cookiecutter.host_type|capitalize}}OpenerImporterPlugin(plugin.OpenerImporterPlugin, {{cookiecutter.host_type|capitalize}}BasePlugin):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''

    load_modes = {
        load_const.OPEN_MODE: load_const.LOAD_MODES[load_const.OPEN_MODE]
    }

    dependency_load_mode = load_const.OPEN_MODE

    @{{cookiecutter.host_type}}_utils.run_in_main_thread
    def get_current_objects(self):
        return {{cookiecutter.host_type}}_utils.get_current_scene_objects()


class {{cookiecutter.host_type|capitalize}}OpenerImporterPluginWidget(
    pluginWidget.OpenerImporterPluginWidget, {{cookiecutter.host_type|capitalize}}BasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
