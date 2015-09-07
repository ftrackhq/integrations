# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack

def get(item):
    '''Return ftrack entity reference for item.

    Will return `None` if no entity reference found on item.

    '''
    # Inline to avoid circular import.
    import hiero

    _item = item

    identifier = None
    entity_type = None

    if isinstance(_item, hiero.core.TrackItem):
        _item = item.source()

    if isinstance(_item, hiero.core.Clip):
        for tag in _item.tags():
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
    '''Set *entity* as reference on *item*.'''
    # Inline to avoid circular import.
    import hiero

    _item = item

    if isinstance(_item, hiero.core.TrackItem):
        _item = item.source()

    if isinstance(_item, hiero.core.Clip):
        tag = hiero.core.Tag('ftrack.entity_reference')
        tag.metadata().setValue('ftrack.identifier', entity.getId())
        tag.metadata().setValue('ftrack.entity_type', entity._type)
        _item.addTag(tag)
    else:
        raise ValueError(
            'Unsupported item type. Needs to be `hiero.core.Clip`'
        )