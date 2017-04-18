..
    :copyright: Copyright (c) 2017 ftrack

.. _building_from_source:

********************
Building from source
********************

.. note::

  Unless you are doing any modifications, there should be no need to build the 
  plugin yourself. See :ref:`getting_started` for instructions on how to
  install and run the plugin.

Building plugin
===============

You can build manually from the source for more control. First obtain a
copy of the source by either downloading the
`zipball <https://bitbucket.org/ftrack/ftrack-connect-rv/get/master.zip>`_ or
cloning the public repository::

    git clone git@bitbucket.org:ftrack/ftrack-connect-rv.git

Build the plugin (Will build the plugin and dependencies in `build/plugin`)::

    python setup.py build_plugin

See :ref:`getting_started` for instructions on how to install and run the
plugin.

Building documentation from source
==================================

To build the documentation from source::

    python setup.py build_sphinx

Then view in your browser::

    file:///path/to/ftrack-connect-rv/build/doc/html/index.html

Running tests against the source
================================

With a copy of the source it is also possible to run the unit tests::

    python setup.py test

Dependencies
============

* `Python <http://python.org>`_ >= 2.6, < 3

Additional For building
-----------------------

* `Sphinx <http://sphinx-doc.org/>`_ >= 1.2.2, < 2
* `sphinx_rtd_theme <https://github.com/snide/sphinx_rtd_theme>`_ >= 0.1.6, < 1

Additional For testing
----------------------

* `Pytest <http://pytest.org>`_  >= 2.3.5
