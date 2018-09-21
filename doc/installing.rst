..
    :copyright: Copyright (c) 2015 ftrack

.. _installing:

**********
Installing
**********

Using ftrack Connect
====================

.. _using/installing_ftrack_connect_package:

The primary way of installing and launching the Nuke studio integration is
through the ftrack Connect package. Go to 
`ftrack Connect package <https://www.ftrack.com/portfolio/connect>`_ and
download it for your platform.

.. seealso::

    Once ftrack Connect package is installed please follow this
    :ref:`article <using/launching>` to launch Nuke studio with the ftrack
    integration.


Building from source
====================

You can also build manually from the source for more control. First obtain a
copy of the source by either downloading the
`zipball <https://bitbucket.org/ftrack/ftrack-connect-nuke-studio/get/master.zip>`_ or
cloning the public repository::

    git clone git@bitbucket.org:ftrack/ftrack-connect-nuke-studio.git

Then you can build and install the package into your current Python
site-packages folder::

    python setup.py  build_plugin

Once build you can move or symlink the folder to the ftrack-connect-plugin folder directory.

Building documentation from source
----------------------------------

To build the documentation from source::

    python setup.py build_sphinx

Then view in your browser::

    file:///path/to/ftrack-connect-nuke-studio/build/doc/html/index.html

Running tests against the source
--------------------------------

With a copy of the source it is also possible to run the unit tests::

    python setup.py test

Dependencies
============

* `Python <http://python.org>`_ >= 2.6, < 3
* `ftrack connect <https://bitbucket.org/ftrack/ftrack-connect>`_ >= 0.1.2, < 2
* `Nuke Studio <https://www.thefoundry.co.uk/products/nuke/studio/>`_ >= 2 < 3

Additional For building
-----------------------

* `Sphinx <http://sphinx-doc.org/>`_ >= 1.2.2, < 2
* `sphinx_rtd_theme <https://github.com/snide/sphinx_rtd_theme>`_ >= 0.1.6, < 1

Additional For testing
----------------------

* `Pytest <http://pytest.org>`_  >= 2.3.5