#!/usr/bin/env python
#    Copyright 2014 Andrei Macavei <andrei.macavei89@gmail.com>
#    Copyright 2014 Tobias Mueller <muelli@cryptobitch.de>
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

from GetKeySection import GetKeySection

from network.AvahiBrowser import AvahiBrowser

from gi.repository import Gtk, GLib, Gio
import logging
import sys

class GnomeKeysignClient(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self)
        self.connect("activate", self.on_activate)
        self.connect("startup", self.on_startup)

        self.log = logging.getLogger()
        self.log = logging

    def on_quit(self, app, param=None):
        self.quit()


    def on_startup(self, app):
        self.log.info("Startup")
        self.window = Gtk.ApplicationWindow(application=app)
        self.window.set_title ("Keysign")

        self.window.set_border_width(10)
        self.window.set_position(Gtk.WindowPosition.CENTER)

        # create notebook container
        notebook = Gtk.Notebook()
        notebook.append_page(GetKeySection(self), Gtk.Label('Get Key'))
        self.window.add(notebook)

        quit = Gio.SimpleAction(name="quit", parameter_type=None)
        self.add_action(quit)
        self.add_accelerator("<Primary>q", "app.quit", None)
        quit.connect("activate", self.on_quit)

        # Avahi services
        self.avahi_browser = None
        self.avahi_service_type = '_geysign._tcp'
        self.discovered_services = []
        GLib.idle_add(self.setup_avahi_browser)

        ## App menus
        appmenu = Gio.Menu.new()
        section = Gio.Menu.new()
        appmenu.append_section(None, section)

        some_action = Gio.SimpleAction.new("scan-image", None)
        some_action.connect('activate', self.on_scan_image)
        self.add_action(some_action)
        some_item = Gio.MenuItem.new("Scan Image", "app.scan-image")
        section.append_item(some_item)

        quit_item = Gio.MenuItem.new("Quit", "app.quit")
        section.append_item(quit_item)

        self.set_app_menu(appmenu)


    def on_scan_image(self, *args, **kwargs):
        print("scanimage")


    def on_activate(self, app):
        self.log.info("Activate!")
        #self.window = Gtk.ApplicationWindow(application=app)
        self.window.show_all()
        # In case the user runs the application a second time,
        # we raise the existing window.
        # self.window.present()


    def setup_avahi_browser(self):
        # FIXME: place a proper service type
        self.avahi_browser = AvahiBrowser(service=self.avahi_service_type)
        self.avahi_browser.connect('new_service', self.on_new_service)
        self.avahi_browser.connect('remove_service', self.on_remove_service)
        return False


    def on_new_service(self, browser, name, address, port, txt_dict):
        published_fpr = txt_dict.get('fingerprint', None)
        self.log.info("Probably discovered something, let's check; %s %s:%i:%s",             name, address, port, published_fpr)

        if self.verify_service(name, address, port):
            GLib.idle_add(self.add_discovered_service, name, address, port, published_fpr)
        else:
            self.log.warn("Client was rejected: %s %s %i",
                        name, address, port)


    def on_remove_service(self, browser, service_type, name):
        '''Receives on_remove signal from avahibrowser.py to remove service from list and
        transfers data to remove_discovered_service'''
        self.log.info("Received a remove signal, let's check; %s:%s", service_type, name)
        GLib.idle_add(self.remove_discovered_service, name)


    def verify_service(self, name, address, port):
        '''A tiny function to return whether the service
        is indeed something we are interested in'''
        return True


    def add_discovered_service(self, name, address, port, published_fpr):
        self.discovered_services += ((name, address, port, published_fpr), )
        #List needs to be modified when server services are removed.
        self.log.info("Clients currently in list '%s'", self.discovered_services)
        return False


    def remove_discovered_service(self, name):
        '''Removes server-side clients from discovered_services list
        when the server name with fpr is a match.'''
        for client in self.discovered_services:
            if client[0] == name:
                self.discovered_services.remove(client)
        self.log.info("Clients currently in list '%s'", self.discovered_services)


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
        format='%(name)s (%(levelname)s): %(message)s')

    app = GnomeKeysignClient()
    app.run(None)