#! /usr/bin/python

import time
import gypsy, gtk
from dbus.mainloop.glib import DBusGMainLoop

def error_handler(exception):
    # TODO: display dialog
    print exception

# A GtkLabel which displays the latest time as reported by the GPS.
class GpsTimeLabel(gtk.Label):
    def __init__(self, gps):
        gtk.Label.__init__(self)
        self.set_selectable(True)
        self.device = gps["Time"]
        self.device.connect_to_signal("TimeChanged", self.time_changed)
        self.device.GetTime(reply_handler=self.time_changed, error_handler=error_handler)

    def time_changed(self, timestamp):
        if timestamp:
            self.set_text(time.strftime("%c", time.gmtime(timestamp)))
        else:
            self.set_text("unavailable")


# A statusbar which displays the fix status of the GPS
class GpsFixStatusbar(gtk.Statusbar):
    def __init__(self, gps):
        gtk.Statusbar.__init__(self)
        self.context = self.get_context_id("FixStatus")
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


class GpsAccuracyLabel(gtk.Label):
    def __init__(self, gps):
        gtk.Label.__init__(self)
        self.set_selectable(True)
        self.device = gps["Accuracy"]
        self.device.connect_to_signal("AccuracyChanged", self.changed)
        self.device.GetAccuracy(reply_handler=self.changed, error_handler=error_handler)

    def changed(self, fields, pdop, hdop, vdop):
        self.set_text("Positional DOP %.2f, Horizonatal DOP %.2f, Vertical DOP %.2f" % (
            (fields & gypsy.ACCURACY_FIELDS_POSITION) and pdop or 0,
            (fields & gypsy.ACCURACY_FIELDS_HORIZONTAL) and hdop or 0,
            (fields & gypsy.ACCURACY_FIELDS_VERTICAL) and vdop or 0))


class GpsLatitudeLabel(gtk.Label):
    def __init__(self, gps):
        gtk.Label.__init__(self)
        self.set_selectable(True)
        self.device = gps["Position"]
        self.device.connect_to_signal("PositionChanged", self.changed)
        self.device.GetPosition(reply_handler=self.changed, error_handler=error_handler)
        
    def changed(self, fields, timestamp, latitude, longitude, altitude):
        if fields & gypsy.POSITION_FIELDS_LATITUDE:
            self.set_text("%+.5f\302\260" % latitude)
        else:
            self.set_text("Unknown latitude")

class GpsLongitudeLabel(gtk.Label):
    def __init__(self, gps):
        gtk.Label.__init__(self)
        self.set_selectable(True)
        self.device = gps["Position"]
        self.device.connect_to_signal("PositionChanged", self.changed)
        self.device.GetPosition(reply_handler=self.changed, error_handler=error_handler)
        
    def changed(self, fields, timestamp, latitude, longitude, altitude):
        if fields & gypsy.POSITION_FIELDS_LONGITUDE:
            self.set_text("%+.5f\302\260" % longitude)
        else:
            self.set_text("Unknown longitude")


class GpsAltitudeLabel(gtk.Label):
    def __init__(self, gps):
        gtk.Label.__init__(self)
        self.set_selectable(True)
        self.device = gps["Position"]
        self.device.connect_to_signal("PositionChanged", self.changed)
        self.device.GetPosition(reply_handler=self.changed, error_handler=error_handler)
        
    def changed(self, fields, timestamp, latitude, longitude, altitude):
        if fields & gypsy.POSITION_FIELDS_ALTITUDE:
            self.set_text("%.1fm" % altitude)
        else:
            self.set_text("Unknown altitude")


class GpsSatelliteChart(gtk.HBox):
    def __init__(self, gps):
        gtk.HBox.__init__(self, True, 2)
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


DBusGMainLoop(set_as_default=True)

gps = gypsy.GPS("00:0B:0D:88:A4:A3")
gps.Start()

window = gtk.Window()
window.connect("delete-event", gtk.main_quit)
window.set_default_size(400, 300)
window.set_title("Gypsy Status")

box = gtk.VBox(False, 0)
window.add(box)

table = gtk.Table(5, 2, False)
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
    table.attach(label, 0, 1, y, y+1, xoptions=gtk.FILL, yoptions=gtk.FILL)
    label = w(gps)
    label.set_alignment(0.0, 0.0)
    table.attach(label, 1, 2, y, y+1, yoptions=gtk.FILL)
    y = y + 1

table.attach(GpsSatelliteChart(gps), 0, 2, y, y+1)

statusbar = GpsFixStatusbar(gps)
box.pack_start(statusbar, False, False, 0)

window.show_all()
gtk.main()
