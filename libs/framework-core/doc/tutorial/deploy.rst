..
    :copyright: Copyright (c) 2022 ftrack

.. _tutorial/deploy:

********************************************
Deploy the customised pipeline within studio
********************************************

.. highlight:: bat

Before we can start using our custom pipeline, we want to make sure
Maya can be launched using our customised framework through Connect.

Create and activate an virtual environment
******************************************

To be able to build the framework integrations, we need to create a Python 3.7.12 virtual environment:

 #. Download Python 3.7.12 (https://www.python.org/downloads/release/python-3712/)
 #. Open a shell/DOS box and install virtual env: ``pip install virtualenv``
 #. Create the virtual environment: ``virtualenv venv_3712``
 #. Activate it: ``venv_py3712\Scripts\activate``

Build the integrations
**********************

We build each integration using this virtual env::

    $ cd mypipeline\ftrack-connect-pipeline-definition
    $ python setup.py build_plugin

We repeat this for the ``ftrack-connect-pipeline-maya`` repository.


The built plugin will end up in the ``build/`` folder.


Install the integrations on another machine
*******************************************

Before we deploy centrally, we advise testing integrations on a separate machine,
and iron out eventual bugs with rigorous testing.

Copy the integrations from each build/ folder to the Connect default plug-in search path,
overwriting the existing plugins:

 #. Windows: C:\Documents and Settings\<User>\Application Data\Local Settings\ftrack\ftrack-connect-plugins
 #. Linux: ~/.local/share/ftrack-connect-plugins
 #. OSX: ~/Library/Application Support/ftrack-connect-plugins

Also copy the custom folder structure, ``custom-location-plugin folder``.

Restart ftrack Connect and verify that all plugins are installed, including
``ftrack-application-launcher``, ``ftrack-connect-pipeline-qt``,
``ftrack-connect-application-launcher-widget``.

Launch Maya on an animation task, verify the publish and
load functions together with the task status set tool.



Deploy the integrations studio wide
***********************************

Here we make sure all on-prem workstations load the same centrally deployed
integrations:

 #. Pick a folder on the network (e.g. ``\\server\share\PIPELINE\connect``)
 #. Move all integrations from local test deploy to this folder.
 #. Move the custom location plug-in to a separate folder (e.g. ``\\server\share\PIPELINE\api``)
 #. Setup FTRACK_CONNECT_PLUGIN_PATH to point to these folders (e.g. ``FTRACK_CONNECT_PLUGIN_PATH=\\server\share\PIPELINE\connect;\\server\share\PIPELINE\api``)
 #. Set FTRACK_EVENT_PLUGIN_PATH to point to the custom location structure this enables our custom folder structure within all API sessions (e.g. ``FTRACK_EVENT_PLUGIN_PATH=\\server\share\PIPELINE\api``).


..  important::

    Make sure that the default builds of your customised integration plugins
    are removed from Connect installed at workstations across your studio
    (see local folders above), otherwise they will collide.

