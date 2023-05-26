..
    :copyright: Copyright (c) 2014 ftrack

.. _using/connect_widgets:

******************
Custom tab widgets
******************

It is currently possible to provide connect with custom tabs though **connect widget plugins**.

This plugins allow to provide custom tabs which can host any custom functionalities,
which might be required by productions.


More information on how to write a connect widget plugin are available in :ref:`development docs <developing/hooks/connect_widget>`


Default plugins
===============

By default ftrack connect is shipped with two default plugins.

* Launch
* Publish


Default Connect widget example

.. image:: /image/connect_widget.png




Installing plugins
==================

New plugins can be provided as part of the FTRACK_CONNECT_PLUGIN_PATH path, under a *hook* folder.

for example ::

    <$FTRACK_CONNECT_PLUGIN_PATH>/my_widget/hook



.. note ::

    If you find yourself in need of using third party modules, please see how ftrack plugins are usually packaged.
    A example is available as part of our `recipes repository <https://bitbucket.org/ftrack/ftrack-recipes/src/master/python/plugins/>`_
