..
    :copyright: Copyright (c) 2021 ftrack

##########
Installing
##########


Building from source
====================

.. note::

   * Requires python 3.7
   * It is suggested to build the project in a virtual environment.


To build manually from the source, first obtain a copy of the source by either downloading the
`zipball <https://bitbucket.org/ftrack/ftrack-application-launcher/get/master.zip>`_ or
cloning the public repository:


.. code-block:: none

    $ git clone git@bitbucket.org:ftrack/ftrack-application-launcher.git


Then you can build the plugin with :


.. code-block:: none

    $ python setup.py build_plugin


The result packaged and unpackaged plugin will be available under the *build* folder of the current project.


Building documentation from source
----------------------------------

To build the documentation from source:

.. code-block:: none

    $ python setup.py build_sphinx


Then view in your browser::

    file:///path/to/ftrack-application-launcher/build/doc/html/index.html


Installing
==========

In order to install, you can either copy the plugin from the build folder or ensure your
**FTRACK_CONNECT_PLUGIN_PATH** includes the output *build* folder.

.. note::

    eg: export FTRACK_CONNECT_PLUGIN_PATH=<ftrack-application-launcher_path>/build


Reporting bugs
==============

If any bug or issue is found please report to support[at]ftrack.com