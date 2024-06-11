# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_core.plugin import BasePlugin


class ResolveEntityPathsPlugin(BasePlugin):
    name = 'resolve_entity_paths'

    def run(self, store):
        '''
        Load the entities, resolve their paths and store them in the given *store*
        '''
        import nuke

        nuke.tprint(self.options)
