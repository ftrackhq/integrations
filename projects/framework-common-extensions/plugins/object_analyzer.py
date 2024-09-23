# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import json
import re

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import (
    PluginUIHookExecutionError,
    PluginExecutionError,
)


class ObjectAnalyzerPlugin(BasePlugin):
    name = 'object_analyzer'

    def get_st_end_frame_object(self, obj_path):
        with open(obj_path, 'r') as file:
            obj_data = json.load(file)
        return obj_data.get('start_frame'), obj_data.get('end_frame')

    def run(self, store):
        '''
        Collect objects path and store them in the given store
        '''
        if not store.get('collected_objects'):
            raise PluginExecutionError(
                'Please pass collected objects to the store before continue.'
            )
        collected_objects = store.get('collected_objects')

        for obj in collected_objects:
            obj_path = obj.get('obj_path')
            if not os.path.exists(obj_path):
                raise PluginExecutionError(
                    'Object path does not exist: {0}'.format(obj_path)
                )

            st_frame, end_frame = self.get_st_end_frame_object(obj_path)
            obj['start_frame'] = st_frame
            obj['end_frame'] = end_frame

            obj_name = obj.get('obj_name')
            name_pattern = self.options.get('name_pattern')
            if not name_pattern:
                raise PluginExecutionError(
                    'Please provide name_pattern in the options.'
                )

            # Convert user-friendly pattern to regex
            keys = re.findall(r'\{(\w+)\}', name_pattern)
            regex_pattern = name_pattern.format(
                **{key: f'(?P<{key}>[^_]+)' for key in keys}
            )
            regex_pattern = f'^{regex_pattern}$'

            match = re.match(regex_pattern, obj_name)
            if not match:
                raise PluginExecutionError(
                    f'Object name does not match the provided pattern: {obj_name}'
                )

            # Extract parts of the name based on the pattern
            for key in match.groupdict():
                obj[key] = match.group(key)

        store['collected_objects'] = collected_objects
