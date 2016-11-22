# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import pyblish.api
import tempfile


class ExtractNukeScriptComponent(pyblish.api.InstancePlugin):
    '''Create ftrack nukescript component if the used enabled it.'''

    order = pyblish.api.ExtractorOrder
    families = ['ftrack.nuke.script']

    def process(self, instance):
        '''Process *instance*.'''
        self.log.debug(
            'Started extracting nuke script {0!r}'.format(
                instance.name
            )
        )

        import nuke
        nuke_script_path = ''
        if nuke.Root().name() == 'Root':
            temporary_script_name = tempfile.NamedTemporaryFile(
                suffix='.nk', delete=True
            ).name
            nuke.scriptSaveAs(temporary_script_name)
            nuke_script_path = temporary_script_name
        else:
            nuke_script_path = nuke.root()['name'].value()

        new_component = {
            'path': nuke_script_path,
            'name': 'scene'
        }

        instance.data['ftrack_components'].append(new_component)
        self.log.debug(
            'Extracted {0!r} from {1!r}'.format(
                new_component, instance.name
            )
        )

pyblish.api.register_plugin(ExtractNukeScriptComponent)
