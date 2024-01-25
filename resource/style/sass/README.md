# Stylesheets

## Structure

The files [style_light.scss]{.title-ref} and
[style_dark.scss]{.title-ref} are compiled (using Compass) to the two
QSS stylesheets [style_light.css]{.title-ref} and
[style_dark.css]{.title-ref}. The only difference between the theme
files should be which of the two [\_colors\_]{.title-ref} files they
include.

\_variables.scss

:   Contains common variables, such as fonts and sizes.

\_[colors]()\*

:   Contains theme-specific color variables.

widget

:   Styling for different QT widgets, such as buttons, inputs etc..

module

:   Contains styling for specific modules.

## Compiling stylesheets

See libs/qt-style/README.md for instructions on how to compile the Monorepo stylesheets.