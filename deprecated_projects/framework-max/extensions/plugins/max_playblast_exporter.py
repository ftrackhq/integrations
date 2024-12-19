# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from pymxs import runtime as rt


class MaxPlayblastExporterPlugin(BasePlugin):
    name = 'max_playblast_exporter'

    def run(self, store):
        '''
        Creates a playblast from the currently active viewport.
        '''
        component_name = self.options.get('component')

        exported_path = get_temp_path(
            is_directory=False, filename_extension="avi"
        )

        try:
            # Create the most basic preview with the currently set viewport settings
            rt.createPreview(
                outputAVI=True,
                filename=exported_path,
                autoplay=False,  # don't open a video player when the preview is done
            )

            self.logger.debug(f"Preview exported to: {exported_path}")
        except Exception as error:
            raise PluginExecutionError(
                f"Error trying to create the playblast, error: {error}"
            )

        store['components'][component_name]['exported_path'] = exported_path
