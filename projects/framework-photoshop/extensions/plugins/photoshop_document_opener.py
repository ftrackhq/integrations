# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_framework_photoshop.rpc_cep import PhotoshopRPCCEP


class PhotoshopDocumentOpenerPlugin(BasePlugin):
    name = 'photoshop_document_opener'

    def run(self, store):
        '''
        Expects collected_path in the <component_name> key of the given *store*,
        opens it in Photoshop and stores the result as 'open_result' under the
        <component_name> key of the given *store*.
        '''
        component_name = self.options.get('component')

        collected_path = store['components'][component_name].get(
            'collected_path'
        )

        if not collected_path:
            raise PluginExecutionError(f'No path provided to open!')

        if not os.path.exists(collected_path):
            raise PluginExecutionError(
                f'Document "{collected_path}" does not exist!'
            )

        try:
            # Get existing RPC connection instance
            photoshop_connection = PhotoshopRPCCEP.instance()

            self.logger.debug(
                f'Telling Photoshop to save document to: {collected_path}'
            )

            open_result = photoshop_connection.rpc(
                'openDocument',
                [collected_path],
            )

        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f'Exception telling Photoshop to open document: {e}'
            )

        if not open_result or isinstance(open_result, str):
            raise PluginExecutionError(
                f'Error opening the document in Photoshop: {open_result}'
            )

        store['components'][component_name]['open_result'] = open_result
