..
    :copyright: Copyright (c) 2022 ftrack

.. _release/release_notes:

*************
Release Notes
*************

.. release:: upcoming

    .. change:: new
        :tags: doc

        Added user documentation, available from ftrack menu.

    .. change:: fix

        Fixed UI bugs in Alembic and FBX exporter.
        Added frame range and take options to FBX exporter, enabling export of animations.
        Displays collected camera in exporters.

    .. change:: changed
        :tags: definitions

        Remove ftrack-connect-pipeline-definitions repository.
        Add plugins and definitions on each integration.

.. release:: 1.0.0
    :date: 2022-11-08

    .. change:: changed
        :tags: Load

        Changed default/first load mode to be merge.


    .. change:: fixed
        :tags: hook

        Same version of Houdini detected twice on Linux because of symlink.


    .. change:: fixed
        :tags: hook

        Fix apprentice discovery bug on Mac.


    .. change:: new
        :tags: doc

        Added API reference and release notes.


    .. change:: new

        Initial release

