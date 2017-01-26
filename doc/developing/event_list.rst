..
    :copyright: Copyright (c) 2014 ftrack

.. _developing/event_list:

**********
Event list
**********

The following is a consolidated list of events published directly by this
plugin.

.. _event_list/ftrack.connect.nuke-studio.get-context-tags:

ftrack.connect.nuke-studio.get-context-tags
===========================================

Synchronous. Published to retrieve context tag configuration.::

    Event(
        topic='ftrack.connect.nuke-studio.get-context-tags'
    )

Expects returned data to be a list of tuples with each tuple of the form
``(tag_name, ftrack_entity_type, regular_expression)``::

    [
        ('episode', 'episode', 'EP(?P<value>\d+)'),
        ('sequence', 'sequence', 'SQ(?P<value>\d+)'),
        ('shot', 'shot', 'SH(?P<value>\d+)')
    ]

The regular expression **must** define a named group called ``value`` which will
be used as the value when the expression matches. The expression is used in a
search, so use anchors if appropriate for exact matches.

Multiple expressions can be defined in order by using the pipe (|) separator if
desired.

.. _event_list/ftrack.connect.nuke-studio.after-template-match:

ftrack.connect.nuke-studio.after-template-match
===============================================

Synchronous. Published to modify the generated structure of a template.::

    Event(
        topic='ftrack.connect.nuke-studio.after-template-match',
        data={
            'application_object': nuke_studio_track_item,
            'template': template,
            'structure': structure
        }
    )

Where *application_object* is a Nuke studio track item.

The *template* is the active template as described by
:ref:`event_list/ftrack.connect.nuke-studio.get-context-tags`.

*structure* is a list of dictionaries containing `name` and `object_type`. Where
`name` is the name of the entity that will be created and `object_type` is the
type of entity, e.g. Shot or Episode.

No returned data is expected.
