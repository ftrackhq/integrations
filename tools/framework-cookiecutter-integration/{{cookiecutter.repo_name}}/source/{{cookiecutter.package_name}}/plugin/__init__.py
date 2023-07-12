# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from {{cookiecutter.package_name}} import constants as {{cookiecutter.host_type}}_constants
from {{cookiecutter.package_name}} import utils as {{cookiecutter.host_type}}_utils
from {{cookiecutter.package_name}}.asset import {{cookiecutter.host_type_capitalized}}FtrackObjectManager
from {{cookiecutter.package_name}}.asset.dcc_object import {{cookiecutter.host_type_capitalized}}DccObject


class {{cookiecutter.host_type_capitalized}}BasePlugin(plugin.BasePlugin):

    host_type = {{cookiecutter.host_type}}_constants.HOST_TYPE

    FtrackObjectManager = {{cookiecutter.host_type_capitalized}}FtrackObjectManager
    '''FtrackObjectManager class to use'''
    DccObject = {{cookiecutter.host_type_capitalized}}DccObject
    '''DccObject class to use'''

    @{{cookiecutter.host_type}}_utils.run_in_main_thread
    def _run(self, event):
        return super({{cookiecutter.host_type_capitalized}}BasePlugin, self)._run(event)


class {{cookiecutter.host_type_capitalized}}BasePluginWidget({{cookiecutter.host_type_capitalized}}BasePlugin, pluginWidget.BasePluginWidget):
    category = 'plugin.widget'
    ui_type = {{cookiecutter.host_type}}_constants.UI_TYPE

    @{{cookiecutter.host_type}}_utils.run_in_main_thread
    def _run(self, event):
        return super({{cookiecutter.host_type_capitalized}}BasePluginWidget, self)._run(event)


from {{cookiecutter.package_name}}.plugin.load import *
from {{cookiecutter.package_name}}.plugin.open import *
from {{cookiecutter.package_name}}.plugin.publish import *
from {{cookiecutter.package_name}}.plugin.asset_manager import *
from {{cookiecutter.package_name}}.plugin.resolver import *
