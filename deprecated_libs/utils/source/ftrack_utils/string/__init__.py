# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import six


# TODO: double check when and if we use this and if it is really needed.
def str_context(context, delimiter='/'):
    '''Utility function to produce a human-readable describing *context*.'''
    if context is None:
        return None
    suffix = ''
    if context.entity_type == 'Asset':
        # Not really a context but attempt to support it anyway.
        suffix = '/{}'.format(context['name'])
        context = context['parent']
    elif not 'project' in context or not 'link' in context:
        # Do not know how to stringify this context
        return str(context)
    # Concatenate project, entity names down to context
    return '{}/{}{}'.format(
        context['project']['name'],
        '/'.join(['{}'.format(link['name']) for link in context['link'][1:]]),
        suffix,
    ).replace('/', delimiter)


# TODO: double check when and if we use this.
def str_version(
    assetversion,
    with_id=False,
    force_version_nr=None,
    by_task=True,
    delimiter='/',
):
    '''Utility function to produce a human-readable string out of *asset_version*.'''
    return '{}/{}/{}{}'.format(
        str_context(
            assetversion['task']
            if by_task
            else assetversion['asset']['parent']
        ),
        assetversion['asset']['name'],
        'v%d' % (force_version_nr or assetversion['version']),
        ('({})'.format(assetversion['id']) if with_id else ''),
    ).replace('/', delimiter)


# TODO: double check this utility and the usage of it.
def safe_string(object):
    '''Make a string out of *object*, by first decoding if byte or unicode string'''
    if six.PY2 and isinstance(object, unicode):
        return object.encode('utf-8')
    if isinstance(object, bytes):
        return object.decode("utf-8")
    return str(object)
