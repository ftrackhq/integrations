# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_maya import plugin

import maya.cmds as cmds
import ftrack_api


class MayaGeometryPublisherValidatorPlugin(
    plugin.MayaPublisherValidatorPlugin
):
    '''Maya geometry publisher validator'''

    plugin_name = 'maya_geometry_publisher_validator'

    def run(self, context_data=None, data=None, options=None):
        '''Make sure the collected objects supplied in *data* are geometries'''

        if not data:
            return False

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])
        if len(collected_objects) == 0:
            msg = 'No geometries selected!'
            self.logger.error(msg)
            return (False, {'message': msg})
        for obj in collected_objects:
            if not cmds.objectType(obj, isAType='geometryShape'):
                return (
                    False,
                    {
                        'message': "the object: {} is not a geometry shape type".format(
                            obj
                        ),
                        'data': None,
                    },
                )
        user_data = {'message': 'geometry exported correctly', 'data': None}
        return (True, user_data)


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MayaGeometryPublisherValidatorPlugin(api_object)
    plugin.register()
