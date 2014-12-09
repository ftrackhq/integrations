# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import re
import functools

import FnAssetAPI

import ftrack

import ftrack_connect_foundry.bridge
import ftrack_connect_hiero.event


class Bridge(ftrack_connect_foundry.bridge.Bridge):
    '''Bridging functionality between core API's.'''

    def _registerEventHandlers(self):
        '''Register appropriate event handlers.'''
        super(Bridge, self)._registerEventHandlers()

        eventManager = FnAssetAPI.Events.getEventManager()
        eventManager.registerListener(
            'hieroToNukeScriptAddClip',
            functools.partial(
                ftrack_connect_hiero.event.hieroToNukeAddClip, self
            )
        )
        eventManager.registerListener(
            'hieroToNukeScriptAddWrite',
            functools.partial(
                ftrack_connect_hiero.event.hieroToNukeAddWrite, self
            )
        )
        eventManager.registerListener(
            'entityReferencesFromNukeNodes',
            functools.partial(
                ftrack_connect_hiero.event.refsFromNukeNodes, self
            )
        )

    def _conformPath(self, path):
        '''Return *path* processed for use by current host.'''
        # Convert sequence format to one understood by Hiero.
        return re.sub('(#+)', self._convertHashes, path)

    def _convertHashes(self, match):
        '''Return hashes as %0d expression.'''
        return '%0{0}d'.format(len(match.group(0)))

    def getEntityDisplayName(self, entityRef, context):
        '''Return human readable name for entity referenced by *entityRef*.'''
        name = ''

        if context and context.locale:
            if context.locale.isOfType('clip'):
                entity = self.getEntityById(entityRef)

                if isinstance(entity, ftrack.Component):
                    # Hiero is sensitive to names so it should just be the
                    # name of the asset
                    asset = entity.getParent().getAsset()
                    name = asset.getName()

        if not name:
            name = super(Bridge, self).getEntityDisplayName(entityRef, context)

        return name
