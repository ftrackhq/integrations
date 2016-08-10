Stylesheets
===========

Structure
----------

The files `style_light.scss` and `style_dark.scss` are compiled (using Compass)
to the two QSS stylesheets `style_light.css` and `style_dark.css`. The only
difference between the theme files should be which of the two `_colors_` files
they include.

_variables.scss
	Contains common variables, such as fonts and sizes.

_colors_*
	Contains theme-specific color variables.

widget
	Styling for different QT widgets, such as buttons, inputs etc..

module
	Contains styling for specific modules.


Compiling stylesheets
---------------------

Use SASS and Compass to generate the Qt Stylesheet used by the application.
First, make sure you have compass installed. It can be installed using rubygems::

	gem install compass

To build the styles, stand in this directory (sass), and run::

	compass watch .

