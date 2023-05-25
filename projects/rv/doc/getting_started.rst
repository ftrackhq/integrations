..
    :copyright: Copyright (c) 2016 ftrack

.. _getting_started:

***************
Getting started
***************

To get started with using the ftrack connect RV plugin, follow this guide
and you will be up and running quickly.

Installing the RV package
-------------------------

First, you will need to install the integration package in RV:

  #. Download the standalone package for RV from the
     `ftrack Integrations page <https://www.ftrack.com/integrations>`_.

  #. Launch RV and install the :file:`rvpkg` package from RV's preferences.

Launching
---------

You can launch RV with the integration either as an action using ftrack Connect
or via the rvlink protocol from the web interface.

Using ftrack Connect
^^^^^^^^^^^^^^^^^^^^

ftrack connect RV comes bundled with ftrack Connect package and allows you
to start launch RV with the ftrack review panels without any additional
configuration.

.. note::

    If you are running Linux, you will need to set the environment variable
    :envvar:`RV_INSTALLATION_PATH` to the root folder of the RV installation
    for ftrack Connect to find the installation.

From the web interface
^^^^^^^^^^^^^^^^^^^^^^

Running ftrack Connect RV via the rvlink protocol requires a bit more setup,
but does not require you to be running Connect in order to use ftrack review
in RV. To do so, follow the instructions below.

  #. Setup the `RV protocol handler <https://support.shotgunsoftware.com/hc/en-us/articles/219042088-RVLink-URLs-RV-as-protocol-handler>`_
     for your browser.

  #. The RV integration currently requires that the ftrack legacy Python API
     is available and configured with valid credentials. To do so, you can
     either configure credentials via environment variables and set
     :envvar:`PYTHONPATH` (globally) to point to the legacy API or extract the
     legacy Python API archive within the installed RV package's :file:`Python`
     directory and edit the file :file:`ftrack.py`, adding API credentials.

     .. seealso::

        :ref:`Getting started with the legacy Python API <ftrack:developing/legacy/getting_started>`
