#########################################################################
# :copyright: Copyright (c) 2018 ftrack

# BUILD WITH : sudo docker build -t ftrack/connect-package --build-arg CACHEBUST=$(date +%s) .
# RUN WITH: docker run --rm -it -v `pwd`/volume:/build ftrack/connect-package

FROM centos:7
LABEL Ftrack AB: 0.1

# Define Python Version to build and use
ENV PYTHON_VERSION 2.7.9

# Define connect version to build
ENV FTRACK_CONNECT_PACKAGE_VERSION master

# Ftrack required environments
# Legacy Plugins
ENV FTRACK_CONNECT_LEGACY_PLUGINS_PATH /opt/ftrack-connect-legacy-plugins
ENV FTRACK_CONNECT_LEGACY_PLUGINS_VERSION 1.0.0

# Legacy API
ENV FTRACK_LEGACY_PYTHON_API_PATH /opt/ftrack-python-legacy-api
ENV FTRACK_LEGACY_PYTHON_API_VERSION master

# Utility environments
ENV OUT_FOLDER build
ENV BUILD_DIR /opt/ftrack-connect-package-${FTRACK_CONNECT_PACKAGE_VERSION}

ENV USER ftrack

#########################################################################
# ----------------------- SYSTEM SETUP ----------------------------------
# Add custom user
RUN useradd ${USER}

# Ensure system is up to date and provide basic tools and libraries.
RUN yum -y update
RUN yum -y groupinstall "Development Tools"
RUN yum -y install \
    wget \
    cmake \
    openssl-devel \
    openssl \
    sqlite-devel \
    sqlite \
    glibc-devel.x86_64 \
    glibc-devel.i686 \
    libicu-devel\
    libicu \
    wget \
    git \
    tar \
    bzip2 \
    bzip2-devel\ 
    python-virtualenv\
    python-pyside\
    python-devel\
    qt-devel\
    libxml2\
    libxslt\
    libffi\
    libffi-devel;

# Use 6 parallel processes for builds.
ENV MAKEFLAGS -j6

# Build selected python version.
RUN yum install -y \
    zlib-devel \
    bzip2-devel \
    openssl-devel \
    ncurses-devel \
    sqlite-devel \
    readline-devel \
    tk-devel \
    gdbm-devel \
    db4-devel \
    libpcap-devel \
    xz-devel \
    expat-devel \
    wget;

RUN wget http://python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz -P /tmp
RUN cd /tmp && tar xf Python-${PYTHON_VERSION}.tar.xz
RUN cd /tmp/Python-${PYTHON_VERSION} && \
    /tmp/Python-${PYTHON_VERSION}/configure \
        --prefix=/usr/local \
        --enable-unicode=ucs4 \
        --with-ensurepip=yes \
        --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib" \
    && make && make altinstall

# Ensure correct versions of setuptool is installed. 
RUN python2.7 -m pip install setuptools==36.0.1

# Install pyside. 
RUN python2.7 -m pip install PySide

# Ensure pyside-rcc is in PATH.
ENV PATH "${PATH}:/usr/local/lib/python2.7/site-packages/PySide"

#########################################################################
# ----------------------- CONNECT SETUP & BUILD--------------------------

# Legacy Plugins.
RUN git clone --branch ${FTRACK_CONNECT_LEGACY_PLUGINS_VERSION} https://bitbucket.org/ftrack/ftrack-connect-legacy-plugins.git ${FTRACK_CONNECT_LEGACY_PLUGINS_PATH}

# Legacy api.
RUN git clone --branch ${FTRACK_LEGACY_PYTHON_API_VERSION} https://bitbucket.org/ftrack/ftrack-python-legacy-api.git  ${FTRACK_LEGACY_PYTHON_API_PATH}

# Clone connect-package code in build folder.
RUN git clone --branch ${FTRACK_CONNECT_PACKAGE_VERSION} https://bitbucket.org/ftrack/ftrack-connect-package.git ${BUILD_DIR}

# Run buld process.
RUN cd ${BUILD_DIR} && python2.7 setup.py build

# Prepare output folders
RUN chown -R ${USER}:${USER} ${BUILD_DIR}
VOLUME /${OUT_FOLDER}
RUN chmod -R 777 /${OUT_FOLDER}

# Disable cache so we always package again the latest built version
ARG CACHEBUST=1

# Create tar.gz and add it to the output folder
RUN cd ${BUILD_DIR}/build/exe.linux-x86_64-2.7/ && \
    tar -zcvf /${OUT_FOLDER}/ftrack-connect-package-${FTRACK_CONNECT_PACKAGE_VERSION}.tgz * \
    && bash
