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
                # We're not using a default for the get method anymore (.get('fstart', 1.0)
                # as this could result in None being returned in some cases.
                # Therefore we're now introducing a default value AFTER retrieving the value
                # from ftrack.
                # TODO: Verify whether this might also happen in other integrations
                #  and other custom attributes
                st_frame = float(
                    task['parent']['custom_attributes'].get('fstart') or 1.0
                )
                end_frame = float(
                    task['parent']['custom_attributes'].get('fend') or 100.0
                )
                fps = float(
                    task['parent']['custom_attributes'].get('fps') or 24.0
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
