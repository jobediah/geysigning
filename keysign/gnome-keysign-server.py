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

import logging
import sys

from gi.repository import Gtk, Gio

from KeySignSection import KeySignSection

class GnomeKeysignServer(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, application_id="org.gnome.keysign.server",
                                 flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self.on_activate)
        
        self.log = logging.getLogger()

    def on_activate(self, data=None):
        window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        window.set_title("Gtk3 Python Example")
        key_sign_section = KeySignSection()
        window.add(key_sign_section)

        window.show_all()
        self.add_window(window)


    def setup_server(self, *args):
        self.log.error("Calling setup_server")


    def stop_server(self, *args):
        self.log.error("Calling stop_server")


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
            format='%(name)s (%(levelname)s): %(message)s')
    app = GnomeKeysignServer()
    app.run(None)
