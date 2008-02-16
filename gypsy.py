# Copyright (C) 2008 Ross Burton <ross@openedhand.com>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

import dbus

DBUS_SERVICE = "org.freedesktop.Gypsy"
DBUS_PATH= "/org/freedesktop/Gypsy"

ACCURACY_FIELDS_NONE = 0
ACCURACY_FIELDS_POSITION = 1 << 0
ACCURACY_FIELDS_HORIZONTAL = 1 << 1
ACCURACY_FIELDS_VERTICAL = 1 << 2

COURSE_FIELDS_NONE = 0
COURSE_FIELDS_SPEED = 1 << 0
COURSE_FIELDS_DIRECTION = 1 << 1
COURSE_FIELDS_CLIMB = 1 << 2

POSITION_FIELDS_NONE = 0
POSITION_FIELDS_LATITUDE = 1 << 0
POSITION_FIELDS_LONGITUDE = 1 << 1
POSITION_FIELDS_ALTITUDE = 1 << 2

DEVICE_FIX_STATUS_INVALID = 0
DEVICE_FIX_STATUS_NONE = 1
DEVICE_FIX_STATUS_2D = 2
DEVICE_FIX_STATUS_3D = 3


class Control(dbus.proxies.ProxyObject):
    def __init__(self):
        dbus.proxies.ProxyObject.__init__(self,
                                          bus=dbus.SystemBus(),
                                          named_service=DBUS_SERVICE,
                                          object_path=DBUS_PATH)


class GPS(dbus.proxies.ProxyObject):
    def __init__(self, device=None, path=None):
        if not device and not path:
            raise Error("device or path need to be specified")
        
        if path is None:
            path = Control().Create(device)
        
        dbus.proxies.ProxyObject.__init__(self,
                                          bus=dbus.SystemBus(),
                                          named_service=DBUS_SERVICE,
                                          object_path=path)
    
    def __getitem__(self, name):
        # TODO: bother with this, or just create the interface name?
        if name in ("Accuracy", "Course", "Device", "Position", "Satellite", "Time"):
            return dbus.Interface(self, dbus_interface="org.freedesktop.Gypsy." + name)
        else:
            raise Exception("Unknown interface %s", name)


if __name__ == "__main__":
    import gobject, dbus.mainloop.glib
    
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    gps = GPS("00:0B:0D:88:A4:A3")
    gps.Start()
    
    def position_changed(fields, timestamp, latitude, longitude, altitude):
        print "%d: %2f, %2f (%1fm)" % (
            timestamp,
            (fields & POSITION_FIELDS_LATITUDE) and latitude or 0,
            (fields & POSITION_FIELDS_LONGITUDE) and longitude or 0,
            (fields & POSITION_FIELDS_ALTITUDE) and altitude or 0)
    gps['Position'].connect_to_signal("PositionChanged", position_changed)

    gobject.MainLoop().run()
