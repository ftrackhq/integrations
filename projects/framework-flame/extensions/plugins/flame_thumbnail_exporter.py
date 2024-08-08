# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import datetime
from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError
from ftrack_framework_flame import presets

import flame

class FlameThumbnailExporterPlugin(BasePlugin):
    name = 'flame_thumbnail_exporter'

    def run(self, store):
        '''
        Create a screenshot from the selected camera given in the *store*.
        Save it to a temp file and this one will be published as thumbnail.
        '''
        component_name = self.options.get('component')

        exported_path = get_temp_path(is_directory=True)

        try:
            # TODO: thumbnail_path = Export thumbnail

            self.logger.debug(f"Thumbnail has been saved to: {exported_path}.")
        except Exception as error:
            raise PluginExecutionError(message=error)

        current_selection = flame.media_panel.selected_entries[0]
        if not isinstance(current_selection, (flame.PySequence, flame.PyClip)):
            return

        self.logger.debug(f"Current selection: {current_selection}.")
        thumbnail_preset_path = presets.get_preset_path('JPG8')

        exporter = flame.PyExporter()

        # Set the exporter to use foreground export. By default it will send a
        # job to Backburner to do the export.
        #
        exporter.foreground = True

        # Do the actual export.
        #
        exporter.export_between_marks = True

        # Duplicate the clip to avoid modifying the clip itself.
        #
        duplicate_clip = flame.duplicate(current_selection)
        self.logger.debug(f"Extracted clip: {duplicate_clip}.")

        try:
            # Give the duplicate clip an unique name. We assume here that the preset
            # we will use have <name> in the destination path.
            #
            new_name = current_selection.name + datetime.datetime.now().strftime(
                "%Y_%m_%d__%H_%M_%S"
            )
            duplicate_clip.name = new_name

            # export first frame
            duplicate_clip.in_mark = current_selection.current_time.get_value()
            duplicate_clip.out_mark = current_selection.current_time.get_value() + 1

            exporter.export(
                duplicate_clip, thumbnail_preset_path, exported_path
            )
            frame_name = str(current_selection.current_time.get_value().frame).zfill(8)

            file_name = f'{ duplicate_clip.name.get_value()}.{frame_name}.jpg'
            destination_path = os.path.join(exported_path, file_name)
            self.logger.debug(f"Thumbnail exported to {destination_path}")

            store['components'][component_name]['exported_path'] = destination_path

        finally:
            # Be sure to clean up duplicated clip in case of error during the export
            #
            flame.delete(duplicate_clip)


