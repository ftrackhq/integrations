# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import os
import appdirs

from ftrack_connect_pipeline import constants as core_constants


def global_context(as_entity=False, session=None):
    '''Return the current global context (Task) id'''
    context_id = os.getenv(
        'FTRACK_CONTEXTID',
        os.getenv('FTRACK_TASKID', os.getenv('FTRACK_SHOTID')),
    )
    if as_entity is True:
        return session.query('Task where id is "{}"'.format(context_id)).one()
    else:
        return context_id


def str_context(context, with_id=False, force_version_nr=None, delimiter='/'):
    '''Utility function to produce a human readable string out or a context.'''
    return '{}/{}'.format(
        context['project']['name'],
        '/'.join(['{}'.format(link['name']) for link in context['link'][1:]]),
    ).replace('/', delimiter)


def str_version(v, with_id=False, force_version_nr=None, delimiter='/'):
    '''Utility function to produce a human readable string out or an asset version.'''
    return '{}/{}/v{}{}'.format(
        str_context(v['task']),
        v['asset']['name'],
        force_version_nr or v['version'],
        ('({})'.format(v['id']) if with_id else ''),
    ).replace('/', delimiter)


def get_snapshot_save_path(context_id, session, extension=None):
    '''Calculate the path to local snapshot save (work path), DCC independent.'''

    result = False
    message = None

    context = session.query(
        'Context where id={}'.format(context_id or global_context())
    ).first()

    if context is None:
        raise Exception(
            'Could not save snapshot - unknown context: {}!'.format(context_id)
        )

    snapshot_path_base = os.environ.get('FTRACK_SNAPSHOT_PATH')
    if snapshot_path_base is None:
        server_folder_name = (
            session.server_url.split('//')[-1].split('.')[0].replace('-', '_')
        )
        snapshot_path_base = os.path.join(
            appdirs.user_data_dir('ftrack-connect', 'ftrack'),
            core_constants.SNAPSHOT_COMPONENT_NAME,
            server_folder_name,
        )

    # Try to query location system (future) for getting task path
    try:
        location = session.pick_location()
        snapshot_path = os.path.join(
            snapshot_path_base, location.get_filesystem_path(context)
        )
    except:
        structure_names = [context['project']['name']] + [
            item['name'] for item in context['link'][1:]
        ]

        # Build path down to context
        snapshot_path = os.sep.join([snapshot_path_base] + structure_names)

    if snapshot_path is not None:
        if not os.path.exists(snapshot_path):
            os.makedirs(snapshot_path)
        if not os.path.exists(snapshot_path):
            return (
                None,
                'Could not create snapshot directory: {}!'.format(
                    snapshot_path
                ),
            )

        # Find latest version number
        next_version_number = 1
        latest_asset_version = session.query(
            'AssetVersion where '
            'task.id={} and is_latest_version=true'.format(context_id)
        ).first()
        if latest_asset_version:
            next_version_number = latest_asset_version['version'] + 1

        # TODO: use task type <> asset type mappings
        filename = context['type']['name']  # Modeling, compositing...

        # Make sure we do not overwrite existing work done
        snapshot_path = os.path.join(
            snapshot_path, '%s_v%03d' % (filename, next_version_number)
        )

        while os.path.exists(snapshot_path) or (
            extension
            and os.path.exists('{}{}'.format(snapshot_path, extension))
        ):
            next_version_number += 1
            snapshot_path = os.path.join(
                os.path.dirname(snapshot_path),
                '%s_v%03d' % (filename, next_version_number),
            )

        result = snapshot_path
    else:
        message = 'Could not evaluate local snapshot path!'

    return result, message
