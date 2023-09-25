ftrack Framework for Photoshop CEP (soon to be deprecated) plugin
=================================================================

# Development

To enable live development, first allow unsigned extensions:

    $ defaults write com.adobe.CSXS.8 PlayerDebugMode 1


Install ZXP extension and then open up permissions on folder:

    $ sudo chmod -R 777 "/library/application support/adobe/cep/extensions/com.ftrack.framework.photoshop.panel"

You are now ready to do live changes to extension, remember to sync back changes to
source folder before committing.


# Build

Set variables:

    FTRACK_ADOBE_CERTIFICATE_PASSWORD=<Adobe exchange vault entry>

Create Adobe extension:

    $ python tests/build.py build_cep


# Install

Use "Extension Manager" tool provided here: https://install.anastasiy.com/ to install 
the built xzp plugin. Remember to remove previous ftrack extensions.
