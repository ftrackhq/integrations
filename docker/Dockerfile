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

# Legacy API
ENV FTRACK_LEGACY_PYTHON_API_PATH /opt/ftrack-python-legacy-api
ENV FTRACK_LEGACY_PYTHON_API_VERSION 3.6.3

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
    bzip2 \
    bzip2-devel \
    cmake \
    db4-devel \
    expat-devel \
    gdbm-devel \
    git \
    glibc-devel.i686 \
    glibc-devel.x86_64 \
    libffi-devel \
    libffi\
    libicu \
    libicu-devel\
    libpcap-devel \
    libxml2\
    libxslt\
    ncurses-devel \
    openssl \
    openssl-devel \
    python-devel\
    python-pyside\
    python-virtualenv\
    qt-devel\
    readline-devel \
    sqlite \
    sqlite-devel \
    tar \
    tk-devel \
    wget \
    xz-devel \
    zlib-devel \
    patchelf;

RUN wget http://python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz -P /tmp
RUN cd /tmp && tar xf Python-${PYTHON_VERSION}.tar.xz
RUN cd /tmp/Python-${PYTHON_VERSION} && \
    /tmp/Python-${PYTHON_VERSION}/configure \
        --prefix=/usr/local \
        --enable-unicode=ucs4 \
        --with-ensurepip=yes \
        --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib" \
    && make && make altinstall


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
