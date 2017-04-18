..
    :copyright: Copyright (c) 2016 ftrack

.. _getting_started:

***************
Getting started
***************

To get started with using the ftrack connect RV plugin, follow this guide
and you will be up and running quickly. The RV integration can be either run
from ftrack Connect or installed as a standalone package in RV. Installing
it as a Standalone package requires more setup, but does not require you to be
running Connect in order to use ftrack review in RV.

RV Connect plugin
-----------------

ftrack connect RV comes bundled with ftrack Connect package and allows you
to start launch RV with the ftrack review panels loaded without installing
anything.

.. note::

    If you are running Linux, you will need to set the environment variable
    :envvar:`RV_INSTALLATION_PATH` to the root folder of the RV installation
    for ftrack Connect to find the installation.

Manual installation
^^^^^^^^^^^^^^^^^^^

You can also install the Connect plugin manually if you are running Connect
from source. To do so, follow the instructions below to download and install
the RV connect plugin.

  #. Download the RV integration from the
     `ftrack Integrations page <https://www.ftrack.com/integrations>`_.

  #. Open Connect and select :guilabel:`Open Plugin Directory` from the service
     menu.

  #. Extract the zip archive in the Connect Plugin Folder


RV Standalone package
---------------------

Installing ftrack Connect RV as a standalone package requires more setup, but
does not require you to be running Connect in order to use ftrack review in RV.
To do so, follow the instructions below.

  #. Setup the `RV protocol handler <https://support.shotgunsoftware.com/hc/en-us/articles/219042088-RVLink-URLs-RV-as-protocol-handler>`_
     for your browser.

  #. Download the standalone package for RV from the
     `ftrack Integrations page <https://www.ftrack.com/integrations>`_.

  #. Launch RV and install the :file:`rvpkg` package from RV's preferences.

  #. The RV integration currently requires that the ftrack legacy Python API
     is available and configured with valid credentials. To do so, you can
     either configure credentials via environment variables and set
     :envvar:`PYTHONPATH` (globally) to point to the legacy API or extract the
     legacy Python API archive within the installed RV package's :file:`Python`
     directory and edit the file :file:`ftrack.py`, adding API credentials.

     .. seealso::

        :ref:`Getting started with the legacy Python API <ftrack:developing/legacy/getting_started>`
