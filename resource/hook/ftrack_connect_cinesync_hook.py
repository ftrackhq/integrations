# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import subprocess
import sys

import ftrack_api
import ftrack_connect.application
from ftrack_action_handler.action import BaseAction


class CinesyncActionLauncher(BaseAction):
    '''Cinesync launch action.'''

    identifier = 'ftrack-connect-cinesync-application'
    label = 'cineSync'

    def __init__(self, applicationStore, session):
        '''Initialise action with *applicationStore*.

        *applicationStore* should be an instance of
        :class:`ftrack_connect.application.ApplicationStore`.

        '''
        super(CinesyncActionLauncher, self).__init__(session=session)

        self.applicationStore = applicationStore

        self.allowed_entity_types_fn = {
            'list': self._get_version_from_lists,
            'assetversion': self._get_version,
            'reviewsession': self._get_version_from_review
        }

    def _get_version(self, entity_id):
        '''Return a single *entity_id* from version'''
        return [entity_id]

    def _get_version_from_lists(self, entity_id):
        '''Return list of version ids from AssetVersionList from *entity_id*'''

        asset_version_lists = self._session.query(
            'AssetVersionList where id is {0}'.format(entity_id)
        ).one()

        result = [
            version['id'] for version in asset_version_lists['items']
        ]

        return result

    def _get_version_from_review(self, entity_id):
        '''Return list of versions ids from ReviewSession from *entity_id*'''

        review_session = self._session.query(
            'select review_session_objects.version_id'
            ' from ReviewSession where id is {0}'.format(entity_id)
        ).one()

        result = []
        for version_object in review_session['review_session_objects']:
            result.append(version_object['version_id'])

        return result

    def is_valid_selection(self, selection):
        '''Check whether the given *selection* is valid'''
        results = []

        for selected_item in selection:
            allowed_entity_types = self.allowed_entity_types_fn.keys()
            if selected_item.get('entityType') in allowed_entity_types:
                results.append(selected_item)

        return results

    def get_versions(self, selection):
        '''Return versions given the *selection*'''
        results = []

        for selected_item in selection:
            entity_type = selected_item.get('entityType')
            entity_id = selected_item.get('entityId')
            version_id_fn = self.allowed_entity_types_fn[entity_type]
            versions = version_id_fn(entity_id)
            results.extend(versions)

        return results

    def get_selection(self, event):
        '''From a raw *event* dictionary, extract the selected entities.'''

        data = event['data']
        selection = data.get('selection', [])
        return selection

    def discover(self, session, entities, event):
        '''Return true if we can handle the selected entities.

        *session* is a `ftrack_api.Session` instance

        *entities* is a list of tuples each containing the entity type and the
        entity id. If the entity is a hierarchical you will always get the
        entity type TypedContext, once retrieved through a get operation you
        will have the "real" entity type ie. example Shot, Sequence
        or Asset Build.

        *event* the unmodified original event'''

        selection = self.get_selection(event)
        if not selection:
            self.logger.debug(
                'No entity selected.'
            )
            return False

        if not self.is_valid_selection(selection):
            valid_types = self.allowed_entity_types_fn.keys()
            self.logger.warning(
                'No valid entity type selected. Valid types: {0}.'.format(
                    ', '.join(valid_types)
                )
            )
            return False

        applications = self.applicationStore.applications
        applications = sorted(
            applications, key=lambda application: application['label']
        )

        self.variant = applications[0].get('variant', None)
        return True

    def open_url(self, asset_version_list):
        ''' Open cinesync url with given *asset_version_list*'''
        url = 'cinesync://ftrack/addVersion?assetVersionList={0}'.format(
            ','.join(asset_version_list)
        )

        self.logger.debug('Opening Cynesinc Url: {0}'.format(url))

        if sys.platform == 'darwin':
            subprocess.call(['open', url])

        elif sys.platform == 'win32':
            subprocess.call(['cmd', '/c', 'start', '', '/b', url])

        elif sys.platform == 'linux2':
            subprocess.call(['xdg-open', url])

    def launch(self, session, entities, event):
        '''Callback method for the action.

        *session* is a `ftrack_api.Session` instance

        *entities* is a list of tuples each containing the entity type and the
        entity id. If the entity is a hierarchical you will always get the
        entity type TypedContext, once retrieved through a get operation you
        will have the "real" entity type ie. example Shot, Sequence
        or Asset Build.

        *event* the unmodified original event

        '''
        # Prevent further processing by other listeners.
        event.stop()
        versions = self.get_versions(event['data']['selection'])
        self.open_url(versions)


class CinesyncApplicationStore(ftrack_connect.application.ApplicationStore):
    '''Discover and store available applications on this host.'''

    def _discoverApplications(self):
        '''Return list of applications that can be launched from this host.'''
        applications = []

        if sys.platform == 'darwin':
            prefix = ['/', 'Applications']

            applications.extend(self._searchFilesystem(
                expression=prefix + ['cineSync.app'],
                label='cineSync',
                applicationIdentifier='cineSync',
                icon='cinesync',
                versionExpression=r'(?P<version>.*)'
            ))

        elif sys.platform == 'win32':
            prefix = ['C:\\', 'Program Files.*']

            applications.extend(self._searchFilesystem(
                expression=prefix + ['cineSync', 'cineSync.exe'],
                label='cineSync',
                applicationIdentifier='cineSync',
                icon='cinesync'
            ))

        elif sys.platform == 'linux2':
            # TODO: Find consistent way to decide where the application is
            # installed. Placeholder for linux
            return

        self.logger.debug('Application found: {0}'.format(applications))
        return applications


def register(session, **kw):
    '''Register hooks for ftrack connect cinesync plugins.'''

    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return

    applicationStore = CinesyncApplicationStore()
    # Create action and register to respond to discover and launch events.
    action = CinesyncActionLauncher(applicationStore, session)
    action.register()
