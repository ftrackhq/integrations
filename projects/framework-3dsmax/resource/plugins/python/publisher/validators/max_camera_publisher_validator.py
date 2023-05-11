# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from pymxs import runtime as rt

import ftrack_api

from ftrack_connect_pipeline_3dsmax import plugin


class MaxCameraPublisherValidatorPlugin(plugin.MaxPublisherValidatorPlugin):
    plugin_name = 'max_camera_publisher_validator'

    def run(self, context_data=None, data=None, options=None):
        '''Return true if all the collected Max node supplied with *data* are cameras'''
        if not data:
            return False

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])

        for obj in collected_objects:
            node = rt.getNodeByName(obj)
            is_camera = rt.isKindOf(node, rt.Camera)
            if not is_camera:
                return (
                    False,
                    {
                        'message': "the object: {} is not a camera node type".format(
                            obj
                        ),
                        'data': None,
                    },
                )
        user_data = {'message': 'camera exported correctly', 'data': None}
        return True, user_data


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxCameraPublisherValidatorPlugin(api_object)
    plugin.register()
