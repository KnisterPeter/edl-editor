#!/usr/bin/python

import sys, os
import pygtk, gtk, gobject
import pygst
pygst.require("0.10")
import gst
import urllib2
from datetime import timedelta
import pyedl

class EDL_Editor:
  
  TIMEOUT = 100
  
  REWIND_IMAGE = gtk.image_new_from_stock(gtk.STOCK_MEDIA_REWIND, gtk.ICON_SIZE_BUTTON)
  PREVIOUS_FRAME = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PREVIOUS, gtk.ICON_SIZE_BUTTON)
  PLAY_IMAGE = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)
  PAUSE_IMAGE = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_BUTTON)
  STOP_IMAGE = gtk.image_new_from_stock(gtk.STOCK_MEDIA_STOP, gtk.ICON_SIZE_BUTTON)
  NEXT_FRAME = gtk.image_new_from_stock(gtk.STOCK_MEDIA_NEXT, gtk.ICON_SIZE_BUTTON)
  FORWARD_IMAGE = gtk.image_new_from_stock(gtk.STOCK_MEDIA_FORWARD, gtk.ICON_SIZE_BUTTON)
  
  PREVIOUS_MARKER = gtk.image_new_from_stock(gtk.STOCK_GOTO_FIRST, gtk.ICON_SIZE_BUTTON)
  MARK_START = gtk.image_new_from_stock(gtk.STOCK_GO_BACK, gtk.ICON_SIZE_BUTTON)
  MARK_END = gtk.image_new_from_stock(gtk.STOCK_GO_FORWARD, gtk.ICON_SIZE_BUTTON)
  NEXT_MARKER = gtk.image_new_from_stock(gtk.STOCK_GOTO_LAST, gtk.ICON_SIZE_BUTTON)
  
  SAVE = gtk.image_new_from_stock(gtk.STOCK_FLOPPY, gtk.ICON_SIZE_BUTTON)
  
  MODE_STOP = 0
  MODE_PAUSE = 1
  MODE_SEEK_PAUSE = 2
  MODE_PLAY = 100

  def __init__(self):
    self.speed = 1.0
    self.progress = "0:00 / 0:00"
    self.mode = self.MODE_STOP
    self.position = 0
    self.duration = 0
    self.start = None
    self.end = None
    
    self.movie_window = gtk.DrawingArea()
    self.movie_window.modify_bg(gtk.STATE_NORMAL, self.movie_window.style.black)

    self.slider = gtk.HScale()
    self.slider.set_range(0, 100)
    self.slider.set_increments(1, 60)
    self.slider.set_draw_value(False)
    self.slider.connect('value-changed', self.on_slider_change)

    self.rewind_60s = gtk.Button('< 60')
    self.rewind_60s.connect("clicked", self.on_rewind_60s)
    self.rewind_10s = gtk.Button('< 10')
    self.rewind_10s.connect("clicked", self.on_rewind_10s)
    self.rewind_1s = gtk.Button('< 1')
    self.rewind_1s.connect("clicked", self.on_rewind_1s)
    self.rewind_button = gtk.Button()
    self.rewind_button.set_image(self.REWIND_IMAGE)
    self.rewind_button.connect("clicked", self.on_rewind)
    self.play_button = gtk.Button()
    self.play_button.set_image(self.PLAY_IMAGE)
    self.play_button.connect("clicked", self.on_play_pause)
    self.forward_button = gtk.Button()
    self.forward_button.set_image(self.FORWARD_IMAGE)
    self.forward_button.connect("clicked", self.on_forward)
    self.forward_1s = gtk.Button('1 >')
    self.forward_1s.connect("clicked", self.on_forward_1s)
    self.forward_10s = gtk.Button('10 >')
    self.forward_10s.connect("clicked", self.on_forward_10s)
    self.forward_60s = gtk.Button('60 >')
    self.forward_60s.connect("clicked", self.on_forward_60s)

    self.previous_marker_button = gtk.Button()
    self.previous_marker_button.set_image(self.PREVIOUS_MARKER)
    self.previous_marker_button.connect("clicked", self.on_previous_marker)
    self.start_marker_button = gtk.Button()
    self.start_marker_button.set_image(self.MARK_START)
    self.start_marker_button.connect("clicked", self.on_mark_start)
    self.end_marker_button = gtk.Button()
    self.end_marker_button.set_image(self.MARK_END)
    self.end_marker_button.connect("clicked", self.on_mark_end)
    self.next_marker_button = gtk.Button()
    self.next_marker_button.set_image(self.NEXT_MARKER)
    self.next_marker_button.connect("clicked", self.on_next_marker)

    self.save_button = gtk.Button()
    self.save_button.set_image(self.SAVE)
    self.save_button.connect("clicked", self.on_save)

    hbox = gtk.HBox()
    hbox.pack_start(self.rewind_60s, False)
    hbox.pack_start(self.rewind_10s, False)
    hbox.pack_start(self.rewind_1s, False)
    hbox.pack_start(self.rewind_button, False)
    hbox.pack_start(self.play_button, False)
    hbox.pack_start(self.forward_button, False)
    hbox.pack_start(self.forward_1s, False)
    hbox.pack_start(self.forward_10s, False)
    hbox.pack_start(self.forward_60s, False)
    hbox.pack_start(gtk.VSeparator(), False, True, 5)
    hbox.pack_start(self.previous_marker_button, False)
    hbox.pack_start(self.start_marker_button, False)
    hbox.pack_start(self.end_marker_button, False)
    hbox.pack_start(self.next_marker_button, False)
    hbox.pack_start(gtk.VSeparator(), False, True, 5)
    hbox.pack_start(self.save_button, False)

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
    self.window.set_size_request(600, 50)
    self.window.connect('destroy', self.on_destroy)
    self.window.add(vbox)
    self.window.show_all()
    
    self.player = gst.element_factory_make("playbin2", "player")
    self.player.set_state(gst.STATE_READY)
    filepath = sys.argv[1]
    if not os.path.isfile(filepath):
      print "File", filepath, "not found"
      sys.exit(1)
    self.player.set_property("uri", "file://" + urllib2.quote(filepath.encode("utf8")))
    self.edlfile = os.path.splitext(filepath)[0] + ".edl"
    if os.path.isfile(self.edlfile):
      self.edl = pyedl.load(open(self.edlfile))
    else:
      self.edl = pyedl.EDL()

    bus = self.player.get_bus()
    bus.add_signal_watch()
    bus.enable_sync_message_emission()
    bus.connect("message", self.on_message)
    bus.connect("sync-message::element", self.on_sync_message)

    self.set_state_and_play_image(gst.STATE_PAUSED, self.PLAY_IMAGE)

    for block in self.edl:
      start = float(block.startTime.days * 86400 + block.startTime.seconds * gst.SECOND) / gst.SECOND
      end = float(block.stopTime.days * 86400 + block.stopTime.seconds * gst.SECOND) / gst.SECOND
      self.add_marker(start, end)

  def add_marker(self, start, end):
    while start < end:
      self.slider.add_mark(start, 0, None)
      start = start + 1

  def on_message(self, bus, message):
    t = message.type
    if t == gst.MESSAGE_ERROR:
      self.set_state_and_play_image(gst.STATE_NULL, self.PLAY_IMAGE)
      err, debug = message.parse_error()
      print "Error: %s" % err, debug
    elif t == gst.MESSAGE_DURATION:
      format, duration = message.parse_duration()
      self.setup_duration(duration)
  
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
    self.mode = self.MODE_STOP
    self.player.set_state(gst.STATE_NULL)
    gtk.main_quit()

  def setup_duration(self, duration):
    self.duration = duration
    self.slider.handler_block_by_func(self.on_slider_change)
    self.slider.set_range(0, float(self.duration) / gst.SECOND)
    self.slider.handler_unblock_by_func(self.on_slider_change)
    
  def on_rewind_60s(self, w):
    if self.mode == self.MODE_PAUSE:
      self.seek_paused(-60)

  def on_rewind_10s(self, w):
    if self.mode == self.MODE_PAUSE:
      self.seek_paused(-10)

  def on_rewind_1s(self, w):
    if self.mode == self.MODE_PAUSE:
      self.seek_paused(-1)

  def on_rewind(self, w):
    if self.mode >= self.MODE_PLAY:
      self.set_speed(self.dec_speed())

  def on_play_pause(self, w):
    if self.mode < self.MODE_PLAY:
      self.set_state_and_play_image(gst.STATE_PLAYING, self.PAUSE_IMAGE)
      gobject.timeout_add(self.TIMEOUT, self.update_slider)
    else:
      self.set_speed(1.0)
      self.set_state_and_play_image(gst.STATE_PAUSED, self.PLAY_IMAGE)

  def on_forward(self, w):
    if self.mode >= self.MODE_PLAY:
      self.set_speed(self.inc_speed())

  def on_forward_1s(self, w):
    if self.mode == self.MODE_PAUSE:
      self.seek_paused(1)

  def on_forward_10s(self, w):
    if self.mode == self.MODE_PAUSE:
      self.seek_paused(10)

  def on_forward_60s(self, w):
    if self.mode == self.MODE_PAUSE:
      self.seek_paused(60)

  def on_slider_change(self, slider):
    pos = self.slider.get_value()
    self.player.seek_simple(gst.FORMAT_TIME, 
      gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_KEY_UNIT, 
      pos * gst.SECOND)
    if self.mode == self.MODE_PAUSE:
      self.set_state_and_play_image(gst.STATE_PLAYING, self.PLAY_IMAGE)
      self.mode = self.MODE_SEEK_PAUSE
      gobject.timeout_add(self.TIMEOUT, self.update_slider)

  def on_previous_marker(self, button):
    t = self.edl.getPrevBoundary(timedelta(seconds=self.position / gst.SECOND))
    self.seek_to(t.days*86400+t.seconds * gst.SECOND)

  def on_mark_start(self, button):
    self.start = self.position
    self.new_marker()

  def on_mark_end(self, button):
    self.end = self.position
    self.new_marker()

  def on_next_marker(self, button):
    t = self.edl.getNextBoundary(timedelta(seconds=self.position / gst.SECOND))
    if t != None:
      self.seek_to(t.days*86400+t.seconds * gst.SECOND)
    else:
      self.seek_to(self.duration)

  def on_save(self, button):
    self.edl.normalize(timedelta(seconds=self.duration / gst.SECOND))
    pyedl.dump(self.edl, open(self.edlfile, "w"))

  def new_marker(self):
    if self.start != None and self.end != None:
      self.edl.newBlock(
        timedelta(seconds=self.start / gst.SECOND), 
        timedelta(seconds=self.end / gst.SECOND))
      #self.slider.add_mark(float(self.start) / gst.SECOND, 0, None)
      #self.slider.add_mark(float(self.end) / gst.SECOND, 0, None)
      self.add_marker(float(self.start) / gst.SECOND, float(self.end) / gst.SECOND)
      self.start = None
      self.end = None

  def seek_to(self, pos):
    self.set_state_and_play_image(gst.STATE_PLAYING, self.PLAY_IMAGE)
    self.mode = self.MODE_SEEK_PAUSE
    self.player.seek_simple(gst.FORMAT_TIME, 
      gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_ACCURATE,
      pos)
    gobject.timeout_add(self.TIMEOUT, self.update_slider)

  def seek_paused(self, offset):
    self.set_state_and_play_image(gst.STATE_PLAYING, self.PLAY_IMAGE)
    self.mode = self.MODE_SEEK_PAUSE
    ns, format = self.player.query_position(gst.FORMAT_TIME)
    pos = ns  + offset * gst.SECOND
    if pos < 0:
      pos = 0
    self.player.seek_simple(gst.FORMAT_TIME, 
      gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_ACCURATE,
      pos)
    gobject.timeout_add(self.TIMEOUT, self.update_slider)

  def update_slider(self):
    if self.mode < self.MODE_SEEK_PAUSE:
      return False
    try:
      self.position, format = self.player.query_position(gst.FORMAT_TIME)
      self.duration, format = self.player.query_duration(gst.FORMAT_TIME)

      self.slider.handler_block_by_func(self.on_slider_change)
      self.slider.set_range(0, float(self.duration) / gst.SECOND)
      self.slider.set_value(float(self.position) / gst.SECOND)
      self.slider.handler_unblock_by_func(self.on_slider_change)

      cur = self.format_nanos(self.position)
      end = self.format_nanos(self.duration)
      self.progress = '%s / %s' % (cur, end)
      self.update_status()
    except gst.QueryError:
      pass
    if self.mode == self.MODE_SEEK_PAUSE:
      self.set_state_and_play_image(gst.STATE_PAUSED, self.PLAY_IMAGE)
      self.mode = self.MODE_PAUSE
      return False
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
    if state == gst.STATE_PLAYING:
      self.mode = self.MODE_PLAY
    elif state == gst.STATE_PAUSED:
      self.mode = self.MODE_PAUSE
    elif state == gst.STATE_NULL:
      self.mode = self.MODE_STOP
    
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
    
  def dec_speed(self):
    speed = self.speed
    if speed > 1:
      speed /= 2
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

