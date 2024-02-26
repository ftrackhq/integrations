#########################################################################
# :copyright: Copyright (c) 2024 ftrack
#

FROM inveniosoftware/centos8-python:3.7
LABEL ftrack AB

# patch repos url
RUN sed -i -e "s|mirrorlist=|#mirrorlist=|g" /etc/yum.repos.d/CentOS-*
RUN sed -i -e "s|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g" /etc/yum.repos.d/CentOS-*

RUN dnf -y update
RUN dnf -y groupinstall "Development Tools"

RUN dnf install -y *libxcb* libXi libSM fontconfig libXrender libxkbcommon-x11 qt5* patchelf --skip-broken

RUN python3.7 -m pip install --upgrade pip

RUN mkdir -p /usr/src/app

# install connect
WORKDIR /usr/src/app
RUN git clone -b master https://bitbucket.org/ftrack/ftrack-connect.git
WORKDIR /usr/src/app/ftrack-connect
RUN git fetch 
RUN python3.7 -m pip install -r requirements.txt
RUN python3.7 setup.py install

# install connect package
WORKDIR /usr/src/app
RUN git clone -b master https://bitbucket.org/ftrack/ftrack-connect-installer.git
WORKDIR /usr/src/app/ftrack-connect-installer
RUN git fetch 

RUN python3.7 -m pip install -r requirements.txt
RUN python3.7 setup.py build

WORKDIR /usr/src/app/ftrack-connect-installer/build
RUN tar -czvf ftrack\ Connect-2.0-C8.tar.gz exe.linux-x86_64-3.7
