..
    :copyright: Copyright (c) 2022 ftrack

.. _tutorial/finalise:

*****************************
Post Slack message on publish
*****************************

Next, we implement a custom finaliser within Maya - a small function that posts a
Slack message containing the version ident, the comment and a thumbnail
(can be replaced with the full Quicktime reviewable movie if desired), with each
publish made.

Functions that run after load and import are called "finalizers" and they are
fed all the data from the previous steps and stages.

Save copy of thumbnail image
****************************

As a preparation, we need to have the thumbnail publisher to save a copy to be
used with the Slack post:

**PIPELINE/ftrack-connect-pipeline-definitions/resource/plugins/maya/python/publisher/exporters/maya_thumbnail_publisher_exporter.py**

..  code-block:: python
    :linenos:
    :emphasize-lines: 2,10

    import os
    import shutil

    ..

    def run(self, context_data=None, data=None, options=None):
        ..
        # Make a copy of the thumbnail to be used with Slack post
        path_slack_thumbnail = os.path.join(os.path.dirname(path), 'slack-{}'.format(os.path.basename(path)))
        shutil.copy(path, path_slack_thumbnail)

        return [path]

Finaliser
*********

**PIPELINE/ftrack-connect-pipeline-definitions/resource/plugins/common/python/publisher/finalisers/common_slack_post_publisher_finalizer.py**

.. literalinclude:: /resource/ftrack-connect-pipeline-definition/resource/plugins/common/python/publisher/finalisers/common_slack_publisher_post_finalizer.py
    :language: python
    :linenos:
    :emphasize-lines: 18,45-48,54-57,66-71


Breakdown of plugin:

 * With the *data* argument, the finaliser gets passed on the result from the entire publish process. From this data we harvest the temporary path to thumbnail and asset version id.
 * We transcode the path so we locate the thumbnail copy.
 * A Slack client API session is created
 * An human readable asset version identifier is compiled
 * If a thumbnail were found, it is uploaded to Slack. A standard chat message is posted otherwise.

Add Slack finaliser to publishers
*********************************


Finally we augment the publishers that we wish to use.

**PIPELINE/ftrack-connect-pipeline-definition/resource/definitions/publisher/maya/geometry-maya-publish.json**

..  code-block:: json
    :linenos:
    :emphasize-lines: 32,36

    {
      "type": "publisher",
      "name": "Geometry Publisher",
      "contexts": [],
      "components": [],
      "finalizers": [
        {
          "name": "main",
          "stages": [
            {
              "name": "pre_finalizer",
              "visible": false,
              "plugins":[
                {
                  "name": "Pre publish to ftrack server",
                  "plugin": "common_passthrough_publisher_pre_finalizer"
                }
              ]
            },
            {
              "name": "finalizer",
              "visible": false,
              "plugins":[
                {
                  "name": "Publish to ftrack server",
                  "plugin": "common_passthrough_publisher_finalizer"
                }
              ]
            },
            {
              "name": "post_finalizer",
              "visible": true,
              "plugins":[
                {
                  "name": "Post slack message",
                  "plugin": "common_slack_publisher_finalizer"
                }
              ]
            }
          ]
        }
      ]
    }


Repeat this for all publishers that should have the finaliser.


Add Slack library
*****************

To be able to use the Slack Python API, we need to add it to our Framework build.
We do that by adding the dependency to setup.py:

**ftrack-connect-pipeline-definition/setup.py**



..  code-block:: python
    :linenos:
    :emphasize-lines: 27,29-31

    ..

    # Configuration.
    setup(
        name='ftrack-connect-pipeline-definition',
        description='Collection of definitions of package and packages.',
        long_description=open(README_PATH).read(),
        keywords='ftrack',
        url='https://bitbucket.org/ftrack/ftrack-connect-pipeline-definition',
        author='ftrack',
        author_email='support@ftrack.com',
        license='Apache License (2.0)',
        packages=find_packages(SOURCE_PATH),
        package_dir={'': 'source'},
        python_requires='<3.10',
        use_scm_version={
            'write_to': 'source/ftrack_connect_pipeline_definition/_version.py',
            'write_to_template': version_template,
            'version_scheme': 'post-release',
        },
        setup_requires=[
            'sphinx >= 1.8.5, < 4',
            'sphinx_rtd_theme >= 0.1.6, < 2',
            'lowdown >= 0.1.0, < 2',
            'setuptools>=44.0.0',
            'setuptools_scm',
            'slackclient'
        ],
        install_requires=[
            'slackclient'
        ],
        tests_require=['pytest >= 2.3.5, < 3'],
        cmdclass={'test': PyTest, 'build_plugin': BuildPlugin},
        zip_safe=False,
    )



..  important::

    A better approach is to add the dependency to the ``ftrack-connect-pipeline``
    module where the other pipeline dependencies are defined and built.