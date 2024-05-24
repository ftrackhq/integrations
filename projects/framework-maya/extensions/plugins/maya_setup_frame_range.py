# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import maya.cmds as cmds

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class MayaSetupFrameRangeStartupPlugin(BasePlugin):
    name = 'maya_setup_frame_range'

    def run(self, store):
        '''
        Set the selected camera name to the *store*
        '''
        context_id = self.context_id
        task = self.session.get('Context', context_id)
        if task:
            try:
                st_frame = task['parent']['custom_attributes'].get(
                    'fstart', 1.0
                )
                end_frame = task['parent']['custom_attributes'].get(
                    'fend', 100.0
                )
                fps = task['parent']['custom_attributes'].get('fps', 24)
                # Set start end frames and frame rate
                cmds.playbackOptions(
                    min=int(st_frame),
                    max=int(end_frame),
                    ast=int(st_frame),
                    aet=int(end_frame),
                )
                cmds.currentUnit(time=f'{int(fps)}fps')
            except Exception as error:
                raise PluginExecutionError(
                    f"Error trying to setup frame range on maya, error: {error}"
                )
        else:
            self.logger.warning("Couldn't find a task to pick up frame range")
