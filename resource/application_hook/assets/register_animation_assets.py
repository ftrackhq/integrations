# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import ftrack_api
from ftrack_connect_pipeline import constants


def register_asset(event):
    return {
        'asset_name': 'Animation',
        'asset_type': 'anim',
        'context': ['Task'],
        'publish': {
            'plugins' : [
                {
                    'context': [
                        {
                            'name' : 'Set Context',
                            'widget': 'context.publish',
                            'plugin':'context.publish',
                            'options': {'context_id': None, 'asset_name': None},
                            'description': 'Set context where to publish to'
                        }
                    ]
                },
                {
                    'collectors': [
                        {
                            'name' : 'From Maya Set',
                            'plugin':'from_set.maya',
                            'options': {'set_name': 'geometry'},
                            'description': 'collect all the geometry in maya set with the given name.'
                        }
                    ]
                },
                {
                    'validators': [
                        {
                            'name' : 'Is not empty',
                            'plugin': 'nonempty',
                            'description': 'check whether the result of collection is not empty.'

                        }
                    ]
                },
                {
                    'extractors': [
                        {
                            'name' : 'Save as Maya Ascii',
                            'plugin': 'to_tmp.maya.ma',
                            'options': {'component_name': 'mayaAscii'},
                            'description': 'Save an .ma file in /tmp'

                        },
                        {
                            'name' : 'Save as Maya Binary',
                            'plugin': 'to_tmp.maya.mb',
                            'options': {'component_name': 'mayaBinary'},
                            'description': 'Save an .mb file in /tmp'

                        }
                    ]
                },
                {
                    'publishers': [
                        {
                            'name' : 'Publish to ftrack',
                            'plugin': 'result',
                            'description': 'publish the result files to ftrack.',
                            'visible': False
                        }
                    ]
                }
            ]
        },
        'load': {
            'plugins': [
               {
                    'context': [
                        {
                            'widget': 'context.load',
                            'plugin':'context.load',
                            'name' : 'Context ',
                            'options': {'component_list': None, 'accepts':['.ma', '.mb']},
                            'description': 'Set context where to load from to'
                        }
                    ]
               },
               {
                    'importers': [
                        {
                            'name' : 'Import file',
                            'plugin':'maya',
                            'description': 'import Ma file',
                            'visible': None
                        }
                    ]
               }
            ]
        }
    }


def register(api_object, **kw):
    '''Register plugin to api_object.'''

    # Validate that api_object is an instance of ftrack_api.Session. If not,
    # assume that _register_assets is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    api_object.event_hub.subscribe(
        'topic={}'.format(constants.REGISTER_ASSET_TOPIC),
        register_asset
    )
