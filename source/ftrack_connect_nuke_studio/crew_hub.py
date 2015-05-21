# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import getpass

import ftrack
import ftrack_connect.crew_hub


class CrewHub(ftrack_connect.crew_hub.SignalCrewHub):

    def __init__(self, *args, **kwargs):
        '''Instantiate CrewHub.'''
        super(CrewHub, self).__init__(*args, **kwargs)

        user = ftrack.getUser(getpass.getuser())
        self.enter({
            'user': {
                'name': user.getName(),
                'id': user.getId()
            },
            'application': {
                'identifier': 'nuke_studio',
                'label': 'Nuke {0}'.format('Studio')
            },
            'context': {
                'project_id': 'my_project_id',
                'containers': []
            }
        })

    def isInterested(self, data):
        '''Return if interested in user with *data*.'''

        # In first version we are interested in all users since all users
        # are visible in the list.
        return True

# Create global crew hub which can connect before UI is created.
_crew_hub = CrewHub()
