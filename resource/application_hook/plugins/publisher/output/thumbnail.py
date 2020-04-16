# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import tempfile
import os
import uuid
import glob

import maya.cmds as cmd
import maya

from ftrack_connect_pipeline_maya import plugin
from ftrack_connect_pipeline import constants

class OutputMayaThumbnailPlugin(plugin.PublisherOutputMayaPlugin):
    plugin_name = 'thumbnail'

    def run(self, context=None, data=None, options=None):
        component_name = options['component_name']
        camera_name = options.get('camera_name', 'persp')

        nodes = cmd.ls(sl=True)
        cmd.select(cl=True)

        current_panel = cmd.getPanel(wf=True)
        panel_type = cmd.getPanel(to=current_panel)  # scriptedPanel
        if panel_type != 'modelPanel':
            visible_panels = cmd.getPanel(vis=True)
            for _panel in visible_panels:
                if cmd.getPanel(to=_panel) == 'modelPanel':
                    current_panel = _panel
                    break
                else:
                    current_panel = None
        previous_camera = 'presp'
        if current_panel:
            previous_camera = cmd.modelPanel(current_panel, q=True, camera=True)

        cmd.lookThru(camera_name)

        # Ensure JPEG is set in renderglobals.
        # Only used on windows for some reason
        currentFormatStr = cmd.getAttr(
            'defaultRenderGlobals.imageFormat',
            asString=True
        )

        restoreRenderGlobals = False
        if not (
                'jpg' in currentFormatStr.lower() or
                'jpeg' in currentFormatStr.lower()
        ):
            currentFormatInt = cmd.getAttr('defaultRenderGlobals.imageFormat')
            cmd.setAttr('defaultRenderGlobals.imageFormat', 8)
            restoreRenderGlobals = True

        filename = tempfile.NamedTemporaryFile(
            suffix='.jpg'
        ).name

        res = cmd.playblast(
            format='image',
            frame=cmd.currentTime(query=True),
            compression='jpg',
            quality=80,
            showOrnaments=False,
            forceOverwrite=True,
            viewer=False,
            filename=filename
        )

        if restoreRenderGlobals:
            cmd.setAttr('defaultRenderGlobals.imageFormat', currentFormatInt)

        if nodes is not None and len(nodes):
            cmd.select(nodes)
        res = res.replace('####', '*')
        path = glob.glob(res)[0]

        cmd.lookThru(previous_camera)

        return {component_name: path}


def register(api_object, **kw):
    plugin = OutputMayaThumbnailPlugin(api_object)
    plugin.register()
