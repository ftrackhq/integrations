# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import tempfile
import os
import uuid
import glob

import maya.cmds as cmd
import maya

from ftrack_connect_pipeline_maya import plugin


class OutputMayaThumbnailPlugin(plugin.OutputMayaPlugin):
    plugin_name = 'thumbnail'

    def run(self, context=None, data=None, options=None):
        component_name = options['component_name']
        camera_name = options.get('camera_name', 'persp')

        nodes = cmd.ls(sl=True)
        cmd.select(cl=True)

        panel = cmd.getPanel(wf=True)
        previous_camera = cmd.modelPanel(panel, q=True, camera=True)

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
            format="image",
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
