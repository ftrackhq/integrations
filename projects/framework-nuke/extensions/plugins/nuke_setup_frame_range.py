# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import nuke

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class NukeSetupFrameRangeStartupPlugin(BasePlugin):
    name = 'nuke_setup_frame_range'

    def run(self, store):
        '''
        Set the nuke frame range and frame rate from the ftrack custom attributes
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
                # Set start frame
                nuke.root()['first_frame'].setValue(int(st_frame))
                # Set end frame
                nuke.root()['last_frame'].setValue(int(end_frame))
                # Set frames per second (fps)
                nuke.root()['fps'].setValue(int(fps))
            except Exception as error:
                raise PluginExecutionError(
                    f"Error trying to setup frame range on maya, error: {error}"
                )
        else:
            self.logger.warning("Couldn't find a task to pick up frame range")
