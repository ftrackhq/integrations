# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

import tempfile
import os
import uuid

import hou
import toolutils

from ftrack_connect_pipeline_houdini import plugin
import ftrack_api


class HoudiniThumbnailPublisherExporterPlugin(
    plugin.HoudiniPublisherExporterPlugin
):
    plugin_name = 'houdini_thumbnail_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        '''Export a thumbnail of the viewport to a file'''

        res = [1024, 768]

        path = "%s.jpg" % (
            os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
        )
        if os.name == "nt":
            path = path.replace('\\', '\\\\')

        desktop = hou.ui.curDesktop()
        scene_view = toolutils.sceneViewer()

        if scene_view is None or (
            scene_view.type() != hou.paneTabType.SceneViewer
        ):
            raise hou.Error('No scene view available to flipbook')
        viewport = scene_view.curViewport()

        if viewport.camera() is not None:
            res = [
                viewport.camera().parm('resx').eval(),
                viewport.camera().parm('resy').eval(),
            ]

        view = '%s.%s.world.%s' % (
            desktop.name(),
            scene_view.name(),
            viewport.name(),
        )

        self.logger.debug(
            'Creating thumbnail from view {} to {}.'.format(view, path)
        )

        executeCommand = 'viewwrite -c -f 0 1 -r {} {} {} {}'.format(
            res[0], res[1], view, path
        )

        hou.hscript(executeCommand)

        return [path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = HoudiniThumbnailPublisherExporterPlugin(api_object)
    plugin.register()
