#!/usr/bin/env python
# encoding: utf-8
#    Copyright 2014 Tobias Mueller <muelli@cryptobitch.de>
#    Copyright 2015 Jody Hansen <jobediah.hansen@gmail.com>
#
#    This file is part of GNOME Keysign.
#
#    GNOME Keysign is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    GNOME Keysign is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with GNOME Keysign.  If not, see <http://www.gnu.org/licenses/>.

import logging
import sys
from _dbus_glib_bindings import DBusGMainLoop
import dbus, avahi
from gi.repository import GObject

from gi.repository import Gtk, Gio, GLib

class SigneesApp(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, application_id="org.gnome.keysign.signeesapp",
                                 flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("startup", self.on_startup)
        self.connect("activate", self.on_activate)

        self.log = logging.getLogger()

    def on_startup(self, data=None):
        service='_geysign._tcp'

        loop = DBusGMainLoop(set_as_default=True)

        bus = dbus.SystemBus(mainloop=loop)

        self._server = dbus.Interface(bus.get_object(avahi.DBUS_NAME, avahi.DBUS_PATH_SERVER), avahi.DBUS_INTERFACE_SERVER)

        browser = self._server.ServiceBrowserNew(avahi.IF_UNSPEC, avahi.PROTO_INET, service, '', 0)
        listener = dbus.Interface(bus.get_object(avahi.DBUS_NAME, browser), avahi.DBUS_INTERFACE_SERVICE_BROWSER)

        listener.connect_to_signal("ItemNew", self.item_new_handler)
        listener.connect_to_signal("ItemRemove", self.item_remove_handler)

        self.client_list = []

        self._mainloop = GObject.MainLoop()
        self.connect("delete-event", self.on_quit)

        GLib.idle_add(self.browse)


    def on_activate(self, data=None):
        window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        window.set_title("SigneesApp")
        window.set_border_width(30)
        self.label = Gtk.Label("Hello World!")
        self.label.set_markup("<b><big>The number of signees on network are:"
                              " %s</big></b>"%0)
        window.add(self.label)
        window.show_all()
        self.add_window(window)


    def on_quit(self, data=None):
        self._mainloop.quit()


    def browse(self):
        self._mainloop.run()


    def service_resolved(self, interface, protocol, name, stype, domain,
                         host, aprotocol, address, port, txt, flags):
        self.client_list.append(name)
        self.log.info("Clients currently in list '%s'", self.client_list)
        self.reset_label(self.client_list)


    def item_new_handler(self, interface, protocol, name, stype, domain, flags):
        self.log.info("Adding service: %s: %s: %s", name, stype, domain)
        self._server.ResolveService(interface, protocol, name, stype, domain,
                                    avahi.PROTO_UNSPEC, dbus.UInt32(0),
                                    reply_handler=self.service_resolved,
                                    error_handler=self.print_error)


    def item_remove_handler(self, interface, protocol, name, stype, domain, flags):
        self.log.info("Removing service: %s: %s: %s", name, stype, domain)
        if name in self.client_list: self.client_list.remove(name)
        self.log.info("Clients currently in list '%s'", self.client_list)
        self.reset_label(self.client_list)


    def print_error(self, *args):
        self.log.warn('error_handler')
        print args[0]


    def reset_label(self,data):
        data = len(set(data))
        self.log.info("Reseting the label")
        self.label.set_markup("<b><big>The number of signees on network are:"
                              " %s</big></b>"%data)



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = SigneesApp()
    app.run(None)