# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack


from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class {{ cookiecutter.plugin_name.capitalize() }}ThumbnailExporterPlugin(BasePlugin):
    name = '{{ cookiecutter.plugin_name }}_thumbnail_exporter'

    def run(self, store):
        '''
        Create a screenshot from the selected camera given in the *store*.
        Save it to a temp file and this one will be published as thumbnail.
        '''
        component_name = self.options.get('component')

        # Export thumbnail

        store['components'][component_name]['exported_path'] = thumbnail_path
