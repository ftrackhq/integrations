#########################################################################
# :copyright: Copyright (c) 2020 ftrack
#

FROM winamd64/python:3.7
LABEL ftrack AB

# install git and ensure is in PATH
RUN Invoke-WebRequest 'https://github.com/git-for-windows/git/releases/download/v2.12.2.windows.2/MinGit-2.12.2.2-64-bit.zip' -OutFile MinGit.zip
RUN Expand-Archive c:\MinGit.zip -DestinationPath c:\MinGit; \
$env:PATH = $env:PATH + ';C:\MinGit\cmd\;C:\MinGit\cmd'; \
Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment\' -Name Path -Value $env:PATH

# create build app folder
RUN mkdir -p /usr/src/app

# update/install base dependencies using pip and wheel so can be fully found by cx_freeze
# this has to run before connect tries to install its (same) dependencies in egg.
RUN python -m pip install --upgrade pip
RUN python -m pip install PySide2, wheel, cx_freeze, appdirs, arrow, certifi, chardet, clique, lowdown, ftrack-python-api, riffle

# ensure pyside2-rcc and pyside2-uic are available in PATH
RUN $env:PATH = $env:PATH + ';C:\Python\Lib\site-packages\PySide2\;C:\Python\Lib\site-packages\PySide2'; \
Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment\' -Name Path -Value $env:PATH

# install connect
WORKDIR /usr/src/app
RUN git clone -b backlog/connect-2/story https://bitbucket.org/ftrack/ftrack-connect.git
WORKDIR /usr/src/app/ftrack-connect
RUN python -m pip install -r requirements.txt
RUN python setup.py install

# install connect package
WORKDIR /usr/src/app
RUN git clone -b backlog/connect-2/cx_freeze_latest https://bitbucket.org/ftrack/ftrack-connect-package.git
WORKDIR /usr/src/app/ftrack-connect-package
RUN python -m pip install -r requirements.txt
RUN python setup.py bdist_msi
