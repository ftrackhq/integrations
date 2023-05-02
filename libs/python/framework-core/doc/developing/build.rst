..
    :copyright: Copyright (c) 2022 ftrack

.. _developing/build:

*****
Build
*****

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
in setup.py beneath the **setup_requires** section.

After that, you should be ready to build the documentation::

    python setup.py build_sphinx



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


