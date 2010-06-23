Gypsy Status
============

Overview
--------
A status monitor for Gypsy that displays the current location and accuracy,
time, satellite information, and a visual map of the area.


Requirements
------------

Python, DBus, python-dbus, osmgpsmap


Usage
-----

    $ ./status.py

By default Gypsy Status will tell Gypsy to use the GPS at `/dev/ttyUSB0`.  If
this is not right for you, pass the location:

    $ ./status.py 00:0B:0D:88:A4:A3
