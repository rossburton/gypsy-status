#! /usr/bin/python
#
# Copyright (C) 2008 Ross Burton <ross@openedhand.com>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
# St, Fifth Floor, Boston, MA 02110-1301 USA

import sys, time
import gypsy, gtk
from dbus.mainloop.glib import DBusGMainLoop

def error_handler(exception):
    # TODO: display dialog
    print exception


# Base class for GPS-using widgets to derive from.
class GpsWidget(gtk.Widget):
    def __init__(self, gps):
        gtk.Widget.__init__(self)
        self.set_gps(gps)
        
    def set_gps(self, gps):
        raise NotImplementedError


# A GtkLabel which displays the latest time as reported by the GPS.
class GpsTimeLabel(GpsWidget, gtk.Label):
    def __init__(self, gps):
        GpsWidget.__init__(self, gps)
        gtk.Label.__init__(self)
        self.set_selectable(True)

    def set_gps(self, gps):
        self.device = gps["Time"]
        self.device.connect_to_signal("TimeChanged", self.time_changed)
        self.device.GetTime(reply_handler=self.time_changed, error_handler=error_handler)
        
    def time_changed(self, timestamp):
        if timestamp:
            self.set_text(time.strftime("%c", time.gmtime(timestamp)))
        else:
            self.set_text("unavailable")


# A statusbar which displays the fix status of the GPS
class GpsFixStatusbar(GpsWidget, gtk.Statusbar):
    def __init__(self, gps):
        GpsWidget.__init__(self, gps)
        gtk.Statusbar.__init__(self)
        self.context = self.get_context_id("FixStatus")

    def set_gps(self, gps):
        self.device = gps["Device"]
        self.device.connect_to_signal("FixStatusChanged", self.fix_changed)
        self.device.GetFixStatus(reply_handler=self.fix_changed, error_handler=error_handler)

    def fix_changed(self, fix):
        self.pop(self.context)
        if fix == gypsy.DEVICE_FIX_STATUS_NONE:
            self.push(self.context, "No fix obtained")
        elif fix == gypsy.DEVICE_FIX_STATUS_2D:
            self.push(self.context, "2D fix obtained")
        elif fix == gypsy.DEVICE_FIX_STATUS_3D:
            self.push(self.context, "3D fix obtained")
        else:
            self.push(self.context, "Invalid fix")


# A GtkLabel showing the dilution of precision.
class GpsAccuracyLabel(GpsWidget, gtk.Label):
    def __init__(self, gps):
        GpsWidget.__init__(self, gps)
        gtk.Label.__init__(self)
        self.set_selectable(True)

    def set_gps(self, gps):
        self.device = gps["Accuracy"]
        self.device.connect_to_signal("AccuracyChanged", self.changed)
        self.device.GetAccuracy(reply_handler=self.changed, error_handler=error_handler)

    def changed(self, fields, pdop, hdop, vdop):
        self.set_text("Positional DOP %.2f, Horizonatal DOP %.2f, Vertical DOP %.2f" % (
            (fields & gypsy.ACCURACY_FIELDS_POSITION) and pdop or 0,
            (fields & gypsy.ACCURACY_FIELDS_HORIZONTAL) and hdop or 0,
            (fields & gypsy.ACCURACY_FIELDS_VERTICAL) and vdop or 0))


# A GtkLabel showing the current latitude
class GpsLatitudeLabel(GpsWidget, gtk.Label):
    def __init__(self, gps):
        GpsWidget.__init__(self, gps)
        gtk.Label.__init__(self)
        self.set_selectable(True)

    def set_gps(self, gps):
        self.device = gps["Position"]
        self.device.connect_to_signal("PositionChanged", self.changed)
        self.device.GetPosition(reply_handler=self.changed, error_handler=error_handler)
        
    def changed(self, fields, timestamp, latitude, longitude, altitude):
        if fields & gypsy.POSITION_FIELDS_LATITUDE:
            self.set_text("%+.5f\302\260" % latitude)
        else:
            self.set_text("Unknown latitude")


# A GtkLabel showing the current longitude
class GpsLongitudeLabel(GpsWidget, gtk.Label):
    def __init__(self, gps):
        GpsWidget.__init__(self, gps)
        gtk.Label.__init__(self)
        self.set_selectable(True)

    def set_gps(self, gps):
        self.device = gps["Position"]
        self.device.connect_to_signal("PositionChanged", self.changed)
        self.device.GetPosition(reply_handler=self.changed, error_handler=error_handler)
        
    def changed(self, fields, timestamp, latitude, longitude, altitude):
        if fields & gypsy.POSITION_FIELDS_LONGITUDE:
            self.set_text("%+.5f\302\260" % longitude)
        else:
            self.set_text("Unknown longitude")


