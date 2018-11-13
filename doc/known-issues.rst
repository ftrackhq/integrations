..
    :copyright: Copyright (c) 2018 ftrack

############
Known Issues
############

A collection on known issues and how to solve them.


ImportError: No Qt binding were found.
======================================

This error is raised tends to appear when first running connect from linux.
This happens due to the missing libpng12 from the system libraries, as is required by 
the Qt png plugin shipped with ftrack-connect.

To solve
--------

install it with the system installation tool e.g. (on centos7):

.. code-block:: bash

    $ sudo yum install -y libpng12

.. note:: text

    In case you are not allowed to install libraries or tools, please contact your system administrator.


No system tray located.
=======================

This error is likey to happen under linux with Gnome 3 as Desktop environment, as 
in this version system tray has been removed.


To solve
--------

Install a Gnome 3 extension such as `Top Icon Plus <https://extensions.gnome.org/extension/1031/topicons/>`_ 
or use different desktop enviromnet such as Kde, Xfce, Mate or Cinnamon.


Cannot mix incompatible Qt library (version XXXX) with this library
===================================================================
This usually happens due to some qt plugins available on the system which have 
been compiled from a different qt version. 


To solve
--------

Unset QT_PLUGIN_PATH enviroment variable.