#########################################################################
# :copyright: Copyright (c) 2018 ftrack

# BUILD WITH : sudo docker build -t ftrack/connect-package .
# RUN WITH: docker run --rm ftrack/connect-package

FROM centos:7
LABEL ftrack AB

# Set default FTRACK_CONNECT_PACKAGE_VERSION version to master
ENV FTRACK_CONNECT_PACKAGE_VERSION master

# Define Python Version to build and use
ENV PYTHON_VERSION 2.7.9

# Ftrack required environments
# Legacy Plugins
ENV FTRACK_CONNECT_LEGACY_PLUGINS_PATH /opt/ftrack-connect-legacy-plugins
ENV FTRACK_CONNECT_LEGACY_PLUGINS_VERSION master

# Legacy API
ENV FTRACK_LEGACY_PYTHON_API_PATH /opt/ftrack-python-legacy-api
ENV FTRACK_LEGACY_PYTHON_API_VERSION master

# Utility environments
ENV OUT_FOLDER build
ENV BUILD_DIR /opt/ftrack-connect-package-${FTRACK_CONNECT_PACKAGE_VERSION}

#########################################################################
# ----------------------- SYSTEM SETUP ----------------------------------

# Use 6 parallel processes for builds.
ENV MAKEFLAGS -j6

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
# -----------------------RUN ENTRYPOINT-------------------------
VOLUME /${OUT_FOLDER}

COPY ./run.sh /
RUN chmod +x /run.sh
ENTRYPOINT ["/run.sh"]
