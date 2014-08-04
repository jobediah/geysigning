#!/usr/bin/env python

import logging
from urlparse import ParseResult

import requests
from requests.exceptions import ConnectionError

import sys
from StringIO import StringIO

try:
    from monkeysign.gpg import TempKeyring, GpgProtocolError
except ImportError, e:
    print "A required python module is missing!\n%s" % (e,)
    sys.exit()

from gi.repository import GLib
from gi.repository import Gtk

from SignPages import KeysPage, KeyPresentPage, KeyDetailsPage

progress_bar_text = ["Step 1: Choose a key and click on 'Next' button",
                     "Step 2: Compare the recieved fingerprint with the owner's key fpr",
                     "Step 3: Check if the identification papers match",
                     "Step 4: Key was succesfully signed"
                    ]

class KeySignSection(Gtk.VBox):

    def __init__(self, app):
        '''Initialises the section which lets the user
        choose a key to be signed by other person.

        ``app'' should be the "app" itself. The place
        which holds global app data, especially the discovered
        clients on the network.
        '''
        super(KeySignSection, self).__init__()

        self.app = app
        self.log = logging.getLogger()

        # these are needed later when we need to get details about
        # a selected key
        self.keysPage = KeysPage()
        self.keyDetailsPage = KeyDetailsPage()
        self.keyPresentPage = KeyPresentPage()
        
        # We hold a reference to a keyserver and
        # we try to start it once we show the key details
        # and to stop it once we left the key details page
        # This should probably go into the main app, not
        # here in the UI part of the application.
        # But we make it work first, and then try to make it
        # nice.
        self.keyserver = None

        # set up notebook container
        self.notebook = Gtk.Notebook()
        self.notebook.append_page(self.keysPage, None)
        self.notebook.append_page(self.keyDetailsPage, None)
        self.notebook.append_page(self.keyPresentPage, None)
        self.notebook.set_show_tabs(False)

        # create back button
        self.backButton = Gtk.Button('Back')
        self.backButton.set_image(Gtk.Image.new_from_icon_name("go-previous", Gtk.IconSize.BUTTON))
        self.backButton.set_always_show_image(True)
        self.backButton.connect('clicked', self.on_button_clicked)
        # create next button
        self.nextButton = Gtk.Button('Next')
        self.nextButton.set_image(Gtk.Image.new_from_icon_name("go-next", Gtk.IconSize.BUTTON))
        self.nextButton.set_always_show_image(True)
        self.nextButton.connect('clicked', self.on_button_clicked)

        buttonBox = Gtk.HBox()
        buttonBox.pack_start(self.backButton, False, False, 0)
        buttonBox.pack_start(self.nextButton, False, False, 0)
        # pack up
        self.pack_start(self.notebook, True, True, 0)
        self.pack_start(buttonBox, False, False, 0)

    def on_button_clicked(self, button):
        # get index of current page
        page_index = self.notebook.get_current_page()

        # FIXME: starting/stopping the avahi publish service
        # should be done in a more robust way.
        if page_index+1 == 2 and button.get_label() == 'Next':
            GLib.idle_add(self.app.setup_avahi_publisher)
        else:
            if self.app.avahi_publisher is not None:
                self.app.avahi_publisher.unpublish()

        if button == self.nextButton:
            # switch to the next page in the notebook
            self.notebook.next_page()
            page_index = self.notebook.get_current_page()
            # get a Gtk.TreeSelection object to process the selected rows
            selection = self.keysPage.treeView.get_selection()
            model, paths = selection.get_selected_rows()
            if page_index == 1:
                for path in paths:
                    iterator = model.get_iter(path)
                    (name, email, keyid) = model.get(iterator, 0, 1, 2)
                    try:
                        openPgpKey = self.keysPage.keysDict[keyid]
                        self.keyPresentPage.display_key_details(openPgpKey)
                    except KeyError:
                        m = "No key details can be shown for this id:%s"
                        print m % (keyid, )
                        self.log.exception(m, keyid)

                    else:
                        keydata = self.keysPage.keyring.export_data(openPgpKey.fpr)
                        self.log.info('About to serve %s', openPgpKey)
                        self.log.debug('The actual data is %s', keydata)
                        self.start_serving_key(keydata)

        elif button == self.backButton:
            self.notebook.prev_page()
            # Yeah, we might also want to check for the correct page
            # and not unconditionally stop serving. But it seems to
            # work well enough
            if self.is_keyserver_running():
                self.stop_serving_key()



    def is_keyserver_running(self):
        "Determines whether we have a keyserver running"
        return self.keyserver


    def start_serving_key(self, key):
        "Starts a keyserver with the key"
        self.log.info("Starting to serve key %r", key)
        self.keyserver = 1


    def stop_serving_key(self):
        "Stops the keyserver started with start_serving_key"
        self.log.info("Stopping keyserver %r", self.keyserver)
        self.keyserver = None

FILENAME = 'testkey.gpg'

