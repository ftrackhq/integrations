.. _developing:

##########
Developing
##########


***********************
Creating a new launcher
***********************

In order to be able to find and manage applications and integrations,
an application launcher has to be provided.

Launchers requires to be either configured or written from scratch using the base libraries included in this module.

The configuration mode is suggested for all the base cases,
where the code base approach is suggested in case of special application launch behaviours.


Attributes
==========

.. note::

    For simplicity we'll be taking the config arguments as example as are easier to read.


Let's have a look at the common attributes you'll find in both, split by mandatory and optional attributes.


**Mandatory attributes**
------------------------

**context**:

    Provide a list to fill up with named contexts.
    The launcher will appear only when one of the given contexts is selected.

    .. note::

        context can contain one or more entity type name such as **"Project"**, **"Task"**, etc...
        **None** in code or **null** in config, will allow to discover the application without any context selected.

**identifier**:

    Defines a unique string identifier for this launcher.

**applicationIdentifier**:

    Defines a unique string identifier for the application to be launch,
    this also need to contain the potential **variant** available, so can be uniquely identified.

    .. note::

        **applicationIdentifier** should always include the **{variant}** variable.


**label**:

    A descriptive label to identify the application.

**icon**:

    An icon to represent the application to launch.

    .. note::

        Icon can be either one of the application name mapped or a full url path to a given icon.

**variant**:

    Defines the variant of the application to be launched.

    .. note::

        **variant** should always include the **{version}** variable.


**search_path**:

    Provide an entry point for each operating system to define where from the application will searched.

    .. note::

        The valid operating system are:

        * **linux**
        * **windows**
        * **darwin**

    Each operating system will require to define :

        **prefix**

            Provide the root search path for all the versions of the given application.

            eg::

                "prefix":["C:\\", "Program Files.*"],

        **expression**

            Provide a regular expression used to extract the versions available for the given application.

            eg::

                "expression":["Something.*", "Something\\d.+.exe"],


    and optionally :

      **version_expression**

            Defines a regular expression used to extract the version from the found application paths.

            eg::

            "version_expression": "Something(?P<version>.*)\\/.+$",



      **launch_arguments**


            Allows to specify specific arguments to be passed when the application gets launched.


            eg::

            "launch_arguments": ["--arguments"]



**Optional attributes**
-----------------------


**priority** *(optional)*:

    Define the priority on which this event will be discovered.

    .. note::

        Negative priorities are higher than positive ones.


**integrations** *(optional)*:


    Provide a way to collect integrations into named groups.
    If any of the integration requested is not discovered, the application itself won't be discovered.


    eg::


        "integrations": {
            "example":["ftrack-example-integration"]
        },


Comparing launchers
===================

Below we'll be looking at the same launch application expressed in configuration and code.


Configuration based launcher
----------------------------

.. note::

    Configuration launchers are based on json language.

.. literalinclude:: examples/config-example.json



Code based launcher
-------------------

.. note::

    Code launchers are based on python 3.7 language.


.. literalinclude:: examples/code-example.py


Customising configuration path
------------------------------

If you want to provide alternative configurations for the application launchers, 
it is possible to override the search path setting the following environment variable to a set of new folder search path.

**FTRACK_APPLICATION_LAUNCHER_CONFIG_PATHS**



