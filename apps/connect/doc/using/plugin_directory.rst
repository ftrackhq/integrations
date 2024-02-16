..
    :copyright: Copyright (c) 2016 ftrack

.. _using/plugin_directory:

****************
Plugin directory
****************

ftrack Connect supports extensions through the use of a plugin directory. The
directory will be automatically searched for hooks where users can add their
own custom event processing, actions and locations.

The path for the :term:`default plugin directory` differs between platforms:

:OS X:
    ~/Library/Application Support/ftrack-connect-plugins

:Windows:
    C:\\Documents and Settings\\<User>\\Application Data\\Local Settings\\ftrack\\ftrack-connect-plugins

:Linux:
    ~/.local/share/ftrack-connect-plugins


An easy way of finding your :term:`default plugin directory` is to open the
ftrack connect menu and click `Open plugin directory`:

.. image:: /image/_open_default_plugin_directory.png
    :align: center

This will create the directory if not already existing and open it in the
file browser. Downloaded Connect plugins can be unzipped and placed in this
directory.

.. seealso::

    For development of plugins please refer to this
    :ref:`article <developing/plugins>`.

Environment variable
====================

Advanced users may want to control where Connect looks for plugins. It may be
because you want to centralise hooks on a network share for everyone in the
Company or just want to have them somewhere else than default.

By setting the `FTRACK_CONNECT_PLUGIN_PATH` you can add additional places
where plugin hooks are discovered. E.g::

    export FTRACK_CONNECT_PLUGIN_PATH=/Users/mattiaslagergren/Desktop/my-plugins
