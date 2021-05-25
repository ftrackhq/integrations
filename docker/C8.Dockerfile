#########################################################################
# :copyright: Copyright (c) 2020 ftrack
#

FROM inveniosoftware/centos8-python:3.7
LABEL ftrack AB

RUN dnf -y update
RUN dnf -y groupinstall "Development Tools"

RUN dnf install -y *libxcb* libXi libSM fontconfig libXrender libxkbcommon-x11 qt5* --skip-broken

RUN python3.7 -m pip install --upgrade pip

RUN mkdir -p /usr/src/app

# install connect
WORKDIR /usr/src/app
RUN git clone -b backlog/connect-2/story https://bitbucket.org/ftrack/ftrack-connect.git
WORKDIR /usr/src/app/ftrack-connect
RUN git fetch 
RUN python3.7 -m pip install -r requirements.txt
RUN python3.7 setup.py install

# install connect package
WORKDIR /usr/src/app
RUN git clone -b backlog/connect-2/story https://bitbucket.org/ftrack/ftrack-connect-package.git
WORKDIR /usr/src/app/ftrack-connect-package
RUN git fetch 

RUN python3.7 -m pip install -r requirements.txt
RUN python3.7 setup.py build

WORKDIR /usr/src/app/ftrack-connect-package/build
RUN tar -czvf ftrack\ Connect-2.0-C8.tar.gz exe.linux-x86_64-3.7