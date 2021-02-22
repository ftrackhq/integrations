..
    :copyright: Copyright (c) 2014-2021 ftrack


######################
ftrack connect package
######################

Meta package that provides support for building platform specific bundles of ftrack connect packages.


Clone the public repository::

    $ git clone git@bitbucket.org:ftrack/ftrack-connect-package.git

Or download and extract the
`zipball <https://bitbucket.org/ftrack/ftrack-connect-package/get/master.zip>`_

Clone ftrack connect public repository::

    $ git clone git@bitbucket.org:ftrack/ftrack-connect.git

Or download and extract the
`zipball <https://bitbucket.org/ftrack/ftrack-connect/get/master.zip>`_



.. note::

    If in windows, please create the virtual env using venv.


Install dependencies with::

    $ pip install -r <ftrack-connect-package>/requirements.txt

.. warning::

    After installing the requirements.txt please manually install cx_freeze from latest master. (This will be included in the requirements when a cx_freeze > `3.7 <https://github.com/marcelotduarte/cx_Freeze/pull/887>`_ is released)::

        $ pip install git+https://github.com/marcelotduarte/cx_Freeze.git


Install ftrack connect::

    $ cd <ftrack-connect>
    $ python setup.py install

Build connect package with (specific build package)::

        $ cd <ftrack-connect-package>



Linux
-----

Build tar.gz release with::

    $ python setup.py build_exe



Once build the result will be available in build/exe.linux-x86_64-**<PYTHON VERSION>**

To generate the tar.gz run from the build folder::

    $ tar -zcvf ftrack-connect-package-<PACKAGE VERSION>-<PLATFORM>.tar.gz exe.linux-x86_64-3.7 --transform 's/exe.linux-x86_64-3.7/ftrack-connect-package/'


Generate the md5 with::

    $ md5sum ftrack-connect-package-<PACKAGE VERSION>-<PLATFORM>.tar.gz > ftrack-connect-package-<PACKAGE VERSION>-<PLATFORM>.tar.gz.md5


.. note::

    Please remember to set **<PLATFORM>** to either:

    * C7 for Centos 7 compatible releases.
    * C8 for centos 8 compatible releases.



Windows
-------

Build msi release with::

    $ python setup.py bdist_msi


.. note::

    Codesign process works only on machine where the key certificate is loaded and available.
    Codesign also require to have the signtool.exe installed and available.


To codesign
...........


Once the msi is built, run the following commands to codesign it::

    $signtool sign /tr http://timestamp.sectigo.com /td sha256 /fd sha256 /a <path to msi file>

At the end of the process you'll then asked to provide your token password, once done, the package should get codesigned.


MaxOs
-----

Install appdmg to be able to create the dmg::

    $ npm install -g appdmg

.. note::

    On latest version of OSX these envs are needed in order to properly build::

        $ export CPPFLAGS=-I/usr/local/opt/openssl/include
        $ export LDFLAGS=-L/usr/local/opt/openssl/lib


To build without codesign
.........................

Build with::

    $ python setup.py bdist_mac


To build and codesign
.....................

Set your certificate id to **CODESIGN_IDENTITY**::

    $ export CODESIGN_IDENTITY="<your_certificate_id_here>"

Set your Apple user name to **APPLE_USER_NAME**::

    $ export APPLE_USER_NAME="<your_apple_user>"

Set your APP-specific password generated on https://appleid.apple.com/account/manage to the keychain under the name ftrack_connect_sign_pass.

Execute the following build command and follow the instructions::

    $ python setup.py bdist_mac --codesign_frameworks --codesign --create_dmg --notarize



Docker
======

As part of this repository, 3 Dockerfile are available to sendbox the build of ftrack-connect-package.

* C7-Dockerfile    [centos 7]
* C8-Dockerfile    [centos 8]
* Win10-Dockerfile [windows 10]

For further informations, please use the README file contained in the **docker** folder.

.. note::

    In order to build in docker windows, you need to have a windows 10 Pro activated and configured.


Known Issues
============

* None

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
