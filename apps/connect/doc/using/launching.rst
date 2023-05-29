..
    :copyright: Copyright (c) 2014 ftrack

.. _using/launching:

*********************
Launching the service
*********************

ftrack connect revolves around a core service that runs locally on your machine.
Once you have the main package :ref:`installed <installing>`, you need to run an
instance of the service.

If you are using one of the pre-built packages you can just run the executable
provided.

    *   Mac users will have ftrack-connect.app executable in the 
        Applications directory.
    *   Windows users will have the ftrack connect executable as a
        shortcut on the Desktop and start menu.
    *   Linux users will have the executable in the directory where the .tar
        file was extracted.

Once the service is launched, the main window will appear and you will also
notice an ftrack icon in your task bar.

Windows:

.. image:: /image/windows_service.png

Mac:

.. image:: /image/mac_service.png

The service will then continue to run in the background even if you close all
the windows.

To reopen a window or exit the service, use the :term:`service context menu`.

Alternative launching methods
=============================

If you are using alternative installation methods, such as building from source
or installing through pip, you should open a terminal and execute the following:

.. code-block:: bash

    python -m ftrack_connect

.. note::

    To see all available launch options (including changing the theme and
    logging verbosity) use:

    .. code-block:: bash

        python -m ftrack_connect --help
