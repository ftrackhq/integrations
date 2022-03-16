# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import os


def get_current_context_id():
    '''return an api object representing the current context.'''
    context_id = os.getenv(
        'FTRACK_CONTEXTID',
        os.getenv('FTRACK_TASKID', os.getenv('FTRACK_SHOTID')),
    )

    return context_id


def str_version(v, with_id=False, force_version_nr=None, delimiter='/'):
    return '{}/{}/{}/v{}{}'.format(
        v['task']['project']['name'],
        '/'.join(
            ['{}'.format(link['name']) for link in v['task']['link'][1:]]
        ),
        v['asset']['name'],
        force_version_nr or v['version'],
        ('({})'.format(v['id']) if with_id else ''),
    ).replace('/', delimiter)