# A GtkLabel showing the current altitude
class GpsAltitudeLabel(GpsWidget, gtk.Label):
    def __init__(self, gps):
        GpsWidget.__init__(self, gps)
        gtk.Label.__init__(self)
        self.set_selectable(True)

    def set_gps(self, gps):
        self.device = gps["Position"]
        self.device.connect_to_signal("PositionChanged", self.changed)
        self.device.GetPosition(reply_handler=self.changed, error_handler=error_handler)
        
    def changed(self, fields, timestamp, latitude, longitude, altitude):
        if fields & gypsy.POSITION_FIELDS_ALTITUDE:
            self.set_text("%.1fm" % altitude)
        else:
            self.set_text("Unknown altitude")


# A widget showing the current satellites and their signal strength
class GpsSatelliteChart(GpsWidget, gtk.HBox):
    def __init__(self, gps):
        GpsWidget.__init__(self, gps)
        gtk.HBox.__init__(self, True, 2)

    def set_gps(self, gps):
        self.device = gps['Satellite']
        self.device.connect_to_signal("SatellitesChanged", self.changed)
        self.device.GetSatellites(reply_handler=self.changed, error_handler=error_handler)

    def changed(self, sats):
        sats.sort(key=lambda s: s[0])
        self.foreach(lambda w: self.remove(w))
        
        for sat in sats:
            box = gtk.VBox(False, 2)
            
            l = gtk.Label()
            if sat[1]:
                l.set_markup("<b>%d</b>" % sat[0])
            else:
                l.set_text("%d" % sat[0])
                l.set_sensitive(False)
            box.pack_start(l, False, False, 0)
            
            bar = gtk.ProgressBar()
            bar.set_orientation(gtk.PROGRESS_BOTTOM_TO_TOP)
            bar.set_fraction(float(sat[4])/100)
            box.add(bar)
            
            box.show_all()
            self.add(box)


# An image showing a map view of the area, from OpenStreetMap
import osmgpsmap

class OsmMapView(GpsWidget, osmgpsmap.GpsMap):
    def __init__(self, gps):
        GpsWidget.__init__(self, gps)
        osmgpsmap.GpsMap.__init__(self)
        self.add_layer(osmgpsmap.GpsMapOsd(show_dpad=False, show_zoom=True))
        self.set_zoom(12)

    def set_gps(self, gps):
        self.device = gps["Position"]
        self.device.connect_to_signal("PositionChanged", self.changed)
        self.device.GetPosition(reply_handler=self.changed, error_handler=error_handler)

    def changed(self, fields, timestamp, latitude, longitude, altitude):
        if fields & (gypsy.POSITION_FIELDS_LONGITUDE + gypsy.POSITION_FIELDS_LATITUDE):
            self.set_center (latitude, longitude);
            self.draw_gps(latitude, longitude, osmgpsmap.INVALID)

# An image showing a satellite view of the area, hacked from Google Maps.
class GoogleSatelliteView(GpsWidget, gtk.Image):
    def __init__(self, gps):
        GpsWidget.__init__(self, gps)
        gtk.Image.__init__(self)
        self.current_quad = None

    def set_gps(self, gps):
        self.device = gps["Position"]
        self.device.connect_to_signal("PositionChanged", self.changed)
        self.device.GetPosition(reply_handler=self.changed, error_handler=error_handler)
        
    def changed(self, fields, timestamp, latitude, longitude, altitude):
        import urllib2
        if fields & (gypsy.POSITION_FIELDS_LONGITUDE + gypsy.POSITION_FIELDS_LATITUDE):
            quad = self.longlat_to_quad(longitude, latitude)
            if (quad == self.current_quad):
                return
            self.current_quad = quad
            url = "http://kh0.google.co.uk/kh?n=404&v=23&t=%s" % quad
            data = ''.join(urllib2.urlopen(url).readlines())
            loader = gtk.gdk.PixbufLoader()
            loader.write(data)
            loader.close()
            pixbuf = loader.get_pixbuf()
            self.set_from_pixbuf(pixbuf)
    
    def longlat_to_quad(self, longitude, latitude):
        import math
        x = (180.0 + longitude) / 360.0
        y = math.radians(-latitude)
        y = 0.5 * math.log((1 + math.sin(y)) / (1 - math.sin(y)))
        y *= 1.0 / (2 * math.pi)
        y += 0.5
        
        lookup = "qrts"
        digits = 16
        quad = "t"
        while digits > 0:
            x -= int(x)
            y -= int(y)
            quad = quad + lookup[(x >= 0.5 and 1 or 0) + (y >= 0.5 and 2 or 0)]
            x = x * 2
            y = y * 2
            digits = digits - 1
        return quad


