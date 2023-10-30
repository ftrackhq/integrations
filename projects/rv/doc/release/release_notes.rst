..
    :copyright: Copyright (c) 2017-2020 ftrack

.. _release/release_notes:

*************
Release Notes
*************

.. release:: upcoming

    .. change:: changed

        Replaced setuptools with Poetry and RV package build tool.

    .. change:: fixed
        :tags: Api

        Rv does not play Entity selections.

    .. change:: fixed
        :tags: Logging

        Log initialization breaks due to utf8 conversion.

    .. change:: fixed
        :tags: Api

        Rv breaks not being able to parse tempdata.
        
    .. change:: fixed
        :tags: UX

        Panel size too small at startup.


.. release:: 5.0
    :date: 2021-09-07

    .. change:: changed

        Port to python 3 and PySide2.

    .. change:: changed

        Refactor to support RV 20XX       
    
    .. change:: fixed
        :tags: Api

        Failed to jump to index error.

.. warning::

    From this version the support for ftrack-connect 1.X is dropped, and
    only ftrack-conenct 2.0 will be supported up to the integration EOL.


.. release:: 4.0
    :date: 2020-01-14

    .. change:: changed

        Moved from Qt Webkit to Qt WebEngine for Qt 5.12 / RV 7.5+

    .. change:: changed
        :tags: Setup

        Exposing dependencies folder to resultan build folder

    .. change:: changed
        :tags: Setup

        Build resultant folder renamed with the plugin name + version

    .. change:: changed
        :tags: Setup

        ftrack-location-compatibility version updated to 0.3.3

    .. change:: changed
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
