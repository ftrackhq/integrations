# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import tempfile
import glob

import maya.cmds as cmds

from ftrack_connect_pipeline_maya import plugin
import ftrack_api


class MayaThumbnailPublisherExporterPlugin(plugin.MayaPublisherExporterPlugin):
    '''Maya thumbnail exporter plugin'''

    plugin_name = 'maya_thumbnail_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        '''Export Maya thumbnail based on collected objects in *data* and camera supplied in *options*'''

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])
        camera_name = options.get('camera_name', 'persp')
        if collected_objects:
            camera_name = collected_objects[0]

        nodes = cmds.ls(sl=True)
        cmds.select(cl=True)

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
        previous_camera = 'presp'
        if current_panel:
            previous_camera = cmds.modelPanel(
                current_panel, q=True, camera=True
            )

        cmds.lookThru(camera_name)

        # Ensure JPEG is set in renderglobals.
        # Only used on windows for some reason
        currentFormatStr = cmds.getAttr(
            'defaultRenderGlobals.imageFormat', asString=True
        )

        restoreRenderGlobals = False
        if not (
            'jpg' in currentFormatStr.lower()
            or 'jpeg' in currentFormatStr.lower()
        ):
            currentFormatInt = cmds.getAttr('defaultRenderGlobals.imageFormat')
            cmds.setAttr('defaultRenderGlobals.imageFormat', 8)
            restoreRenderGlobals = True

        filename = tempfile.NamedTemporaryFile(suffix='.jpg').name

        res = cmds.playblast(
            format='image',
            frame=cmds.currentTime(query=True),
            compression='jpg',
            quality=80,
            showOrnaments=False,
            forceOverwrite=True,
            viewer=False,
            filename=filename,
        )

        if restoreRenderGlobals:
            cmds.setAttr('defaultRenderGlobals.imageFormat', currentFormatInt)

        if nodes is not None and len(nodes):
            cmds.select(nodes)
        res = res.replace('####', '*')
        path = glob.glob(res)[0]

        cmds.lookThru(previous_camera)

        return [path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MayaThumbnailPublisherExporterPlugin(api_object)
    plugin.register()
