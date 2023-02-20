# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_maya import plugin

import maya.cmds as cmds
import ftrack_api


class MayaCameraPublisherValidatorPlugin(plugin.MayaPublisherValidatorPlugin):
    '''Maya camera publisher validator plugin'''

    plugin_name = 'maya_camera_publisher_validator'

    def run(self, context_data=None, data=None, options=None):
        '''Make sure the collected objects supplied in *data* are cameras'''

        if not data:
            return False

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])
        if len(collected_objects) == 0:
            msg = 'No cameras selected!'
            self.logger.error(msg)
            return (False, {'message': msg})
        for obj in collected_objects:
            is_camera = False
            relatives = cmds.listRelatives(obj, f=True)
            for relative in relatives:
                if cmds.objectType(relative, isAType="camera"):
                    is_camera = True
                if is_camera:
                    break
            if not is_camera:
                self.logger.error("{} is not a camera!".format(obj))
                return (False, {'message': "{} is not a camera!".format(obj)})
        return True


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MayaCameraPublisherValidatorPlugin(api_object)
    plugin.register()
