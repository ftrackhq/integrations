..
    :copyright: Copyright (c) 2022 ftrack

.. _introduction/how:

************
How it works
************

Here we will outline how the new framework works, within the DCC application.


.. important::

    We are not going to touch upon Connect and the launcher, please see separate
    user documentation.


As mentioned previously, the new framework is designed to make it easy to write
custom code that takes care of asset load and publishing, the new framework achieves
this by introducing “definitions” which basically are JSON schemas that configures
which framework plugins (loaders and publishers) to run for a certain ftrack asset type.


Let’s see
what happens step by step within the DCC application during launch, load, asset
management and publish.


.. toctree::
    :maxdepth: 2
    :caption: Contents:

    launch
    load
    asset
    publish

