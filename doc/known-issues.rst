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

