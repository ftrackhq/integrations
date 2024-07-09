# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os.path
import shutil

import clique

from ftrack_framework_core.plugin import BasePlugin
from ftrack_utils.paths import get_temp_path


class RenameExporterPlugin(BasePlugin):
    name = 'rename_file_exporter'

    def check_collection(self, path):
        '''
        Check if the given *path* is a collection.
        '''
        try:
            collection = clique.parse(path)
        except Exception as error:
            self.logger.debug(f"{path} is not a collection.")
            return False
        self.logger.debug(f"{path} is a collection.")
        return collection

    def rename(self, origin_path, destination_path):
        '''
        Rename the given *origin_path* to *destination_path*
        '''
        # Pick file extension from origin_path
        no_extension_path, extension_format = os.path.splitext(origin_path)
        # Pick file base name from origin_path
        base_name = os.path.basename(no_extension_path)

        if not destination_path:
            destination_path = get_temp_path(
                filename_extension=extension_format
            )

        if os.path.isdir(destination_path):
            destination_path = os.path.join(
                destination_path, base_name + extension_format
            )

        return shutil.copy(origin_path, destination_path)

    def run(self, store):
        '''
        Expects collected_path in the <component_name> key of the given *store*
        and an export_destination from the :obj:`self.options`.
        '''
        component_name = self.options.get('component')

        collected_path = store['components'][component_name]['collected_path']
        export_destination = self.options.get('export_destination')
        if export_destination:
            export_destination = os.path.expanduser(export_destination)

        collection = self.check_collection(collected_path)

        if collection:
            new_location = []
            for file_path in collection:
                if export_destination and not os.path.isdir(
                    export_destination
                ):
                    export_destination = os.path.dirname(export_destination)
                if not export_destination:
                    export_destination = get_temp_path(is_directory=True)
                new_location.append(self.rename(file_path, export_destination))
                self.logger.debug(
                    f"Copied {collected_path} to {export_destination}."
                )
            collections, remainder = clique.assemble(new_location)
            store['components'][component_name]['exported_path'] = collections[
                0
            ].format()
        else:
            store['components'][component_name]['exported_path'] = self.rename(
                collected_path, export_destination
            )
            self.logger.debug(
                f"Copied {collected_path} to {export_destination}."
            )
