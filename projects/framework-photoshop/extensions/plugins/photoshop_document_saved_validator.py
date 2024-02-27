# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import (
    PluginExecutionError,
    PluginValidationError,
)

from ftrack_framework_photoshop.rpc_cep import PhotoshopRPCCEP


class PhotoshopDocumentSavedValidatorPlugin(BasePlugin):
    '''
    Plugin to validate if the Photoshop document has been saved.
    '''

    name = 'photoshop_document_saved_validator'

    def save_document_to_temp(self, store, extension_format):
        '''
        Save the current Photoshop document.
        '''

        # Get existing RPC connection instance
        photoshop_connection = PhotoshopRPCCEP.instance()

        self.logger.warning('Photoshop document not saved, asking to save')
        temp_path = get_temp_path(filename_extension=extension_format)
        save_result = photoshop_connection.rpc('saveDocument', [temp_path])
        # Will return a boolean containing the result.
        if not save_result or isinstance(save_result, str):
            raise PluginExecutionError(
                f'An error occurred while saving the'
                f' document: {save_result}'
            )
        elif save_result:
            self.logger.info('Document saved successfully')

        component_name = self.options.get('component', 'main')
        store['components'][component_name]['document_name'] = temp_path
        store['components'][component_name]['document_saved'] = True
        store['components'][component_name]['valid_file'] = True

    def run(self, store):
        '''
        Run the validation process for the Photoshop document.
        '''
        component_name = self.options.get('component', 'main')
        document_name = store['components'][component_name].get(
            'document_name'
        )
        extension_format = store['components'][component_name].get(
            'extension_format'
        )
        document_saved = store['components'][component_name].get(
            'document_saved'
        )

        if (
            not document_saved
            or not document_name
            or not os.path.exists(document_name)
        ):
            # Document is not saved or path not found, save it first.
            self.logger.warning('Photoshop document has never been saved.')
            raise PluginValidationError(
                message='Photoshop document has never been saved, Click fix to '
                'save it to a temp file',
                on_fix_callback=self.save_document_to_temp,
                fix_kwargs={'extension_format': extension_format},
            )
        elif not document_name.lower().endswith(extension_format.lower()):
            self.logger.warning(
                f'Photoshop document saved in wrong format, '
                f're-saving as {extension_format}'
            )
            raise PluginValidationError(
                message=f'Photoshop document saved in wrong format, Click fix to '
                f'save it to a {extension_format} temp file',
                on_fix_callback=self.save_document_to_temp,
                fix_kwargs={'extension_format': extension_format},
            )

        self.logger.debug("Document is saved validation passed.")
        store['components'][component_name]['valid_file'] = True
