# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack

def get(item):
    '''Return ftrack entity reference for item.

    Will return `None` if no entity reference found on item.

    '''
    # Inline to avoid circular import.
    import hiero

    identifier = None
    entity_type = None

    if isinstance(item, hiero.core.TrackItem):
        for tag in item.tags():
            if (
                tag.name() == 'ftrack.entity_reference'
                and tag.metadata().hasKey('ftrack.identifier')
                and tag.metadata().hasKey('ftrack.entity_type')
            ):
                identifier = tag.metadata().value('ftrack.identifier')
                entity_type = tag.metadata().value('ftrack.entity_type')

    entity = None
    if entity_type == 'component':
        entity = ftrack.Component(identifier)

    elif entity_type == 'asset_version':
        entity = ftrack.AssetVersion(identifier)

    elif entity_type == 'asset':
        entity = ftrack.Asset(identifier)

    elif entity_type == 'show':
        entity = ftrack.Project(identifier)

    elif entity_type == 'task':
        entity = ftrack.Task(identifier)

    return entity


def set(item, entity):
    '''Set *entity* as reference on *item*.

    Raise :exc:`TypeError` if *item* is not of type `hiero.core.TrackItem`.

    '''
    # Inline to avoid circular import.
    import hiero

    if isinstance(item, hiero.core.TrackItem):
        tag = hiero.core.Tag('ftrack.entity_reference')
        tag.metadata().setValue('ftrack.identifier', entity.getId())
        tag.metadata().setValue('ftrack.entity_type', entity._type)
        tag.setVisible(False)
        item.addTag(tag)
    else:
        raise TypeError(
            'Unsupported item type. Needs to be `hiero.core.TrackItem`'
        )