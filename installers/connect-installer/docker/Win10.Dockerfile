# escape=`
#########################################################################
# :copyright: Copyright (c) 2024 ftrack
#

FROM winamd64/python:3.7
LABEL ftrack AB

# Install MinGit
RUN Invoke-WebRequest 'https://github.com/git-for-windows/git/releases/download/v2.26.0.windows.1/MinGit-2.26.0-busybox-64-bit.zip' -OutFile mingit.zip; `
    Expand-Archive c:\mingit.zip -DestinationPath c:\MinGit; `
    Remove-Item c:\mingit.zip; `
    setx /M PATH $($Env:PATH + ';C:\MinGit\cmd')

# Install BuildTools
RUN Invoke-WebRequest "https://aka.ms/vs/16/release/vs_buildtools.exe" -OutFile vs_buildtools.exe; `
    Start-Process vs_buildtools.exe -Wait -ArgumentList '`
    --quiet `
    --wait `
    --norestart `
    --nocache `
    --installPath C:\BuildTools `
    --add Microsoft.VisualStudio.Workload.MSBuildTools `
    --add Microsoft.VisualStudio.Workload.VCTools ` 
    --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 ` 
    --add Microsoft.VisualStudio.Component.Windows10SDK.18362 ` 
    --add Microsoft.VisualStudio.Component.VC.CMake.Project ` 
    --add Microsoft.VisualStudio.Component.TestTools.BuildTools ` 
    --add Microsoft.VisualStudio.Component.VC.ASAN ` 
    --add Microsoft.VisualStudio.Component.VC.140'; `
    Remove-Item c:\vs_buildtools.exe

# create build app folder
RUN mkdir -p /usr/src/app

# update/install base dependencies using pip and wheel so can be fully found by cx_freeze
# this has to run before connect tries to install its (same) dependencies in egg.
RUN python -m pip install --upgrade pip

# install connect
WORKDIR /usr/src/app
RUN git clone -b master https://bitbucket.org/ftrack/ftrack-connect.git
WORKDIR /usr/src/app/ftrack-connect
RUN git fetch 
RUN git fetch --tag

RUN python -m pip install -r requirements.txt

# ensure pyside2-rcc and pyside2-uic are available in PATH
RUN setx /M PATH $($Env:PATH + ';C:\Python\Lib\site-packages\PySide2')

RUN python setup.py install

# install connect package
WORKDIR /usr/src/app
RUN git clone -b master https://bitbucket.org/ftrack/ftrack-connect-installer.git
WORKDIR /usr/src/app/ftrack-connect-installer
RUN git fetch 
RUN git fetch --tag

RUN python -m pip install -r requirements.txt
RUN python setup.py bdist_msi
RUN dir dist
