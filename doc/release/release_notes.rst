..
    :copyright: Copyright (c) 2022 ftrack

.. _release/release_notes:

*************
Release Notes
*************

.. release:: 1.2.0
    :date: 2023-04-05

    .. change:: fix
        :tags: asset manager

         Fixed bug when a version could not be changed on an unloaded asset.

    .. change:: new
        :tags: doc

        Added user documentation, available from ftrack menu.

    .. change:: change
        :tags: publisher

         Enhanced image sequence and movie publisher UI - migrated options from exporter to collector.

    .. change:: fix
        :tags: publisher

         Fixed Nuke 14 publish render bug.

    .. change:: changed
        :tags: definitions

        Remove ftrack-connect-pipeline-definitions repository.
        Add plugins and definitions on each integration.

.. release:: 1.1.0
    :date: 2022-11-08


    .. change:: fixed

        Fix unsubscribe_client_context_change exception.


    .. change:: fixed

        Fixed bug were Nuke log viewer and documentation was not working.


    .. change:: fixed

        Prevented multiple docked publishers and asset managers.


    .. change:: fixed

        Frame range not updating on launch.


    .. change:: fixed

        Remove event hub disconnect, aligned menu and reordered asset manager engine functions.


.. release:: 1.0.1
    :date: 2022-08-01

    .. change:: new

        Initial release

