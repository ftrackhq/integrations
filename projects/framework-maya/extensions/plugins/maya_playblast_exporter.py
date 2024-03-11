# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import glob
import platform
import maya.cmds as cmds

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class MayaPlayblastExporterPlugin(BasePlugin):
    name = 'maya_playblast_exporter'

    def run(self, store):
        '''
        Create a screenshot from the selected camera given in the *store*.
        Save it to a temp file and this one will be published as thumbnail.
        '''
        component_name = self.options.get('component')
        camera_name = store['components'][component_name].get('camera_name')

        # Get Current selected nodes
        previous_selected_nodes = cmds.ls(sl=True)
        self.logger.debug(
            f"Previous selected nodes saved.: {previous_selected_nodes}."
        )
        # Cleanup the selection
        cmds.select(cl=True)

        # Get the current panel
        current_panel = cmds.getPanel(wf=True)
        self.logger.debug(f"Current panel is: {current_panel}.")
        panel_type = cmds.getPanel(to=current_panel)  # scriptedPanel
        if panel_type != 'modelPanel':
            visible_panels = cmds.getPanel(vis=True)
            for _panel in visible_panels:
                if cmds.getPanel(to=_panel) == 'modelPanel':
                    current_panel = _panel
                    break
                else:
                    current_panel = None
        # Get the current camera
        previous_camera = 'presp'
        if current_panel:
            previous_camera = cmds.modelPanel(
                current_panel, q=True, camera=True
            )
            self.logger.debug(
                f"Previous selected camera saved: {previous_camera}."
            )

        cmds.lookThru(camera_name)

        # Set resolution and start/end frame from maya settings
        res_w = int(cmds.getAttr('defaultResolution.width'))
        res_h = int(cmds.getAttr('defaultResolution.height'))

        start_frame = cmds.playbackOptions(q=True, min=True)
        end_frame = cmds.playbackOptions(q=True, max=True)

        exported_path = get_temp_path()

        playblast_format = 'movie'
        playblast_compression = None
        if 'linux' in platform.platform().lower():
            playblast_format = 'qt'
            playblast_compression = 'raw'

        try:
            # Create the image
            export_result = cmds.playblast(
                format=playblast_format,
                compression=playblast_compression,
                sequenceTime=0,
                clearCache=1,
                viewer=0,
                offScreen=True,
                showOrnaments=0,
                frame=range(int(start_frame), int(end_frame + 1)),
                filename=exported_path,
                fp=4,
                percent=100,
                quality=70,
                w=res_w,
                h=res_h,
            )
            self.logger.debug(f"Playblast exported to: {exported_path}")
        except Exception as error:
            raise PluginExecutionError(
                f"Error trying to create the playblast, error: {error}"
            )

        if previous_selected_nodes:
            cmds.select(previous_selected_nodes)
            self.logger.debug("Previous camera has been selected.")
        self.logger.debug(f"export_result: {export_result}")
        # export_result = export_result.replace('####', '*')
        full_path = glob.glob(export_result + '.*')[0]
        self.logger.debug(f"Full path of the exported thumbnail: {full_path}")

        cmds.lookThru(previous_camera)

        store['components'][component_name]['exported_path'] = full_path