# An image showing a street map of the local area, using the Yahoo mapping
# service.
class YahooMapView(GpsWidget, gtk.Image):
    
    appid = "c0ifISrV34Gd86w2vO.o2KYw_MeEAeogclikp6Atdw3VxzYACBhf8mwHiBX9oJS73YSM"
    
    def __init__(self, gps):
        GpsWidget.__init__(self, gps)
        gtk.Image.__init__(self)
        
        self.current_lat = None
        self.current_lon = None
        self.current_url = None

    def set_gps(self, gps):
        self.device = gps["Position"]
        self.device.connect_to_signal("PositionChanged", self.changed)
        self.device.GetPosition(reply_handler=self.changed, error_handler=error_handler)

    def changed(self, fields, timestamp, latitude, longitude, altitude):
        from urllib import urlopen, urlencode
        import xml.etree.ElementTree as etree

        if fields & (gypsy.POSITION_FIELDS_LONGITUDE + gypsy.POSITION_FIELDS_LATITUDE):
            if round(latitude, 3) == self.current_lat and round (longitude, 3) == self.current_lon:
                return
            
            print latitude, self.current_lat
            print longitude, self.current_lon
            
            self.current_lat = round(latitude, 3)
            self.current_lon = round(longitude, 3)
            
            # TODO: use Twisted or do this in a thread
            url = "http://local.yahooapis.com/MapsService/V1/mapImage"
            query = {
                "appid": self.appid,
                "image_width": 200,
                "image_height": 200,
                "zoom": 3,
                "latitude": latitude,
                "longitude": longitude
                }
            rsp = etree.parse(urlopen(url, urlencode(query))).getroot()
            if rsp.tag != "Result":
                self.clear()
                return
            url = rsp.text

            # Don't reload if the URL hasn't changed
            if url == self.current_url:
                return
            self.current_url = url
            
            loader = gtk.gdk.PixbufLoader()
            for d in urlopen(rsp.text):
                loader.write(d)
            loader.close()
            pixbuf = loader.get_pixbuf()
            self.set_from_pixbuf(pixbuf)


DBusGMainLoop(set_as_default=True)

if len(sys.argv) > 1:
    gps = gypsy.GPS(sys.argv[1])
else:
    gps = gypsy.GPS("/dev/ttyUSB0")
gps['Device'].Start()

window = gtk.Window()
window.connect("delete-event", gtk.main_quit)
window.set_default_size(400, 300)
window.set_title("Gypsy Status")

box = gtk.VBox(False, 0)
window.add(box)

table = gtk.Table(5, 3, False)
table.set_border_width(8)
table.set_row_spacings(8)
table.set_col_spacings(8)
box.pack_start(table, True, True, 0)

widgets = (
    ("GPS Time", GpsTimeLabel),
    ("Latitude", GpsLatitudeLabel),
    ("Longitude", GpsLongitudeLabel),
    ("Altitude", GpsAltitudeLabel),
    ("Accuracy", GpsAccuracyLabel)
    )
y = 0
for (l, w) in widgets:
    label = gtk.Label("<b>%s:</b>" % l)
    label.set_use_markup(True)
    label.set_alignment(0.0, 0.0)
    table.attach(label, 0, 1, y, y+1, xoptions=gtk.FILL)
    label = w(gps)
    label.set_alignment(0.0, 0.0)
    table.attach(label, 1, 2, y, y+1, xoptions=gtk.FILL)
    y = y + 1

table.attach(OsmMapView(gps), 2, 3, 0, y)

table.attach(GpsSatelliteChart(gps), 0, 3, y, y+1)

statusbar = GpsFixStatusbar(gps)
box.pack_start(statusbar, False, False, 0)


window.show_all()
gtk.main()
