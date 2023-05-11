# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from pymxs import runtime as rt

from ftrack_connect_pipeline_3dsmax import plugin

import ftrack_api


class MaxGeometryPublisherValidatorPlugin(plugin.MaxPublisherValidatorPlugin):
    plugin_name = 'max_geometry_publisher_validator'

    def run(self, context_data=None, data=None, options=None):
        '''Return true if all the collected Max node supplied with *data* are geometry'''

        if not data:
            return False

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])
        if len(collected_objects) == 0:
            msg = 'No geometries selected!'
            self.logger.error(msg)
            return False, {'message': msg}
        for obj in collected_objects:
            node = rt.getNodeByName(obj)
            if not rt.superClassOf(node) == rt.GeometryClass:
                return (
                    False,
                    {
                        'message': "the object: {} is not a geometry node type".format(
                            obj
                        ),
                        'data': None,
                    },
                )
        user_data = {'message': 'geometry exported correctly', 'data': None}
        return True, user_data


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxGeometryPublisherValidatorPlugin(api_object)
    plugin.register()
