# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import tempfile

import maya.cmds as cmd
import maya

from ftrack_connect_pipeline_3dsmax import plugin


class ExtractMaxAsciiPlugin(plugin.ExtractorMaxPlugin):
    plugin_name = 'mayaascii'

    def run(self, context=None, data=None, options=None):

        def call(component_name):
            new_file_path = tempfile.NamedTemporaryFile(delete=False, suffix='.ma').name
            self.logger.debug('Calling extractor options: data {}'.format(data))
            cmd.select(data, r=True)
            cmd.file(rename=new_file_path)
            cmd.file(save=True, type='mayaAscii')
            return {component_name: new_file_path}

        component_name = options['component_name']
        return maya.utils.executeInMainThreadWithResult(call, component_name)


def register(api_object, **kw):
    plugin = ExtractMayaAsciiPlugin(api_object)
    plugin.register()
