# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import clique
import shutil

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class HarmonyThumbnailExporterPlugin(BasePlugin):
    name = 'harmony_thumbnail_exporter'

    SUPPORTED_FORMATS = ['bmp', 'gif', 'jpeg', 'jpg', 'png', 'tif', 'tiff']

    def run(self, store):
        '''
        Pick up previously rendered image sequence and pick the middle image
        for use as thumbnail if possible.
        '''
        component_name = self.options.get('component')
        sequence_expression = (
            store['components'].get('sequence', {}).get('exported_path')
        )
        if not sequence_expression:
            raise PluginExecutionError(
                f'Could not locate previously exported image sequence component and output'
            )

        collection = clique.parse(sequence_expression)
        if not collection:
            raise PluginExecutionError(
                message=f"Could not parse image sequence from: {sequence_expression}"
            )

        # Check if the format is supported
        extension = collection.format('{tail}')
        if extension not in self.SUPPORTED_FORMATS:
            self.logger.warning(
                f'Unsupported thumbnail format: {extension}, skipping'
            )
            return

        # Pick the middle frame
        middle_frame = list(collection.indexes)[
            int(len(collection.indexes) / 2)
        ]

        image_path = get_temp_path(filename_extension=extension)

        # Copy the frame to the temp path
        src = collection.format('{head}%s{tail}' % middle_frame)

        self.logger.debug(f'Copying {src} to {image_path}')
        shutil.copy(src, image_path)

        store['components'][component_name]['exported_path'] = image_path