class GetKeySection(Gtk.Box):

    def __init__(self, app):
        '''Initialises the section which lets the user
        start signing a key.

        ``app'' should be the "app" itself. The place
        which holds global app data, especially the discovered
        clients on the network.
        '''
        super(GetKeySection, self).__init__()

        self.app = app
        self.log = logging.getLogger()

        # the temporary keyring we operate in
        self.tempkeyring = None

        # set up main container
        mainBox = Gtk.VBox(spacing=10)
        # set up labels
        self.topLabel = Gtk.Label()
        self.topLabel.set_markup('Type fingerprint')
        midLabel = Gtk.Label()
        midLabel.set_markup('... or scan QR code')
        # set up text editor
        self.textview = Gtk.TextView()
        self.textbuffer = self.textview.get_buffer()
        # set up scrolled window
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.add(self.textview)

        # set up webcam frame
        # FIXME  create the actual webcam widgets
        self.scanFrame = Gtk.Frame(label='QR Scanner')

        # set up download button
        # Scenario: When 'Download' button is clicked it will request data
        # from network using self.app.discovered_services to get address
        self.downloadButton = Gtk.Button('Download Key')
        self.downloadButton.connect('clicked', self.on_button_clicked)
        self.downloadButton.set_image(Gtk.Image.new_from_icon_name("document-save", Gtk.IconSize.BUTTON))
        self.downloadButton.set_always_show_image(True)
        # pack up
        mainBox.pack_start(self.topLabel, False, False, 0)
        mainBox.pack_start(scrolledwindow, False, False, 0)
        mainBox.pack_start(midLabel, False, False, 0)
        mainBox.pack_start(self.scanFrame, True, True, 0)
        mainBox.pack_start(self.downloadButton, False, False, 0)
        self.pack_start(mainBox, True, False, 0)


    def download_key_http(self, address, port):
        url = ParseResult(
            scheme='http',
            # This seems to work well enough with both IPv6 and IPv4
            netloc="[[%s]]:%d" % (address, port),
            path='/',
            params='',
            query='',
            fragment='')
        # return requests.get(url.geturl()).text

        # FIXME: hardcoded. Make it pass the data received from network.
        fd = open(FILENAME, "r")
        text = fd.read()
        fd.close()

        return text

    def try_download_keys(self, clients):
        for client in clients:
            self.log.debug("Getting key from client %s", client)
            name, address, port = client
            try:
                keydata = self.download_key_http(address, port)
                yield keydata
            except ConnectionError, e:
                # FIXME : We probably have other errors to catch
                self.log.exception("While downloading key from %s %i",
                                    address, port)

    def verify_downloaded_key(self, downloaded_data, fingerprint):
        # FIXME: implement a better and more secure way to verify the key
        if self.tmpkeyring.import_data(downloaded_data):
            imported_key_fpr = self.tmpkeyring.get_keys().keys()[0]
            if imported_key_fpr == fingerprint:
                return True

        return False

    def obtain_key_async(self, fingerprint, callback=None, data=None, error_cb=None):
        other_clients = self.app.discovered_services
        self.log.debug("The clients found on the network: %s", other_clients)

        # create a temporary keyring to not mess up with the user's own keyring
        self.tmpkeyring = TempKeyring()

        for keydata in self.try_download_keys(other_clients):
            if self.verify_downloaded_key(keydata, fingerprint):
                # FIXME: temporary solution to pass the fingerprint
                # to the callback function.
                if data is None:
                    data = self.tmpkeyring.get_keys().keys()[0]

                is_valid = True
            else:
                is_valid = False

            if is_valid:
                break
        else:
            self.log.error("Could not find fingerprint %s " +\
                           "with the available clients (%s)",
                           fingerprint, other_clients)
            self.log.debug("Calling error callback, if available: %s",
                            error_cb)

            if error_cb:
                GLib.idle_add(error_cb, data)
            # FIXME : don't return here
            return

        GLib.idle_add(callback, keydata, data)
        # If this function is added itself via idle_add, then idle_add will
        # keep adding this function to the loop until this func ret False
        return False

    def on_button_clicked(self, button):

        start_iter = self.textbuffer.get_start_iter()
        end_iter = self.textbuffer.get_end_iter()

        # FIXME: hardcoded
        fingerprint = '140162A978431A0258B3EC24E69EEE14181523F4'
        # fingerprint = self.textbuffer.get_text(start_iter, end_iter, False)
        self.textbuffer.delete(start_iter, end_iter)

        self.topLabel.set_text("downloading key with fingerprint:\n%s"
                                % fingerprint)

        err = lambda x: self.textbuffer.set_text("Error downloading")
        GLib.idle_add(self.obtain_key_async, fingerprint,
            self.recieved_key, fingerprint,
            err
            )

    def recieved_key(self, keydata, *data):
        self.textbuffer.insert_at_cursor("Key succesfully imported with"
                                " fingerprint:\n{}".format(data[0]))
