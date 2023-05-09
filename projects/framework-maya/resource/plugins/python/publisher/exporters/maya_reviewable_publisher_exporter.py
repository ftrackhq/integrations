# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import tempfile
import glob
import platform

import maya.cmds as cmds

from ftrack_connect_pipeline_maya import plugin
import ftrack_api


class MayaReviewablePublisherExporterPlugin(
    plugin.MayaPublisherExporterPlugin
):
    '''Maya reviewable exporter plugin'''

    plugin_name = 'maya_reviewable_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        '''Export Maya reviewable based on collected objects in *data* and camera supplied in *options*'''

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])
        camera_name = options.get('camera_name', 'persp')
        if collected_objects:
            camera_name = collected_objects[0]

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

        previous_camera = 'persp'
        if current_panel:
            previous_camera = cmds.modelPanel(
                current_panel, q=True, camera=True
            )

        cmds.lookThru(camera_name)

        res_w = int(cmds.getAttr('defaultResolution.width'))
        res_h = int(cmds.getAttr('defaultResolution.height'))

        start_frame = cmds.playbackOptions(q=True, min=True)
        end_frame = cmds.playbackOptions(q=True, max=True)

        prev_selection = cmds.ls(sl=True)
        cmds.select(cl=True)

        filename = tempfile.NamedTemporaryFile().name

        playblast_data = dict(
            format='movie',
            sequenceTime=0,
            clearCache=1,
            viewer=0,
            offScreen=True,
            showOrnaments=0,
            frame=range(int(start_frame), int(end_frame + 1)),
            filename=filename,
            fp=4,
            percent=100,
            quality=70,
            w=res_w,
            h=res_h,
        )

        if 'linux' in platform.platform().lower():
            playblast_data['format'] = 'qt'
            playblast_data['compression'] = 'raw'

        cmds.playblast(**playblast_data)

        if len(prev_selection):
            cmds.select(prev_selection)

        cmds.lookThru(previous_camera)

        temp_files = glob.glob(filename + '.*')
        # TODO:
        # find a better way to find the extension of the playblast file.
        full_path = temp_files[0]

        return [full_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MayaReviewablePublisherExporterPlugin(api_object)
    plugin.register()
