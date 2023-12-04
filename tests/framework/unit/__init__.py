import sys
import os

ROOT_INTEGRATIONS_FOLDER = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
)

INCLUDE_PACKAGES = [
    'libs/constants',
    'libs/framework-core',
    'libs/framework-engine',
    'libs/framework-plugin',
    # QT
    'libs/framework-widget',
    'libs/framework-qt',
    'libs/qt',
    'libs/qt-style',
    'libs/utils',
]

for _package in INCLUDE_PACKAGES:
    sys.path.append(os.path.join(ROOT_INTEGRATIONS_FOLDER, _package, "source"))
