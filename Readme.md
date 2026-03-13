Join multiple lines
===================
Original work by Daan Goedkoop

Fork by Eithan Weiss Schonberg

Introduction
------------

After selecting multiple features of a line layer, this plugin can merge
them into one feature with a continuous line.

The plugin will automatically put the selected lines in a geographically
logical order and direction. If the end points of two lines do not match
exactly, a line segment between both points is added to make the end result
a single, continuous line. The attributes of the new line will be those of
one of the selected features, but one cannot predict which one.

Testing
-------

A test project / layer has been supplied to experiment with and see the
characteristics of the plugin.

Version history
---------------

* 1.0.0: 2026-03-13
     * QGIS 4 compatibility
     * Class and method name changes
     * Code refactoring and cleanup
* 0.4.1: 2018-11-30
     * Bug fix for displaying warnings
* 0.4: 2018-01-22
     * Update for QGis 3.0
     * Support multi-part lines
* 0.3: 2014-02-03
     * Update for QGis 2.0
     * Operation is now a single undo/redo-step, instead of having a
       separate step for the removal of the superfluous features.
* 0.2: 2013-04-29
     * Produce valid geometry if begin and end vertices are identical.
* 0.1: 2013-04-26
     * Initial version