..
    :copyright: Copyright (c) 2022 ftrack

.. _developing/build:

****************
Build and deploy
****************

.. highlight:: bash

Create a virtual environment
============================

 #. Download and install/build latest Python 3.7, see below for reasoning on which Python version to use.
 #. Install virtualenv.
 #. Create a virtual env.
 #. Change folder to ftrack-connect-pipeline

Run::

    pip install .

This will setup your virtual environment with the dependencies needed.


Choosing Python base version
----------------------------

To take into consideration here is the target set of DCC applications the
Framework is supposed to work with, from that set you need to evaluate which
is the lowest common denominator built in Python interpreter version. As of 2022,
this is Python 3.7 but will be subject to change as DCC:s move forward according
to the VFX reference platform.


Building the Framework
======================

The process of building a Framework plugin is the same:

 #. Activate the virtual env created above.
 #. Change folder to ftrack-connect-pipeline

Run::

    python setup.py build_plugin

This will produce output into the /build subfolder, repeat this step for each
Framework plugin (ftrack-connect-pipeline-definition, ftrack-connect-pipeline-qt
and so on)


Building the documentation
==========================

Install the doc build dependencies into your virtual env, you will find these
in setup.py beneat the **setup_requires** section.

After that, you should be ready to build the documentation::

    python setup.py build_sphinx


Deploying the Framework locally
===============================

After you have built, copy the plugin directory that is output in /build for
each Framework plugin, to the ftrack Connect plugin path (or to a location
pointed to by the FTRACK_CONNECT_PLUGIN_PATH):

 * Windows; **%LOCALAPPDATA%\\ftrack\\ftrack-connect-plugins**
 * Mac OSX; **~/Library/Application Support/ftrack-connect-plugins**
 * Linux; **~/.local/share/ftrack-connect-plugins**

Finalise by restarting Connect and DCC(s) to have the newly built integrations discovered.

..  important::

    This is no need to restart Connect on a rebuild if the the version number is
    the same, in that case only a relaunch of DCC is required.


Building and deploying Connect centrally
========================================

To minimise IT administrative tasks, one could build Connect and launch it from
a central location within an new or existing Python environment.

The process is documented in the :ref:`ftrack Connect documentation <ftrack-connect:developing>`,
a short summary:

 * Clone the code from: https://github.com/ftrackhq/ftrack-connect.git
 * Create a Virtual environment
 * Change folder to ftrack-connect
 * Install the requirements

Run::

    pip install .

or::

    python setup.py install

A Connect executable is then compiled, which can be set to run a login time on
workstations and be wrapped with a proper launcher having an icon.



Deploying Framework centrally
=============================

To have Connect pickup your custom built Framework plugins, build and deploy them
to a central network location, for example::

    \\filesrv\nas\pipeline\connect

Then on workstations set the environment variable to point at this location::

    set|export FTRACK_CONNECT_PLUGIN_PATH=\\filesrv\nas\pipeline\connect

Finally install and launch Connect, remember to remove any locally installed
Framework plugins to prevent conflict.