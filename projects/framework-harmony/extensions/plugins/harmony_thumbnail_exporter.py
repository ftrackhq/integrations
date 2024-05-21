# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import clique
import shutil

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class HarmonyThumbnailExporterPlugin(BasePlugin):
    name = 'harmony_thumbnail_exporter'

    def run(self, store):
        '''
        Create a screenshot from the selected camera given in the *store*.
        Save it to a temp file and this one will be published as thumbnail.
        '''
        component_name = self.options.get('component')

        '''
        Pick up previously rendered image sequence and transcode it to a movie file, storing the path
        in the *store* under the component name.
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

        # Pick the middle frame
        middle_frame = list(collection.indexes)[
            int(len(collection.indexes) / 2)
        ]

        extension = collection.format('{tail}')
        image_path = get_temp_path(filename_extension=extension)

        # Copy the frame to the temp path
        src = collection.format('{head}%s{tail}' % middle_frame)

        self.logger.debug(f'Copying {src} to {image_path}')
        shutil.copy(src, image_path)

        store['components'][component_name]['exported_path'] = image_path
