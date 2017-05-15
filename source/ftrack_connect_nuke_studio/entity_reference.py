# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack_api

from ftrack_connect.session import (
    get_shared_session
)

session = get_shared_session()

def translate_from_legacy_entity_types(entity_type):
    '''Return translated entity type tht can be used with the new API.'''


    for schema in session.schemas:
        alias_for = schema.get('alias_for')

        if (
            alias_for and isinstance(alias_for, basestring) and
            alias_for.lower() == entity_type
        ):
            return schema['id']

    for schema in session.schemas:
        if schema['id'].lower() == entity_type:
            return schema['id']

    return entity_type


def translate_to_legacy_entity_type(entity_type):
    for schema in session.schemas:
        if schema['id'] != entity_type:
            continue

        alias_for = schema.get('alias_for')

        if alias_for and isinstance(alias_for, dict):
            return alias_for.get('id')

    return entity_type

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

    if None not in (entity_type, identifier):
        return session.get(
            translate_from_legacy_entity_types(entity_type), identifier
        )



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
        entity_id = entity.get('id')
        entity_type = entity.entity_type

    if isinstance(item, hiero.core.TrackItem):
        entity_type = translate_from_legacy_entity_types(
            entity_type
        )

        for _tag in item.tags()[:]:
            if _tag.name() == 'ftrack.entity_reference':
                item.removeTag(_tag)

        tag = hiero.core.Tag('ftrack.entity_reference')

        tag.metadata().setValue('ftrack.identifier', entity_id)
        tag.metadata().setValue('ftrack.entity_type', entity_type)
        tag.setVisible(False)

        item.addTag(tag)

    else:
        raise TypeError(
            'Unsupported item type. Needs to be `hiero.core.TrackItem`'
        )