# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

import {{cookiecutter.host_type}}

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_{{cookiecutter.host_type}} import constants as {{cookiecutter.host_type}}_constants
from ftrack_connect_pipeline_{{cookiecutter.host_type}}.utils import custom_commands as {{cookiecutter.host_type}}_utils
from ftrack_connect_pipeline_{{cookiecutter.host_type}}.asset import {{cookiecutter.host_type|capitalize}}FtrackObjectManager
from ftrack_connect_pipeline_{{cookiecutter.host_type}}.asset.dcc_object import {{cookiecutter.host_type|capitalize}}DccObject


class {{cookiecutter.host_type|capitalize}}BasePlugin(plugin.BasePlugin):

    host_type = {{cookiecutter.host_type}}_constants.HOST_TYPE

    FtrackObjectManager = {{cookiecutter.host_type|capitalize}}FtrackObjectManager
    '''FtrackObjectManager class to use'''
    DccObject = {{cookiecutter.host_type|capitalize}}DccObject
    '''DccObject class to use'''

    @{{cookiecutter.host_type}}_utils.run_in_main_thread
    def _run(self, event):
        return super({{cookiecutter.host_type|capitalize}}BasePlugin, self)._run(event)


class {{cookiecutter.host_type|capitalize}}BasePluginWidget({{cookiecutter.host_type|capitalize}}BasePlugin, pluginWidget.BasePluginWidget):
    category = 'plugin.widget'
    ui_type = {{cookiecutter.host_type}}_constants.UI_TYPE

    @{{cookiecutter.host_type}}_utils.run_in_main_thread
    def _run(self, event):
        return super({{cookiecutter.host_type|capitalize}}BasePluginWidget, self)._run(event)


from ftrack_connect_pipeline_{{cookiecutter.host_type}}.plugin.load import *
from ftrack_connect_pipeline_{{cookiecutter.host_type}}.plugin.open import *
from ftrack_connect_pipeline_{{cookiecutter.host_type}}.plugin.publish import *
from ftrack_connect_pipeline_{{cookiecutter.host_type}}.plugin.asset_manager import *
