#!/bin/sh
# :copyright: Copyright (c) 2018 ftrack


# Update to latest pip version
python2.7 -m pip install --upgrade pip==19.3.0

# Ensure correct versions of setuptool is installed. 
python2.7 -m pip install setuptools==36.0.1

# Ensure arrow and its dependencies are installed
python2.7 -m pip install arrow


# Clone respositories.
git clone --branch ${FTRACK_LEGACY_PYTHON_API_VERSION} https://bitbucket.org/ftrack/ftrack-python-legacy-api.git  ${FTRACK_LEGACY_PYTHON_API_PATH};
git clone --branch ${FTRACK_CONNECT_PACKAGE_VERSION} https://bitbucket.org/ftrack/ftrack-connect-package.git ${BUILD_DIR};

# Build connect package.
echo Building Connect Package Version: ${FTRACK_CONNECT_PACKAGE_VERSION} in /${OUT_FOLDER}/ftrack-connect-package-${FTRACK_CONNECT_PACKAGE_VERSION}.tar.gz

cd ${BUILD_DIR} && python2.7 setup.py build

# Package result code.
cd ${BUILD_DIR}/build/ && tar -zcvf /${OUT_FOLDER}/ftrack-connect-package-${FTRACK_CONNECT_PACKAGE_VERSION}.tar.gz exe.linux-x86_64-2.7 --transform 's/exe.linux-x86_64-2.7/ftrack-connect-package/' 

if [ -v $UPLOAD_BUILD ]; then
    # Install awscli for amazon upload.
    yum install -y libyaml-devel
    python2.7 -m pip install awscli
    
    echo "RUN "
    # Copy result file to amazon storage.
    aws s3 cp --acl public-read \
        /${OUT_FOLDER}/ftrack-connect-package-${FTRACK_CONNECT_PACKAGE_VERSION}.tar.gz \
        s3://ftrack-deployment/ftrack-connect/ftrack-connect-package-${FTRACK_CONNECT_PACKAGE_VERSION}.tar.gz
else
    echo 'BUILD UPLOAD DISABLED'

    if [ -f /${OUT_FOLDER}/ftrack-connect-package-*.tar.gz ]; then
        filename=$(ls /${OUT_FOLDER}/ftrack-connect-package-*.tar.gz)
        echo "Use docker cp to copy the package:"
        echo "  docker cp $HOSTNAME:/$filename ./"
    fi
fi

