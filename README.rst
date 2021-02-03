..
    :copyright: Copyright (c) 2014-2020 ftrack

######################
ftrack connect package
######################

Meta package that provides support for building platform specific bundles of
ftrack connect packages.

********
Building
********


Clone the public repository::

    $ git clone git@bitbucket.org:ftrack/ftrack-connect-package.git

Or download and extract the
`zipball <https://bitbucket.org/ftrack/ftrack-connect-package/get/master.zip>`_

Clone ftrack connect public repository::

    $ git clone git@bitbucket.org:ftrack/ftrack-connect.git

Or download and extract the
`zipball <https://bitbucket.org/ftrack/ftrack-connect/get/master.zip>`_

Create and activate a virtual environment with python3.7

Install dependencies with::

    $ pip install -r <ftrack-connect-package>/requirements.txt

Install ftrack connect::

    $ cd <ftrack-connect>
    $ python setup.py install

Build connect package with (specific build package)::

        $ cd <ftrack-connect-package>


Windows:

    .. note ::

        In case of : WindowsError [206] filepath or extension too long
        manually install the first failing dependencies

    ::

        $ python setup.py bdist_msi

OSX:

    Install appdmg to be able to create the dmg::

        $ npm install -g appdmg

    ..Note::
        On latest version of OSX these envs are needed in order to properly build::

            $ export CPPFLAGS=-I/usr/local/opt/openssl/include
            $ export LDFLAGS=-L/usr/local/opt/openssl/lib


    * To build without codesign do::

            $ python setup.py bdist_mac

    * To build and codesign do:

        Set your certificate id to CODESIGN_IDENTITY::

            $ export CODESIGN_IDENTITY="<your_certificate_id_here>"

        Set your Apple user name to APPLE_USER_NAME::

            $ export APPLE_USER_NAME="<your_apple_user>"

        Set your APP-specific password generated on https://appleid.apple.com/account/manage to the keychain under the name ftrack_connect_sign_pass.

        Execute the following build command and follow the instructions::

            $ python setup.py bdist_mac --codesign_frameworks --codesign --create_dmg --notarize


Known Issues
============

* On Windows, the process will sometimes segfault when building. Running build
  again will solve the issue.

* Sometimes the build process will fail with an error about a missing
  'build_data' command. Running build again without changes should solve the
  issue.

Dependencies
============

* `Python <http://python.org>`_ >= 3.7, < 3.8
* `ftrack-connect <https://bitbucket.org/ftrack/ftrack-connect>`_ >= 2.0, < 3.0

*********************
Copyright and license
*********************

Copyright (c) 2014-2020 ftrack

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this work except in compliance with the License. You may obtain a copy of the
License in the LICENSE.txt file, or at:

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
