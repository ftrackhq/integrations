# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import maya.cmds as cmds

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class MayaHelloWorldBootstrapPlugin(BasePlugin):
    name = 'maya_hello_world'

    def run(self, store):
        '''
        Set the selected camera name to the *store*
        '''
        print("hello world")
