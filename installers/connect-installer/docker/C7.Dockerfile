#########################################################################
# :copyright: Copyright (c) 2014-2023 ftrack
#

FROM inveniosoftware/centos7-python:3.6
LABEL ftrack AB

RUN yum -y update
RUN yum -y groupinstall "Development Tools"

RUN yum install -y *libxcb* libXi libSM fontconfig libXrender libxkbcommon-x11 qt5* patchelf

RUN python -m pip install --upgrade pip

RUN mkdir -p /usr/src/app

# install connect
WORKDIR /usr/src/app
RUN git clone -b master https://bitbucket.org/ftrack/ftrack-connect.git
WORKDIR /usr/src/app/ftrack-connect
RUN git fetch 
RUN python -m pip install -r requirements.txt
RUN python setup.py install

# install connect package
WORKDIR /usr/src/app
RUN git clone -b master https://bitbucket.org/ftrack/ftrack-connect-installer.git
WORKDIR /usr/src/app/ftrack-connect-installer
RUN git fetch 

RUN python -m pip install -r requirements.txt
RUN python setup.py build

WORKDIR /usr/src/app/ftrack-connect-installer/build
RUN tar -czvf ftrack\ Connect-2.0-C7.tar.gz exe.linux-x86_64-3.6
