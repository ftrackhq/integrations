# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from {{cookiecutter.package_name}}.plugin import (
    {{cookiecutter.host_type_capitalized}}BasePlugin,
    {{cookiecutter.host_type_capitalized}}BasePluginWidget,
)

from {{cookiecutter.package_name}}.utils import custom_commands as {{cookiecutter.host_type}}_utils
from {{cookiecutter.package_name}}.constants.asset import modes as load_const
from {{cookiecutter.package_name}}.constants import asset as asset_const


class {{cookiecutter.host_type_capitalized}}LoaderImporterPlugin(plugin.LoaderImporterPlugin, {{cookiecutter.host_type_capitalized}}BasePlugin):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''

    load_modes = load_const.LOAD_MODES

    dependency_load_mode = load_const.REFERENCE_MODE

    @{{cookiecutter.host_type}}_utils.run_in_main_thread
    def get_current_objects(self):
        return {{cookiecutter.host_type}}_utils.get_current_scene_objects()


class {{cookiecutter.host_type_capitalized}}LoaderImporterPluginWidget(
    pluginWidget.LoaderImporterPluginWidget, {{cookiecutter.host_type_capitalized}}BasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
