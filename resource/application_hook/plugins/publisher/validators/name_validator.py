# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_maya import plugin

import maya.cmds as mc


class CheckGeoNamesValidatorPlugin(plugin.ValidatorMayaPlugin):
    plugin_name = 'name_validator'

    def run(self, context=None, data=None, options=None):
        print "The context --> ", context
        print "The data --> ", data
        print "The options --> ", options
        self.logger.info('context: {}'.format(context))
        self.logger.info('data: {}'.format(data))
        self.logger.info('options: {}'.format(options))
        allObj = mc.ls(data, tr=True)
        for obj in allObj:
            if obj.startswith("ftrack_") == False:
                return False
        return True


def register(api_object, **kw):
    plugin = CheckGeoNamesValidatorPlugin(api_object)
    plugin.register()
