# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack


from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class {{ cookiecutter.integration_name.capitalize() }}ThumbnailExporterPlugin(BasePlugin):
    name = '{{ cookiecutter.integration_name }}_thumbnail_exporter'

    def run(self, store):
        '''
        Create a screenshot from the selected camera given in the *store*.
        Save it to a temp file and this one will be published as thumbnail.
        '''
        component_name = self.options.get('component')

        thumbnail_path = None
        try:
            # TODO: thumbnail_path = Export thumbnail

            self.logger.debug(f"Thumbnail has been saved to: {thumbnail_path}.")
        except Exception as error:
            raise PluginExecutionError(message=error)

        store['components'][component_name]['exported_path'] = thumbnail_path
