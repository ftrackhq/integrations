..
    :copyright: Copyright (c) 2022 ftrack

.. _developing/environment:

************************
Coding environment setup
************************

IDE
***

Internally at ftrack we use PyCharm as our main development tool. Visual Studio
would be our second editor of choice, enabling additional free remote
debugging against DCC:s/Maya.


Source Code Management
**********************

It is possible to edit the code and configurations directly without and SCM, but
that will make it very complicated to download and merge in new Framework releases
as they are announced.

The recommended way of doing this is to create your own repositories and then
sync in changes from ftrack by setting adding a remote pointer to our GitHub
repositories. This process is described in detail within the :ref:`tutorial`.