# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from pymxs import runtime as rt


class MaxSetupFrameRangeStartupPlugin(BasePlugin):
    name = 'max_setup_frame_range'

    def run(self, store):
        '''
        Set the maya frame range and frame rate from the ftrack custom attributes
        '''
        context_id = self.context_id
        task = self.session.get('Context', context_id)
        if task:
            try:
                start_frame = task['parent']['custom_attributes'].get(
                    'fstart', 1.0
                )
                end_frame = task['parent']['custom_attributes'].get(
                    'fend', 100.0
                )
                fps = task['parent']['custom_attributes'].get('fps', 9)

                if end_frame == start_frame:
                    self.logger.warning(
                        f'''
                        3dsMax does not allow start and end frame to be the same.
                        Your desired values: {start_frame} - {end_frame}
                        Required to add one frame of padding to the end.
                        Actually used values: {start_frame} - {end_frame + 1}
                        '''
                    )
                    end_frame += 1

                # Set start end frames and frame rate
                rt.frameRate = fps
                rt.animationRange = rt.interval(start_frame, end_frame)
                rt.sliderTime = start_frame

            except Exception as error:
                raise PluginExecutionError(
                    f"Error trying to setup frame range on max, error: {error}"
                )
        else:
            self.logger.warning("Couldn't find a task to pick up frame range")
