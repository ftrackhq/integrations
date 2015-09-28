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


def set(item, entity=None, entity_id=None, entity_type=None):
    '''Set entity reference on *item*.

    Either accepts *entity* of type :py:class:`ftrack.Task` or an
    *entity_id* and *entity_type*.

    Raise :exc:`TypeError` if *item* is not of type `hiero.core.TrackItem`.

    Raise :exc:`ValueError` if not *entity* or *entity_id* and *entity_type*
    are specified.

    '''
    # Inline to avoid circular import.
    import hiero

    if entity is None and entity_id is None and entity_type is None:
        raise ValueError(
            'Need to specify either *entity* or *entity_type* and *entity_id*.'
        )

    if entity:
        entity_id = entity.getId()

        # Use private `_type` since `entityType` not supported on
        # ftrack.AssetVersion.
        entity_type = entity._type

    if isinstance(item, hiero.core.TrackItem):
        tag = None
        for _tag in item.tags():
            if _tag.name() == 'ftrack.entity_reference':
                tag = _tag
                break

        if not tag:
            tag = hiero.core.Tag('ftrack.entity_reference')
            item.addTag(tag)

        tag.metadata().setValue('ftrack.identifier', entity_id)
        tag.metadata().setValue('ftrack.entity_type', entity_type)
        tag.setVisible(False)
    else:
        raise TypeError(
            'Unsupported item type. Needs to be `hiero.core.TrackItem`'
        )
