######################
ftrack connect package
######################

Meta package that provides support for building platform specific bundles of
ftrack connect packages.

********
Building
********

.. highlight:: bash

Clone the public repository::

    $ git clone git@bitbucket.org:ftrack/ftrack-connect-package.git

Or download and extract the
`zipball <https://bitbucket.org/ftrack/ftrack-connect-package/get/master.zip>`_

Once you have a copy of the source build locally a standalone executable for the
platform you are currently on::

    $ python setup.py build

Alternatively, build appropriate bundles for target platform:

Windows::

    $ python setup.py bdist_msi

OSX::

    $ python setup.py bdist_mac

Dependencies
============

* `Python <http://python.org>`_ >= 2.6, < 3
* `ftrack-connect <https://bitbucket.org/ftrack/ftrack-connect>`_ >= 0.1, < 1

*********************
Copyright and license
*********************

Copyright (c) 2014 ftrack

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this work except in compliance with the License. You may obtain a copy of the
License in the LICENSE.txt file, or at:

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
