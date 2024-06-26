# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import tempfile
import uuid

import hou
import toolutils

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class HoudiniThumbnailExporterPlugin(BasePlugin):
    name = 'houdini_thumbnail_exporter'

    def run(self, store):
        '''
        Create a screenshot from the selected camera given in the *store*.
        Save it to a temp file and this one will be published as thumbnail.
        '''
        component_name = self.options.get('component')

        resolution = [1024, 768]

        try:
            thumbnail_path = "{}.jpg".format(
                os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
            )
            if os.name == "nt":
                thumbnail_path = thumbnail_path.replace("\\", "\\\\")

            desktop = hou.ui.curDesktop()
            scene_view = toolutils.sceneViewer()

            if scene_view is None or (
                scene_view.type() != hou.paneTabType.SceneViewer
            ):
                raise hou.Error('No scene view available to flipbook')

            viewport = scene_view.curViewport()

            if viewport.camera() is not None:
                resolution = [
                    viewport.camera().parm('resx').eval(),
                    viewport.camera().parm('resy').eval(),
                ]

            view = '{}.{}.world.{}'.format(
                desktop.name(),
                scene_view.name(),
                viewport.name(),
            )

            self.logger.debug(
                'Creating thumbnail from view {} to {}.'.format(
                    view, thumbnail_path
                )
            )

            executeCommand = 'viewwrite -c -f 0 1 -r {} {} {} {}'.format(
                resolution[0], resolution[1], view, thumbnail_path
            )

            hou.hscript(executeCommand)

            self.logger.debug(
                f"Thumbnail has been saved to: {thumbnail_path}."
            )
        except Exception as error:
            raise PluginExecutionError(message=error)

        store['components'][component_name]['exported_path'] = thumbnail_path
