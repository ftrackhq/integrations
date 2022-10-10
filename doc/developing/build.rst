..
    :copyright: Copyright (c) 2022 ftrack

.. _developing/build:

****************
Build and deploy
****************

.. highlight:: bash

TBC

Building and deploying Connect centrally
========================================

To minimise IT administrative tasks, one could build Connect and launch it from
a central location within an new or existing Python environment.

Simply checkout Connect 2 from Bitbucket repository and build it:

 * Clone the code
 * Create a venv
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

To have Connect pickup your custom built framework plugins, build and deploy them
to a central network location, for example::

    \\filesrv\nas\pipeline\connect

Then on workstations set the environment varible to point at this locatoin::

    set|export FTRACK_CONNECT_PLUGIN_PATH=\\filesrv\nas\pipeline\connect

Finally install and launch Connect, remember to remove any locally installed
framework plugins to prevent conflict.