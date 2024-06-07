# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import hou

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class HoudiniSetupFrameRangeStartupPlugin(BasePlugin):
    name = 'houdini_setup_frame_range'

    def run(self, store):
        '''
        Set the houdini frame range and fps from the ftrack custom attributes
        '''
        context_id = self.context_id
        task = self.session.get('Context', context_id)
        if task:
            try:
                st_frame = float(
                    task['parent']['custom_attributes'].get('fstart', 1.0)
                )
                end_frame = float(
                    task['parent']['custom_attributes'].get('fend', 100.0)
                )
                fps = float(
                    task['parent']['custom_attributes'].get('fps', 24.0)
                )
                # Set start frame
                self.logger.debug(
                    f'Setting frame range and fps to: {st_frame}-{end_frame} @ {fps}fps'
                )
                hou.hscript(
                    'tset {0} {1}'.format(st_frame / fps, end_frame / fps)
                )
                hou.playbar.setPlaybackRange(st_frame, end_frame)
                hou.setFrame(st_frame)
                hou.setFps(fps)
            except Exception as error:
                raise PluginExecutionError(
                    f"Error trying to setup frame range on houdini, error: {error}"
                )
        else:
            self.logger.warning("Couldn't find a task to pick up frame range")
