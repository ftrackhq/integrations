..
    :copyright: Copyright (c) 2022 ftrack

.. _release/release_notes:

*************
Release Notes
*************

.. release:: upcoming

    .. change:: changed

        Use Poetry as build infrastructure instead of setuptools

    .. change:: changed

        Optimised Assembler/loader with optimised query projections

    .. change:: fix

        Optimised Opener query projections

   .. change:: fix

        Align assembler UI, consolidated assembler widget module.
        Consolidated asset manager widget module.
        Added docstrings.
        Updated progress widget UI, consolidated batch progress widget.
        Updated accordion base checked and checkable attributes.
        Improved asset and version selector.
        Updated definition selector to support adding an empty definition or not.

    .. change:: changed
        :tags: definitions

        Remove ftrack-connect-pipeline-definitions repository.
        Add plugins and definitions on each integration.

    .. change:: fix

        Added spacer to option widget overlays.
        (Base collector widget) Make sure initial collected objects are picked up.

    .. change:: fix

        Fixed list alternate style bug.

    .. change:: fix

        Have context selector support not only tasks, and start on browsing on a given context.
        Have context selector disable thumbnail load.

.. release:: 1.2.0
    :date: 2022-12-15

    .. change:: new

        3ds Max integration - Disable multithreading for certain DCCs, Added scroll widget to publisher overlay for large option sets.

.. release:: 1.1.0
    :date: 2022-11-08

    .. change:: fix
        :tags: opener

        Error on changing opener asset version to/from a non compatible.

    .. change:: new
        :tags: houdini

        Houdini integration.

    .. change:: fix
        :tags: publisher,assembler,opener

        Updated progress widget style and appearance of finalizer section.

    .. change:: change
        :tags: publisher,assembler,opener

        Use core pipeline DefinitionObject API instead of raw definition dictionary operations.

    .. change:: fixed
        :tags: dynamicwidget

        Fixed bug where default plugin option list item were not selected.

    .. change:: change
        :tags: assembler

        Have assembler start in browse mode instead of suggestions.

    .. change:: change
        :tags: dynamicwidget

        Finalised Dynamic widget . list / combobox handling.

    .. change:: change
        :tags: dynamicwidget

        Dynamic widget renders widgets within a group box instead of using the default redundant plugin widget label.

    .. change:: change
        :tags: overlay

        Updated the visual appearance of options overlay, removed accordion use.

    .. change:: fixed
        :tags: overlay

        Fixed further overlay event filter warnings.

    .. change:: fixed
        :tags: context

        Align with changes in pipeline context workflow.

    .. change:: fixed

        Removed event filter warnings in Nuke and Maya.

    .. change:: fixed

        Fixed assembler version selector bug caused by previous opener changes.

    .. change:: fixed
        :tags: doc

        Fixed bug where opener definition selector could not spot an openable version.

    .. change:: change

         Removed version id from asset list event.

    .. change:: change

        Passing version ID from version selection instead of Version API object

    .. change:: change

        Prevent opener from listing and opening incompatible snapshots

.. release:: 1.0.1
    :date: 2022-08-01

    .. change:: new

        Initial release

