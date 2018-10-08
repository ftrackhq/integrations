#!/bin/sh
# :copyright: Copyright (c) 2018 ftrack

# Clone respositories.
git clone --branch ${FTRACK_LEGACY_PYTHON_API_VERSION} https://bitbucket.org/ftrack/ftrack-python-legacy-api.git  ${FTRACK_LEGACY_PYTHON_API_PATH};
git clone --branch ${FTRACK_CONNECT_PACKAGE_VERSION} https://bitbucket.org/ftrack/ftrack-connect-package.git ${BUILD_DIR};

# Build connect package.
echo Building Connect Package Version: ${FTRACK_CONNECT_PACKAGE_VERSION}
cd ${BUILD_DIR} && python2.7 setup.py build

# Package result code.
cd ${BUILD_DIR}/build/ && tar -zcvf /${OUT_FOLDER}/ftrack-connect-package-${FTRACK_CONNECT_PACKAGE_VERSION}.tar.gz exe.linux-x86_64-2.7 --transform 's/exe.linux-x86_64-2.7/ftrack-connect-package/' 

if [ -v UPLOAD_BUILD ]; then
    # Install awscli for amazon upload.
    yum install -y libyaml-devel
    python2.7 -m pip install awscli

    # Copy result file to amazon storage.
    aws s3 cp \
        /${OUT_FOLDER}/ftrack-connect-package-${FTRACK_CONNECT_PACKAGE_VERSION}.tar.gz \
        s3://ftrack-deployment/ftrack-connect/ftrack-connect-package-${FTRACK_CONNECT_PACKAGE_VERSION}.tar.gz
else
    echo 'BUILD UPLOAD DISABLED, please run with :  -v `pwd`/volume:/build , to extract the built files.'
fi

