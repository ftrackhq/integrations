# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError
from ftrack_framework_flame.utils import presets

import flame

class FlameReviewableExporterPlugin(BasePlugin):
    name = 'flame_reviewable_exporter'

    def run(self, store):
        '''
        Create a screenshot from the selected camera given in the *store*.
        Save it to a temp file and this one will be published as thumbnail.
        '''
        component_name = self.options.get('component')

        exported_path = get_temp_path(is_directory=True)

        self.logger.debug(f"Reviewable has been saved to: {exported_path}.")

        current_selection = flame.media_panel.selected_entries[0]
        if not isinstance(current_selection, (flame.PySequence, flame.PyClip)):
            return

        thumbnail_preset_path = presets.get_preset_path('MOV8')

        exporter = flame.PyExporter()

        # Set the exporter to use foreground export. By default it will send a
        # job to Backburner to do the export.
        #
        exporter.foreground = True

        exporter.export(
            current_selection, thumbnail_preset_path, exported_path
        )
        file_name = f'{current_selection.name.get_value()}.mov'
        destination_path = os.path.join(exported_path, file_name)
        self.logger.debug(f"Reviwable Exported to {destination_path}")
        store['components'][component_name]['exported_path'] = destination_path

