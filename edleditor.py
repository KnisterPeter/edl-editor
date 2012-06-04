#!/usr/bin/python

"""
class PlaybackInterface:

    def __init__(self):
        self.main_window = gtk.Window()
        self.play_button = gtk.Button()
        self.slider = gtk.HScale()

        self.hbox = gtk.HBox()  
        self.hbox.pack_start(self.play_button, False)
        self.hbox.pack_start(self.slider, True, True)

        self.main_window.add(self.hbox)
        self.main_window.connect('destroy', self.on_destroy)

        self.play_button.set_image(self.PLAY_IMAGE)
        self.play_button.connect('clicked', self.on_play)

        self.slider.set_range(0, 100)
        self.slider.set_increments(1, 10)
        self.slider.connect('value-changed', self.on_slider_change)

        self.main_window.set_border_width(6)
        self.main_window.set_size_request(600, 50)

        self.playbin = gst.element_factory_make('playbin2')
        self.playbin.set_property('uri', 'file:///var/movies/deutsch/Star+Trek+V+-+Am+Rande+des+Universums.mkv')

        self.bus = self.playbin.get_bus()
        self.bus.add_signal_watch()

        self.bus.connect("message::eos", self.on_finish)

        self.is_playing = False

        self.main_window.show_all()

    def on_finish(self, bus, message):
        self.playbin.set_state(gst.STATE_PAUSED)
        self.play_button.set_image(self.PLAY_IMAGE)
        self.is_playing = False
        self.playbin.seek_simple(gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH, 0)
        self.slider.set_value(0)

    def on_destroy(self, window):
        # NULL state allows the pipeline to release resources
        self.playbin.set_state(gst.STATE_NULL)
        self.is_playing = False
        gtk.main_quit()

    def on_play(self, button):
        if not self.is_playing:
            self.play_button.set_image(self.PAUSE_IMAGE)
            self.is_playing = True

            self.playbin.set_state(gst.STATE_PLAYING)
            gobject.timeout_add(100, self.update_slider)

        else:
            self.play_button.set_image(self.PLAY_IMAGE)
            self.is_playing = False

            self.playbin.set_state(gst.STATE_PAUSED)

    def on_slider_change(self, slider):
        seek_time_secs = slider.get_value()
        self.playbin.seek_simple(gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_KEY_UNIT, seek_time_secs * gst.SECOND)

    def update_slider(self):
        if not self.is_playing:
            return False # cancel timeout

        try:
            nanosecs, format = self.playbin.query_position(gst.FORMAT_TIME)
            duration_nanosecs, format = self.playbin.query_duration(gst.FORMAT_TIME)

            # block seek handler so we don't seek when we set_value()
            self.slider.handler_block_by_func(self.on_slider_change)

            self.slider.set_range(0, float(duration_nanosecs) / gst.SECOND)
            self.slider.set_value(float(nanosecs) / gst.SECOND)

            self.slider.handler_unblock_by_func(self.on_slider_change)

        except gst.QueryError:
            # pipeline must not be ready and does not know position
         pass

        return True # continue calling every 30 milliseconds


if __name__ == "__main__":
    PlaybackInterface()
    gtk.main()
"""

import sys, os
import pygtk, gtk, gobject
import pygst
pygst.require("0.10")
import gst
import urllib2

class EDL_Editor:
  
  PLAY_IMAGE = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)
  PAUSE_IMAGE = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_BUTTON)
  STOP_IMAGE = gtk.image_new_from_stock(gtk.STOCK_MEDIA_STOP, gtk.ICON_SIZE_BUTTON)
  REWIND_IMAGE = gtk.image_new_from_stock(gtk.STOCK_MEDIA_REWIND, gtk.ICON_SIZE_BUTTON)
  FORWARD_IMAGE = gtk.image_new_from_stock(gtk.STOCK_MEDIA_FORWARD, gtk.ICON_SIZE_BUTTON)

  def __init__(self):
    self.rewind_button = gtk.Button()
    self.rewind_button.set_image(self.REWIND_IMAGE)

    self.forward_button = gtk.Button()
    self.forward_button.set_image(self.FORWARD_IMAGE)

    self.stop_button = gtk.Button()
    self.stop_button.set_image(self.STOP_IMAGE)

    self.play_button = gtk.Button()
    self.play_button.set_image(self.PLAY_IMAGE)
    self.play_button.connect("clicked", self.start_stop)

    hbox = gtk.HBox()
    hbox.pack_start(self.rewind_button, False)
    hbox.pack_start(self.play_button, False)
    hbox.pack_start(self.stop_button, False)
    hbox.pack_start(self.forward_button, False)

    self.movie_window = gtk.DrawingArea()

    vbox = gtk.VBox()
    vbox.add(self.movie_window)
    vbox.pack_start(hbox, False)

    self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.window.set_title("EDL Editor")
    self.window.set_default_size(640, 480)
    self.window.connect('destroy', self.on_destroy)
    self.window.add(vbox)
    self.window.show_all()
    
    self.player = gst.element_factory_make("playbin2", "player")
    bus = self.player.get_bus()
    bus.add_signal_watch()
    bus.enable_sync_message_emission()
    bus.connect("message", self.on_message)
    bus.connect("sync-message::element", self.on_sync_message)
    self.is_playing = False

  def on_destroy(self, window):
      # NULL state allows the pipeline to release resources
      self.player.set_state(gst.STATE_NULL)
      self.is_playing = False
      gtk.main_quit()
    
  def start_stop(self, w):
    if not self.is_playing:
      self.is_playing = True
      filepath = sys.argv[1]
      if os.path.isfile(filepath):
        self.play_button.set_image(self.PAUSE_IMAGE)
        self.player.set_property("uri", "file://" + urllib2.quote(filepath.encode("utf8")))
        self.player.set_state(gst.STATE_PLAYING)
    else:
      self.is_playing = False
      self.player.set_state(gst.STATE_NULL)
      self.play_button.set_image(self.PLAY_IMAGE)
            
  def on_message(self, bus, message):
    t = message.type
    if t == gst.MESSAGE_EOS:
      self.is_playing = False
      self.player.set_state(gst.STATE_NULL)
      self.play_button.set_image(self.PLAY_IMAGE)
    elif t == gst.MESSAGE_ERROR:
      self.is_playing = False
      self.player.set_state(gst.STATE_NULL)
      err, debug = message.parse_error()
      print "Error: %s" % err, debug
      self.play_button.set_image(self.PLAY_IMAGE)
  
  def on_sync_message(self, bus, message):
    if message.structure is None:
      return
    message_name = message.structure.get_name()
    if message_name == "prepare-xwindow-id":
      imagesink = message.src
      imagesink.set_property("force-aspect-ratio", True)
      gtk.gdk.threads_enter()
      imagesink.set_xwindow_id(self.movie_window.window.xid)
      gtk.gdk.threads_leave()


if __name__ == "__main__":
  EDL_Editor()
  gtk.gdk.threads_init()
  gtk.main()

