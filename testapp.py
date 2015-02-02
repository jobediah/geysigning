from gi.repository import Gtk, Gio
import sys

#Can we separate the window from both applications?

class TertiaryApp(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, application_id="apps.test.helloworld",
                                 flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self.on_activate)
        Wid =0L
        #if len(sys.argv) == 2:
        #    Wid = long(sys.argv[1])
        self. plug = Gtk.Plug(Wid)
        self.plug = self.plug.get_id()
        print "Plug ID=", self.plug


    def on_activate(self, data=None):
        notebook = Gtk.Notebook()
        self.widget = notebook.append_page(Gtk.Label('Get Key'))
        #self.plug.connet("embedded", self.embed_event)
        self.plug.add(self.widget)
        self.plug.show_all()


class MainApp(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, application_id="apps.test.helloworld",
                                 flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self.on_activate)
        #Want this in main, need to pass data between two classes
        app2 = TertiaryApp()
        app2.run(None)


    def on_activate(self, data=None):

        window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        window.set_title("Gtk3 Python Example")
        window.set_border_width(24)

        vbox = Gtk.VBox()

        notebook = Gtk.Notebook()
        notebook.append_page(Gtk.Label('Keys'))
        window.add(vbox)
        vbox.pack_start(notebook, expand=True, fill=True, padding=0)

        #old code
        #notebook.append_page(Gtk.Label('Get Key'))
        #window.add(notebook)


        socket = Gtk.Socket()
        print socket

        #Following code gets socket ID number
        #socket.show()
        #vbox.pack_start(socket, expand=True, fill=True, padding=0)
        #vbox must be added before to get socket id
        #socket_id = socket.get_id()
        #print "Socket ID=", socket_id

        print app2.plug

        widget = Gtk.Socket.add_id(socket, app2.plug)  #This line is failing
        print widget

        if widget == None:
            label = Gtk.Label()
            label.set_label("Hello World")
            widget = label

        vbox.pack_start(widget, expand=True, fill=True, padding=0)

        #Will want this later?
        #socket.connect("plug-added", self.plugged_event)

        window.show_all()
        self.add_window(window)

if __name__ == "__main__":
    #app2 = TertiaryApp()
    #app2.run(None)

    app = MainApp()
    app.run(None)

