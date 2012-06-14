#!/usr/bin/python

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
    self.speed = 1.0
    self.progress = "0:00 / 0:00"
    
    self.movie_window = gtk.DrawingArea()
    self.movie_window.modify_bg(gtk.STATE_NORMAL, self.movie_window.style.black)

    self.slider = gtk.HScale()
    self.slider.set_range(0, 100)
    self.slider.set_increments(1, 60)
    self.slider.set_draw_value(False)
    self.slider.connect('value-changed', self.on_slider_change)

    self.rewind_button = gtk.Button()
    self.rewind_button.set_image(self.REWIND_IMAGE)
    self.rewind_button.connect("clicked", self.on_rewind)

    self.play_button = gtk.Button()
    self.play_button.set_image(self.PLAY_IMAGE)
    self.play_button.connect("clicked", self.on_play_pause)

    self.forward_button = gtk.Button()
    self.forward_button.set_image(self.FORWARD_IMAGE)
    self.forward_button.connect("clicked", self.on_forward)

    hbox = gtk.HBox()
    hbox.pack_start(self.rewind_button, False)
    hbox.pack_start(self.play_button, False)
    hbox.pack_start(self.forward_button, False)

    self.label_time = gtk.Label(self.progress)
    self.label_speed = gtk.Label("%f x" % self.speed)
    sbox = gtk.HBox()
    sbox.pack_start(self.label_time, False, True, 5)
    sbox.pack_start(gtk.VSeparator(), False, True, 5)
    sbox.pack_start(self.label_speed, False, True, 5)

    vbox = gtk.VBox()
    vbox.add(self.movie_window)
    vbox.pack_start(self.slider, False, True, 5)
    vbox.pack_start(hbox, False, True, 5)
    vbox.pack_start(sbox, False, True, 5)
    
    self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.window.set_title("EDL Editor")
    self.window.set_default_size(640, 480)
    #self.window.set_border_width(6)
    self.window.set_size_request(600, 50)
    self.window.connect('destroy', self.on_destroy)
    self.window.add(vbox)
    self.window.show_all()
    
    self.player = gst.element_factory_make("playbin2", "player")
    self.player.set_state(gst.STATE_READY)
    filepath = sys.argv[1]
    if os.path.isfile(filepath):
      self.player.set_property("uri", "file://" + urllib2.quote(filepath.encode("utf8")))
    bus = self.player.get_bus()
    bus.add_signal_watch()
    bus.enable_sync_message_emission()
    bus.connect("message", self.on_message)
    bus.connect("sync-message::element", self.on_sync_message)

    self.set_state_and_play_image(gst.STATE_PLAYING, self.PAUSE_IMAGE)
    gobject.timeout_add(100, self.update_slider)

  def on_message(self, bus, message):
    t = message.type
    if t == gst.MESSAGE_ERROR:
      self.set_state_and_play_image(gst.STATE_NULL, self.PLAY_IMAGE)
      err, debug = message.parse_error()
      print "Error: %s" % err, debug
  
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

  def on_destroy(self, window):
    self.is_playing = False
    self.player.set_state(gst.STATE_NULL)
    gtk.main_quit()
    
  def on_play_pause(self, w):
    if not self.is_playing:
      self.set_state_and_play_image(gst.STATE_PLAYING, self.PAUSE_IMAGE)
      gobject.timeout_add(100, self.update_slider)
    else:
      self.set_speed(1.0)
      self.set_state_and_play_image(gst.STATE_PAUSED, self.PLAY_IMAGE)

  def on_rewind(self, w):
    pass

  def on_forward(self, w):
    self.set_speed(self.inc_speed())

  def on_slider_change(self, slider):
    pos = slider.get_value() * gst.SECOND
    self.player.seek_simple(gst.FORMAT_TIME, 
      gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_KEY_UNIT, 
      pos)

  def update_slider(self):
    if not self.is_playing:
      return False
    try:
      ns, format = self.player.query_position(gst.FORMAT_TIME)
      dns, format = self.player.query_duration(gst.FORMAT_TIME)

      self.slider.handler_block_by_func(self.on_slider_change)
      self.slider.set_range(0, float(dns) / gst.SECOND)
      self.slider.set_value(float(ns) / gst.SECOND)
      self.slider.handler_unblock_by_func(self.on_slider_change)

      cur = self.format_nanos(ns)
      end = self.format_nanos(dns)
      self.progress = '%s / %s' % (cur, end)
      self.update_status()
    except gst.QueryError:
      pass
    return True

  def set_speed(self, speed=1.0):
    self.speed = speed
    ns, format = self.player.query_position(gst.FORMAT_TIME)
    self.player.seek(speed, 
      gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_ACCURATE,
      gst.SEEK_TYPE_SET, ns,
      gst.SEEK_TYPE_NONE, 0)
    self.update_status()

  def set_state_and_play_image(self, state, image):
    self.is_playing = state == gst.STATE_PLAYING
    self.player.set_state(state)
    self.play_button.set_image(image)

  def format_nanos(self, ns):
    s,ns = divmod(ns, 1000000000)
    m,s = divmod(s, 60)
    if m < 60:
      return "%02i:%02i" %(m,s)
    h,m = divmod(m, 60)
    return "%i:%02i:%02i" %(h,m,s)
    
  def inc_speed(self):
    speed = self.speed
    if speed < 32:
      speed *= 2
    else:
      speed = 1.0
    return speed
    
  def update_status(self):
    self.label_time.set_text(self.progress)
    self.label_speed.set_text("%.2f x" % self.speed)

if __name__ == "__main__":
  EDL_Editor()
  gtk.gdk.threads_init()
  gtk.main()

