# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import tempfile

import maya.cmds as cmd
import maya

from ftrack_connect_pipeline_maya import plugin


class ExtractMayaReviewablePlugin(plugin.OutputMayaPlugin):
    plugin_name = 'reviewable'

    def run(self, context=None, data=None, options=None):
        component_name = options['component_name']
        camera_name = options.get('camera_name', 'persp')

        panel = cmd.getPanel(wf=True)
        previous_camera = cmd.modelPanel(panel, q=True, camera=True)

        cmd.lookThru(camera_name)

        res_w = int(cmd.getAttr('defaultResolution.width'))
        res_h = int(cmd.getAttr('defaultResolution.height'))

        start_frame = cmd.playbackOptions(q=True, min=True)
        end_frame = cmd.playbackOptions(q=True, max=True)

        prev_selection = cmd.ls(sl=True)
        cmd.select(cl=True)

        filename = tempfile.NamedTemporaryFile(
            suffix='.mov'
        ).name

        cmd.playblast(
            format='qt',
            sequenceTime=0,
            clearCache=1,
            viewer=0,
            offScreen=True,
            showOrnaments=0,
            frame=range(int(start_frame), int(end_frame + 1)),
            filename=filename,
            fp=4,
            percent=100,
            compression="png",
            quality=70,
            w=res_w,
            h=res_h
        )

        if len(prev_selection):
            cmd.select(prev_selection)

        cmd.lookThru(previous_camera)

        return {component_name: filename}


def register(api_object, **kw):
    plugin = ExtractMayaReviewablePlugin(api_object)
    plugin.register()
