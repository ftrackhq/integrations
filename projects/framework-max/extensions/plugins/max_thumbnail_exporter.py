# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack


from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from pymxs import runtime as rt


class MaxThumbnailExporterPlugin(BasePlugin):
    name = 'max_thumbnail_exporter'

    def run(self, store):
        '''
        Create a screenshot from the selected camera given in the *store*.
        Save it to a temp file and this one will be published as thumbnail.
        '''
        component_name = self.options.get('component')

        thumbnail_path = None
        try:
            viewport_index = rt.viewport.activeViewport
            bitmap = rt.viewport.getViewportDib(index=viewport_index)
            thumbnail_path = get_temp_path(filename_extension='.jpg')
            bitmap.filename = thumbnail_path
            rt.save(bitmap)

            self.logger.debug(
                f"Thumbnail has been saved to: {thumbnail_path}."
            )
        except Exception as error:
            raise PluginExecutionError(message=error)

        store['components'][component_name]['exported_path'] = thumbnail_path
