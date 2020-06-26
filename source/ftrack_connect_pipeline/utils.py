# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import os

def get_current_context():
    '''return an api object representing the current context.'''
    context_id = os.getenv(
        'FTRACK_CONTEXTID',
            os.getenv('FTRACK_TASKID',
                os.getenv('FTRACK_SHOTID'
            )
        )
    )

    return context_id

