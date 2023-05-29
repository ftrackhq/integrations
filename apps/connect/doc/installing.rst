..
    :copyright: Copyright (c) 2014 ftrack

.. _installing:

**********
Installing
**********

.. highlight:: bash

Pre-built packages are available for download for Windows, Linux and Mac from
the `Integrations webpage <https://www.ftrack.com/portfolio/connect>`_.

.. note::

    Alternative installation methods require technical knowledge.

Building from source
====================

You can also build manually from the source for more control. First obtain a
copy of the source by either downloading the
`zipball <https://bitbucket.org/ftrack/ftrack-connect/get/master.zip>`_ or
cloning the public repository:


.. code-block:: none

    $ git clone git@bitbucket.org:ftrack/ftrack-connect.git


install the requirements to prepare you environment with:

.. code-block:: none

    $ python -m pip install -r requirements.txt


Then you can build and install the package into your current Python
site-packages folder:


.. code-block:: none

    $ python setup.py install


Alternatively, just build locally and manage yourself:

.. code-block:: none

    $ python setup.py build


Is also possible to build live development version using:

.. code-block:: none

    $ python setup.py build_ext --inplace


Building from git repository
============================

.. note::

    This is an advance method and is not suggested for average users
    Please refer to the previous way to install as default.


Alternatively, install using `pip <http://www.pip-installer.org/>`_:

.. code-block:: none

    $ pip install git+https://bitbucket.org/ftrack/ftrack-connect.git


.. warning::

    When installing through pip, the default hooks will not be properly installed as part of the package,
    but they'll instead be installed on the root of the interpreter eg:

    C:\\Python37\\ftrack_connect_resource\\hook

    Before starting connect please ensure the path is added to your

    * **FTRACK_EVENT_PLUGIN_PATH**

    environment variable.


Building documentation from source
----------------------------------

To build the documentation from source:

.. code-block:: none

    $ python setup.py build_sphinx


Then view in your browser::

    file:///path/to/ftrack-connect/build/doc/html/index.html

Running tests against the source
--------------------------------

With a copy of the source it is also possible to run the unit tests:

.. code-block:: none

    $ python setup.py test



Dependencies
============

* `Python <http://python.org>`_ >= 3, < 4
* `PySide <http://qt-project.org/wiki/PySide>`_ >= 2, < 3
* `Riffle <https://github.com/4degrees/riffle>`_ >= 0.1.0, < 2W
* `Qt.py <https://github.com/mottosso/Qt.py>`_ >= 1.3 < 2

Additional For building
-----------------------

* `pyScss <https://github.com/Kronuz/pyScss>`_ >= 1.2.0, < 2
* `Sphinx <http://sphinx-doc.org/>`_ >= 1.8.5, < 4
* `sphinx_rtd_theme <https://github.com/snide/sphinx_rtd_theme>`_ >= 0.1.6, < 1
* `Lowdown <https://bitbucket.org/ftrack/lowdown>`_ >= 0.1.0, < 1

Additional For testing
----------------------

* `Pytest <http://pytest.org>`_  >= 2.3.5
