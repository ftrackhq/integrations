# :copyright: Copyright (c) 2018 ftrack

Docker for building ftrack-connect-package
==========================================

Build:
------
$ docker build -t ftrack/connect-package  .


Run and deploy:
---------------
This step will build and upload the file to the amazon folder
$ docker run --env-file <yourenvfile> -it ftrack/connect-package

Run and debug:
--------------
This step will build and test locally the result, please remembre to unset UPLOAD_BUILD environment in the envfile
docker cp <result_docker_image>:/build/ftrack-connect-package-master.tar.gz .

EnvFile
-------
The envfile to be passed along will have to contain:

# connect version to build
FTRACK_CONNECT_PACKAGE_VERSION=<set tag or branch version to use>

# amazon credentials to upload build
AWS_ACCESS_KEY_ID=<amazon access key>
AWS_SECRET_ACCESS_KEY=<amazon secret key>
AWS_DEFAULT_REGION=<amazon default region>

# to enable the upload to amazon please set
UPLOAD_BUILD="1"