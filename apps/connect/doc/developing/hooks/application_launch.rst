..
    :copyright: Copyright (c) 2016 ftrack

.. _developing/hooks/application_launch:

*********************************
ftrack.connect.application.launch
*********************************

The `ftrack.connect.application.launch` synchronous event is triggered when an
application is launched using the
:py:class:`ftrack_connect.application.ApplicationLauncher`.

It can be used to modify the environment and arguments used when launching
applications using :py:func:`subprocess.Popen`.

Example event passed to hook::

    Event(
        topic='ftrack.connect.application.launch',
        data=launch_data
    )

The passed data variable, launch_data is a dictionary containing:

command
    The first arugment passed to subprocess.Popen, containing a :py:class:`list`
    of the command should run.

options
    A dictionary with keyword arguments passed to subprocess.Popen.

application
    A dictionary containing information about the application that is being
    launched.

context
    The ftrack entity context that the application is being launched for.

Modifications to the launch_data dictionary, either by replacing the content
or modifying it directly, will be picked up and used by the application
launcher.
