# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import subprocess
import os
import getpass
import sys
import pprint
import logging
import platform

import ftrack_api
import ftrack_connect.application


class LaunchAction(object):
    '''ftrack connect legacy plugins discover and launch action.'''

    identifier = 'ftrack-connect-cinesync-application'

    def __init__(self, applicationStore, launcher, session):
        '''Initialise action with *applicationStore* and *launcher*.

        *applicationStore* should be an instance of
        :class:`ftrack_connect.application.ApplicationStore`.

        *launcher* should be an instance of
        :class:`ftrack_connect.application.ApplicationLauncher`.

        '''
        super(LaunchAction, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.applicationStore = applicationStore
        self.launcher = launcher
        self.session = session
        self.allowed_entity_types_fn = {
            'list': self._get_version_from_lists,
            'assetversion': self._get_version,
            'reviewsession': self._get_version_from_review
        }

    def _get_version(self, entity_id):
        '''Return a single entity_id from version'''
        return entity_id

    def _get_version_from_lists(self, entity_id):
        '''Return comma separated list of versions from AssetVersionList'''

        asset_version_lists = self.session.query(
            'AssetVersionList where id is {0}'.format(entity_id)
        ).one()
        
        result = [
            version['id'] for version in asset_version_lists['items'] if version
        ]

        return ','.join(result)

    def _get_version_from_review(self, entity_id):
        '''Return comma separated list of versions from ReviewSession'''

        review_session = self.session.query(
            'select review_session_objects.version_id'
            ' from ReviewSession where id is {0}'.format(entity_id)
        ).one()

        result = [
            version_object['version_id'] for version_object in review_session['review_session_objects'] if version_object
        ]

        return ','.join(result)

    def register(self):
        '''Override register to filter discover actions on logged in user.'''

        self.session.event_hub.subscribe(
            'topic=ftrack.action.discover and source.user.username={0}'.format(
                self.session.api_user
            ),
            self.discover
        )

        self.session.event_hub.subscribe(
            'topic=ftrack.action.launch and source.user.username={0} '
            'and data.actionIdentifier={1}'.format(
                self.session.api_user, self.identifier
            ),
            self.launch
        )

    def is_valid_selection(self, selection):
        '''Check whether the given *selection* is valid'''
        results = []

        for selected_item in selection:
            allowed_entity_types = self.allowed_entity_types_fn.keys()
            if selected_item.get('entityType') in allowed_entity_types:
                results.append(selected_item)

        return results

    def get_versions(self, selection):
        '''Return versions given the selection'''
        results = []

        for selected_item in selection:
            entity_type = selected_item.get('entityType')
            entity_id = selected_item.get('entityId')
            version_id_fn = self.allowed_entity_types_fn[entity_type]
            versions = version_id_fn(entity_id)
            results.append(versions)

        return results

    def get_selection(self, event):
        '''From a raw event dictionary, extract the selected entities.

        :param event: Raw ftrack event
        :type event: dict
        :returns: List of entity dictionaries
        :rtype: List of dict'''

        data = event['data']
        selection = data.get('selection', [])
        return selection

    def discover(self, event):
        '''Return discovered applications.'''

        selection = self.get_selection(event)
        if not selection:
            return

        if not self.is_valid_selection(selection):
            return

        items = []
        applications = self.applicationStore.applications

        applications = sorted(
            applications, key=lambda application: application['label']
        )

        for application in applications:
            applicationIdentifier = application['identifier']
            label = application['label']
            items.append({
                'actionIdentifier': self.identifier,
                'label': label,
                'variant': application.get('variant', None),
                'description': application.get('description', None),
                'icon': application.get('icon', 'default'),
                'applicationIdentifier': applicationIdentifier
            })

        return {
            'items': items
        }

    def open_url(self, asset_version_list):
        ''' Open cinesync url with given *asset_version_list*'''

        asset_version_list_string = ','.join(asset_version_list)
        url = 'cinesync://ftrack/addVersion?assetVersionList={0}'.format(
            asset_version_list_string
        )

        try:
            system = platform.system()
        except Exception:
            system = os.uname()[0]

        if system == 'Darwin':
            subprocess.call(['open', url])

        elif system == 'Windows':
            subprocess.call(['cmd', '/c', 'start', '', '/b', url])

        elif system == 'Linux':
            subprocess.call(['xdg-open', url])

    def launch(self, event):
        '''Handle *event*.

        event['data'] should contain:

            *applicationIdentifier* to identify which application to start.

        '''
        # Prevent further processing by other listeners.
        event.stop()
        versions = self.get_versions(event['data']['selection'])
        self.open_url(versions)


class ApplicationStore(ftrack_connect.application.ApplicationStore):
    '''Discover and store available applications on this host.'''

    def _discoverApplications(self):
        '''Return a list of applications that can be launched from this host.

        An application should be of the form:

            dict(
                'identifier': 'name_version',
                'label': 'Name',
                'variant': 'version',
                'description': 'description',
                'path': 'Absolute path to the file',
                'version': 'Version of the application',
                'icon': 'URL or name of predefined icon'
            )

        '''
        applications = []

        if sys.platform == 'darwin':
            prefix = ['/', 'Applications']

            applications.extend(self._searchFilesystem(
                expression=prefix + ['cineSync.app'],
                label='cineSync',
                applicationIdentifier='cineSync',
                icon='cineSync'
            ))

        elif sys.platform == 'win32':
            prefix = ['C:\\', 'Program Files.*']

            applications.extend(self._searchFilesystem(
                expression=prefix + ['cineSync', 'cineSync.exe'],
                label='cineSync',
                applicationIdentifier='cineSync',
                icon='cineSync'
            ))
        return applications


def register(session, **kw):
    '''Register hooks for ftrack connect cinesync plugins.'''

    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return

    applicationStore = ApplicationStore()

    launcher = ftrack_connect.application.ApplicationLauncher(applicationStore)

    # Create action and register to respond to discover and launch events.
    action = LaunchAction(applicationStore, launcher, session)
    action.register()
