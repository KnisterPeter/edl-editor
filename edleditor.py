#!/usr/bin/python

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, Gtk, Gdk
from gi.repository import GdkX11, GstVideo

import sys, os
import urllib2
from datetime import timedelta
import pyedl

class EDL_Editor:
  
  TIMEOUT = 100
  
  REWIND_IMAGE = Gtk.Image(stock=Gtk.STOCK_MEDIA_REWIND, icon_size=Gtk.IconSize.BUTTON)
  PREVIOUS_FRAME = Gtk.Image(stock=Gtk.STOCK_MEDIA_PREVIOUS, icon_size=Gtk.IconSize.BUTTON)
  PLAY_IMAGE = Gtk.Image(stock=Gtk.STOCK_MEDIA_PLAY, icon_size=Gtk.IconSize.BUTTON)
  PAUSE_IMAGE = Gtk.Image(stock=Gtk.STOCK_MEDIA_PAUSE, icon_size=Gtk.IconSize.BUTTON)
  STOP_IMAGE = Gtk.Image(stock=Gtk.STOCK_MEDIA_STOP, icon_size=Gtk.IconSize.BUTTON)
  NEXT_FRAME = Gtk.Image(stock=Gtk.STOCK_MEDIA_NEXT, icon_size=Gtk.IconSize.BUTTON)
  FORWARD_IMAGE = Gtk.Image(stock=Gtk.STOCK_MEDIA_FORWARD, icon_size=Gtk.IconSize.BUTTON)
  
  PREVIOUS_MARKER = Gtk.Image(stock=Gtk.STOCK_GOTO_FIRST, icon_size=Gtk.IconSize.BUTTON)
  MARK_START = Gtk.Image(stock=Gtk.STOCK_GO_BACK, icon_size=Gtk.IconSize.BUTTON)
  MARK_DELETE = Gtk.Image(stock=Gtk.STOCK_DELETE, icon_size=Gtk.IconSize.BUTTON)
  MARK_END = Gtk.Image(stock=Gtk.STOCK_GO_FORWARD, icon_size=Gtk.IconSize.BUTTON)
  NEXT_MARKER = Gtk.Image(stock=Gtk.STOCK_GOTO_LAST, icon_size=Gtk.IconSize.BUTTON)
  
  SAVE = Gtk.Image(stock=Gtk.STOCK_FLOPPY, icon_size=Gtk.IconSize.BUTTON)
  
  MODE_STOP = 0
  MODE_PAUSE = 1
  MODE_SEEK_PAUSE = 2
  MODE_PLAY = 100

  def __init__(self):
    filepath = os.path.abspath(sys.argv[1])
    if not os.path.isfile(filepath):
      print "File", filepath, "not found"
      sys.exit(1)

    self.speed = 1.0
    self.progress = "0:00 / 0:00"
    self.mode = self.MODE_STOP
    self.position = 0
    self.duration = -1
    self.start = None
    self.end = None
    
    self.setup_ui()
    self.setup_pipeline(filepath)

    self.set_state_and_play_image(Gst.State.PAUSED, self.PLAY_IMAGE)

  def setup_ui(self):
    self.movie_window = Gtk.DrawingArea()
    self.movie_window.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 1))

    self.slider = Gtk.HScale()
    self.slider.set_range(0, 100)
    self.slider.set_increments(1, 60)
    self.slider.set_draw_value(False)
    self.slider.connect('value-changed', self.on_slider_change)

    self.rewind_60s = Gtk.Button('< 60')
    self.rewind_60s.connect("clicked", self.on_rewind_60s)
    self.rewind_10s = Gtk.Button('< 10')
    self.rewind_10s.connect("clicked", self.on_rewind_10s)
    self.rewind_5s = Gtk.Button('< 5')
    self.rewind_5s.connect("clicked", self.on_rewind_5s)
    self.rewind_1s = Gtk.Button('< 1')
    self.rewind_1s.connect("clicked", self.on_rewind_1s)
    self.rewind_1_halfs = Gtk.Button('< 1/2')
    self.rewind_1_halfs.connect("clicked", self.on_rewind_1_halfs)
    self.rewind_button = Gtk.Button()
    self.rewind_button.set_image(self.REWIND_IMAGE)
    self.rewind_button.connect("clicked", self.on_rewind)
    self.play_button = Gtk.Button()
    self.play_button.set_image(self.PLAY_IMAGE)
    self.play_button.connect("clicked", self.on_play_pause)
    self.forward_button = Gtk.Button()
    self.forward_button.set_image(self.FORWARD_IMAGE)
    self.forward_button.connect("clicked", self.on_forward)
    self.forward_1_halfs = Gtk.Button('1/2 >')
    self.forward_1_halfs.connect("clicked", self.on_forward_1_halfs)
    self.forward_1s = Gtk.Button('1 >')
    self.forward_1s.connect("clicked", self.on_forward_1s)
    self.forward_5s = Gtk.Button('5 >')
    self.forward_5s.connect("clicked", self.on_forward_5s)
    self.forward_10s = Gtk.Button('10 >')
    self.forward_10s.connect("clicked", self.on_forward_10s)
    self.forward_60s = Gtk.Button('60 >')
    self.forward_60s.connect("clicked", self.on_forward_60s)
    self.forward_120s = Gtk.Button('120 >')
    self.forward_120s.connect("clicked", self.on_forward_120s)

    self.previous_marker_button = Gtk.Button()
    self.previous_marker_button.set_image(self.PREVIOUS_MARKER)
    self.previous_marker_button.connect("clicked", self.on_previous_marker)
    self.start_marker_button = Gtk.Button()
    self.start_marker_button.set_image(self.MARK_START)
    self.start_marker_button.connect("clicked", self.on_mark_start)
    self.delete_marker_button = Gtk.Button()
    self.delete_marker_button.set_image(self.MARK_DELETE)
    self.delete_marker_button.connect("clicked", self.on_mark_delete)
    self.end_marker_button = Gtk.Button()
    self.end_marker_button.set_image(self.MARK_END)
    self.end_marker_button.connect("clicked", self.on_mark_end)
    self.next_marker_button = Gtk.Button()
    self.next_marker_button.set_image(self.NEXT_MARKER)
    self.next_marker_button.connect("clicked", self.on_next_marker)

    self.save_button = Gtk.Button()
    self.save_button.set_image(self.SAVE)
    self.save_button.connect("clicked", self.on_save)

    hbox = Gtk.HBox()
    hbox.pack_start(self.rewind_60s, False, False, 0)
    hbox.pack_start(self.rewind_10s, False, False, 0)
    hbox.pack_start(self.rewind_5s, False, False, 0)
    hbox.pack_start(self.rewind_1s, False, False, 0)
    hbox.pack_start(self.rewind_1_halfs, False, False, 0)
    hbox.pack_start(self.rewind_button, False, False, 0)
    hbox.pack_start(self.play_button, False, False, 0)
    hbox.pack_start(self.forward_button, False, False, 0)
    hbox.pack_start(self.forward_1_halfs, False, False, 0)
    hbox.pack_start(self.forward_1s, False, False, 0)
    hbox.pack_start(self.forward_5s, False, False, 0)
    hbox.pack_start(self.forward_10s, False, False, 0)
    hbox.pack_start(self.forward_60s, False, False, 0)
    hbox.pack_start(self.forward_120s, False, False, 0)
    hbox.pack_start(Gtk.VSeparator(), False, True, 5)
    hbox.pack_start(self.previous_marker_button, False, False, 0)
    hbox.pack_start(self.start_marker_button, False, False, 0)
    hbox.pack_start(self.delete_marker_button, False, False, 0)
    hbox.pack_start(self.end_marker_button, False, False, 0)
    hbox.pack_start(self.next_marker_button, False, False, 0)
    hbox.pack_start(Gtk.VSeparator(), False, True, 5)
    hbox.pack_start(self.save_button, False, False, 0)

    self.label_time = Gtk.Label(self.progress)
    self.label_speed = Gtk.Label("%f x" % self.speed)
    sbox = Gtk.HBox()
    sbox.pack_start(self.label_time, False, True, 5)
    sbox.pack_start(Gtk.VSeparator(), False, True, 5)
    sbox.pack_start(self.label_speed, False, True, 5)

    vbox = Gtk.VBox()
    vbox.add(self.movie_window)
    vbox.pack_start(self.slider, False, True, 5)
    vbox.pack_start(hbox, False, True, 5)
    vbox.pack_start(sbox, False, True, 5)
    
    self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    self.window.set_title("EDL Editor")
    self.window.set_default_size(800, 600)
    self.window.set_size_request(600, 50)
    self.window.connect('destroy', self.on_destroy)
    self.window.add(vbox)
    self.window.show_all()
    self.xid = self.movie_window.get_property('window').get_xid()
    
  def setup_pipeline(self, filepath):
    self.player = Gst.ElementFactory.make('playbin', None)
    self.player.set_state(Gst.State.READY)
    self.player.set_property("uri", "file://" + urllib2.quote(filepath))
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

  ###
  # Event handler
  ###

  def on_message(self, bus, message):
    t = message.type
    if t == Gst.MessageType.ERROR:
      self.set_state_and_play_image(Gst.State.NULL, self.PLAY_IMAGE)
      err, debug = message.parse_error()
      print "Error: %s" % err, debug
    elif t == Gst.MessageType.DURATION_CHANGED:
      self.duration = -1

  def on_destroy(self, window):
    self.mode = self.MODE_STOP
    self.player.set_state(Gst.State.NULL)
    Gtk.main_quit()

  def on_sync_message(self, bus, message):
    if message.get_structure() is None:
      return
    message_name = message.get_structure().get_name()
    if message_name == "prepare-window-handle":
      imagesink = message.src
      imagesink.set_property("force-aspect-ratio", True)
      imagesink.set_window_handle(self.xid)

  def on_rewind_60s(self, w):
    if self.mode == self.MODE_PAUSE:
      self.seek_paused(-60)

  def on_rewind_10s(self, w):
    if self.mode == self.MODE_PAUSE:
      self.seek_paused(-10)

  def on_rewind_5s(self, w):
    if self.mode == self.MODE_PAUSE:
      self.seek_paused(-5)

  def on_rewind_1s(self, w):
    if self.mode == self.MODE_PAUSE:
      self.seek_paused(-1)

  def on_rewind_1_halfs(self, w):
    if self.mode == self.MODE_PAUSE:
      self.seek_paused(-0.5)

  def on_rewind(self, w):
    if self.mode >= self.MODE_PLAY:
      self.set_speed(self.dec_speed())

  def on_play_pause(self, w):
    if self.mode < self.MODE_PLAY:
      self.set_state_and_play_image(Gst.State.PLAYING, self.PAUSE_IMAGE)
      GObject.timeout_add(self.TIMEOUT, self.update_slider)
    else:
      if self.speed <= 1.0:
        self.set_state_and_play_image(Gst.State.PAUSED, self.PLAY_IMAGE)
      self.set_speed(1.0)

  def on_forward(self, w):
    if self.mode >= self.MODE_PLAY:
      self.set_speed(self.inc_speed())

  def on_forward_1s(self, w):
    if self.mode == self.MODE_PAUSE:
      self.seek_paused(1)

  def on_forward_5s(self, w):
    if self.mode == self.MODE_PAUSE:
      self.seek_paused(5)

  def on_forward_1_halfs(self, w):
    if self.mode == self.MODE_PAUSE:
      self.seek_paused(0.5)

  def on_forward_10s(self, w):
    if self.mode == self.MODE_PAUSE:
      self.seek_paused(10)

  def on_forward_60s(self, w):
    if self.mode == self.MODE_PAUSE:
      self.seek_paused(60)

  def on_forward_120s(self, w):
    if self.mode == self.MODE_PAUSE:
      self.seek_paused(120)

  def on_slider_change(self, slider):
    pos = self.slider.get_value()
    self.player.seek_simple(Gst.Format.TIME, 
      Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, 
      pos)
    if self.mode == self.MODE_PAUSE:
      self.set_state_and_play_image(Gst.State.PLAYING, self.PLAY_IMAGE)
      self.mode = self.MODE_SEEK_PAUSE
      GObject.timeout_add(self.TIMEOUT, self.update_slider)

  def on_previous_marker(self, button):
    t = self.edl.getPrevBoundary(timedelta(seconds=self.position / Gst.SECOND))
    self.seek_to(t.days*86400+t.seconds * Gst.SECOND)

  def on_mark_start(self, button):
    self.start = self.position
    self.new_marker()

  def on_mark_delete(self, button):
    t = timedelta(seconds=self.position / Gst.SECOND)
    block = self.edl.findBlock(t)
    if block is not None:
      self.edl.deleteBlock(t)
      self.redraw_marker()
    self.start = None
    self.end = None

  def on_mark_end(self, button):
    self.end = self.position
    self.new_marker()

  def on_next_marker(self, button):
    t = self.edl.getNextBoundary(timedelta(seconds=self.position / Gst.SECOND))
    if t != None:
      self.seek_to(t.days*86400+t.seconds * Gst.SECOND)
    elif self.duration != -1:
      self.seek_to(self.duration - Gst.SECOND / 2)

  def on_save(self, button):
    self.edl.normalize(timedelta(seconds=self.duration / Gst.SECOND))
    pyedl.dump(self.edl, open(self.edlfile, "w"))

  ###
  # UI operations
  ###

  def draw_markers(self):
    for block in self.edl:
      start = float(block.startTime.days * 86400 + block.startTime.seconds * Gst.SECOND)
      end = float(block.stopTime.days * 86400 + block.stopTime.seconds * Gst.SECOND)
      self.add_marker(start, end)

  def add_marker(self, start, end):
    self.slider.add_mark(start, 0, None)
    self.slider.add_mark(end, 0, None)

  def redraw_marker(self):
    self.slider.clear_marks()
    self.draw_markers()

  def setup_duration(self):
    _, self.duration = self.player.query_duration(Gst.Format.TIME)
    self.slider.handler_block_by_func(self.on_slider_change)
    self.slider.set_range(0, self.duration)
    self.slider.handler_unblock_by_func(self.on_slider_change)
    
  def update_slider(self):
    if self.duration == -1:
      self.setup_duration()
      self.draw_markers()

    if self.mode < self.MODE_SEEK_PAUSE:
      return False
    try:
      _, self.position = self.player.query_position(Gst.Format.TIME)

      self.slider.handler_block_by_func(self.on_slider_change)
      self.slider.set_value(self.position)
      self.slider.handler_unblock_by_func(self.on_slider_change)

      cur = self.format_nanos(self.position)
      end = self.format_nanos(self.duration)
      self.progress = '%s / %s' % (cur, end)
      self.update_status()
    except Gst.QueryError:
      pass
    if self.mode == self.MODE_SEEK_PAUSE:
      self.set_state_and_play_image(Gst.State.PAUSED, self.PLAY_IMAGE)
      self.mode = self.MODE_PAUSE
      return False
    return True
    
  def update_status(self):
    self.label_time.set_text(self.progress)
    self.label_speed.set_text("%.2f x" % self.speed)

  ###
  # Util operations
  ###
    
  def new_marker(self):
    if self.start != None and self.end != None:
      self.edl.newBlock(
        timedelta(seconds=self.start / Gst.SECOND), 
        timedelta(seconds=self.end / Gst.SECOND))
      self.add_marker(self.start, self.end)
      self.start = None
      self.end = None

  def seek_to(self, pos):
    self.set_state_and_play_image(Gst.State.PLAYING, self.PLAY_IMAGE)
    self.mode = self.MODE_SEEK_PAUSE
    self.player.seek_simple(Gst.Format.TIME, 
      Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
      pos)
    GObject.timeout_add(self.TIMEOUT, self.update_slider)

  def seek_paused(self, offset):
    self.set_state_and_play_image(Gst.State.PLAYING, self.PLAY_IMAGE)
    self.mode = self.MODE_SEEK_PAUSE
    _, ns = self.player.query_position(Gst.Format.TIME)
    pos = ns  + offset * Gst.SECOND
    if pos < 0:
      pos = 0
    self.player.seek_simple(Gst.Format.TIME, 
      Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
      pos)
    GObject.timeout_add(self.TIMEOUT, self.update_slider)

  def set_speed(self, speed=1.0):
    self.speed = speed
    _, ns = self.player.query_position(Gst.Format.TIME)
    self.player.seek(speed, 
      Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
      Gst.SeekType.SET, ns,
      Gst.SeekType.NONE, 0)
    self.update_status()

  def set_state_and_play_image(self, state, image):
    if state == Gst.State.PLAYING:
      self.mode = self.MODE_PLAY
    elif state == Gst.State.PAUSED:
      self.mode = self.MODE_PAUSE
    elif state == Gst.State.NULL:
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
    
if __name__ == "__main__":
  GObject.threads_init()
  Gst.init(None)
  EDL_Editor()
  Gtk.main()

