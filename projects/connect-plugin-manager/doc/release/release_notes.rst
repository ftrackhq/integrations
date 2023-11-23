
..
    :copyright: Copyright (c) 2021 ftrack

.. _release/release_notes:

*************
Release Notes
*************

.. release:: upcoming

    .. change:: changed

        Replaced setuptools with Poetry, use build tooling to produce Connect plugin.

    .. change:: fixed

        Proper error message if plugin installation fails or a plugin is missing.

    .. change:: added

        Support for platform specific plugin builds.

    .. change:: change

        Moved repository to monorepo package projects/connect-plugin-manager.

.. release:: 0.1.5
    :date: 2022-11-08

    .. change:: added

        Support semantic versioning precedence.

.. release:: 0.1.4
    :date: 2022-05-18

    .. change:: added
        :tags: Event
    
        Allow plugin to restart connect.

.. release:: 0.1.3
    :date: 2022-03-25

    .. change:: changed
        :tags: API

        Use ftrack_connect.qt module for pyside imports.

    .. change:: changed
        :tags: Event

        Emit new usage_events in batches.

    .. change:: changed
        :tags: Event

        Provide usage event with operating system in use.


.. release:: 0.1.2
    :date: 2022-03-08

    .. change:: changed
        :tags: Docs

        Fix and improve documentation.

    .. change:: fixed
        :tags: UX

        Installed plugins cannot be disabled from updating.

    .. change:: changed
        :tags: UX

        Installed plugins are grayed out.

    .. change:: changed
        :tags: UX

        Remove dashed borders and add label to explain install methods.


.. release:: 0.1.1
    :date: 2022-02-14

    .. change:: new
        :tags: Plugin

        Provide plugin manager connectWidget.

