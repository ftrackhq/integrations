..
    :copyright: Copyright (c) 2022 ftrack

.. _tutorial/setup:

*****
Setup
*****

.. highlight:: bat

Prerequisites
*************

For this exercise we require to following:

 * A workstation, in our example a PC running Windows 11.
 * A text editor for syntax highlighted editing of Python code, for example PyCharm or Visual Code.
 * Git command line tools installed, including Git bash.
 * A licensed version of Maya 2022 or later.
 * A valid ftrack trial or subscription.
 * ftrack Connect 2 Package installed, with the new framework.
 * A central storage scenario setup to point to your studio network file share.



Git repositories
****************

The best approach is to create your own set of repositories and then pull from the
ftrack Framework repositories as a remote upstream.

..  important::

    You are not forced to create repositories, the simplest approach is to just pull
    the code and start working on it. Recall that it will be difficult to work on
    the code internally as a team without proper SCM in place.


We will extend two Framework plugins:

 * ftrack-connect-pipeline-definition
 * ftrack-connect-pipeline-maya

The rest of the plugins we will use are shipped with Connect and installable through
the plugin manager.

As a first step, create the repositories within your SCM environment (GitHub, Bitbucket, locally..). We
recommend you create them by the same name to minimise confusion.


Next create folders, clone the remote repositories with Git bash and merge from ftrack::

    $ mkdir mypipeline
    $ cd mypipeline
    $ git clone <my SCM service base url>/ftrack-connect-pipeline-definition
    $ git remote add upstream https://github.com/ftrackhq/ftrack-connect-pipeline-definition.git
    $ git fetch upstream
    $ git merge upstream/main
    $ git rebase upstream/main


Repeat the steps above for ftrack-connect-pipeline-maya repository. Throughout this
tutorial, the folder **mypipeline** will refer to this location were you checkout
and store your local source code repository.

At any new release done by ftrack, you can simply pull these and then merge into your repository::

    $ git pull upstream main


Branching
*********

We are not going into full detail on how to manage your source code, a good
general practice to always develop on stories, e.g. backlog/bigfeature/story with
sub branches. For more guidelines on Git: https://nvie.com/posts/a-successful-git-branching-model


Testing
*******

During the test phase you would want to test your tools locally before deploying
centrally. As first step, :ref:`create a virtual environment <developing/build>`,
then follow the instructions on how to build and deploy locally::

    $ <activate virtual environment>
    $ cd mypipeline\ftrack-connect-pipeline-definition
    $ python setup.py build_plugin
    $ rmdir /s "%HOMEPATH%\AppData\Local\ftrack\ftrack-connect-plugins\ftrack-connect-pipeline-definition-<version>"
    $ move build\ftrack-connect-pipeline-definition-<version> "%HOMEPATH%\AppData\Local\ftrack\ftrack-connect-plugins"

The same process applies to the Maya DCC plugin and all other Connect framework plugins.

Pipeline deploy
***************

Towards the end of this chapter, we will build the integration plugins
and put them centrally on a server for everyone to use. We assume there is a space
for pipeline to reside on a network share::

    \\server\share\PIPELINE

This will be the physical location of our custom pipeline, and will be named
"**PIPELINE**" hereafter.








