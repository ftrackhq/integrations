# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Test configuration for framework-maya-deadline.

Usage::

    pytest tests/ -v \\
        --dcc-connect-plugin ../framework-maya \\
        --dcc-connect-plugin .

The first ``--dcc-connect-plugin`` is the primary
(framework-maya, provides DCC discovery).  The second
layers framework-maya-deadline on top.
"""
