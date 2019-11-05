..
    :copyright: Copyright (c) 2017 ftrack

.. _release/release_notes:

*************
Release Notes
*************

.. release:: Upcoming

    ..change:: changed
        :tags: Setup

        Build resultant folder renamed with the plugin name + version

    ..change:: changed
        :tags: Setup

        ftrack-location-compatibility version updated to 0.3.3

    ..change:: changed
        :tags: Setup

        Pip compatibility for version 19.3.0 or higher

.. release:: 3.7
    :date: 2017-11-17

    .. change:: fixed

       Fail gracefully if a single asset version fails to load.

.. release:: 3.6
    :date: 2017-06-28

    .. change:: fixed

        Unable to add notes with annotations.

    .. change:: fixed

        Plugin outputs error if installation location is not found for RV under
        Linux.

    .. change:: fixed

        The action is registered twice in ftrack connect.

.. release:: 3.5
    :date: 2017-05-30

    .. change:: fixed

        RV crashes when loading a previously loaded version for the second time.

.. release:: 3.4
    :date: 2017-05-17

    .. change:: new
        :tags: Documentation

        Added :ref:`installation instructions <getting_started>`.

    .. change:: fixed

        New versions of RV are not found in their default installation directory.
