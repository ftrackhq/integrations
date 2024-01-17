# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import glob
import maya.cmds as cmds

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class MayaThumbnailExporterPlugin(BasePlugin):
    name = 'maya_thumbnail_exporter'

    def run(self, store):
        '''
        Create a screenshot from the selected camera given in the *store*.
        Save it to a temp file and this one will be published as thumbnail.
        '''
        component_name = self.options.get('component')
        camera_name = store['components'][component_name].get('camera_name')

        # Get Current selected nodes
        prevoius_selected_nodes = cmds.ls(sl=True)
        # Cleanup the selection
        cmds.select(cl=True)

        # Get the current panel
        current_panel = cmds.getPanel(wf=True)
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

        cmds.lookThru(camera_name)

        restoreRenderGlobals = False
        try:
            # Ensure JPEG is set in renderglobals.
            # Only used on windows for some reason
            currentFormatStr = cmds.getAttr(
                'defaultRenderGlobals.imageFormat', asString=True
            )
            if not (
                'jpg' in currentFormatStr.lower()
                or 'jpeg' in currentFormatStr.lower()
            ):
                currentFormatInt = cmds.getAttr(
                    'defaultRenderGlobals.imageFormat'
                )
                cmds.setAttr('defaultRenderGlobals.imageFormat', 8)
                restoreRenderGlobals = True
        except Exception as error:
            raise PluginExecutionError(
                f"Error trying to set JPEG in renderglobals, error: {error}"
            )

        exported_path = get_temp_path(filename_extension='jpg')

        try:
            # Create the image
            export_result = cmds.playblast(
                format='image',
                frame=cmds.currentTime(query=True),
                compression='jpg',
                quality=80,
                showOrnaments=False,
                forceOverwrite=True,
                viewer=False,
                filename=exported_path,
            )
        except Exception as error:
            raise PluginExecutionError(
                f"Error trying to create the thumbnail, error: {error}"
            )

        # Restore render globals
        if restoreRenderGlobals:
            cmds.setAttr('defaultRenderGlobals.imageFormat', currentFormatInt)

        if prevoius_selected_nodes:
            cmds.select(prevoius_selected_nodes)
        export_result = export_result.replace('####', '*')
        full_path = glob.glob(export_result)[0]

        cmds.lookThru(previous_camera)

        store['components'][component_name]['exported_path'] = full_path
