# -*- coding : UTF-8 -*-
"""
:filename: sppas.ui.wxapp.page_editor.media.smmpctrl.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  A base class panel to display buttons for a media player.

.. _This file is part of SPPAS: https://sppas.org/
..
    -------------------------------------------------------------------------

     ######   ########   ########      ###      ######
    ##    ##  ##     ##  ##     ##    ## ##    ##    ##     the automatic
    ##        ##     ##  ##     ##   ##   ##   ##            annotation
     ######   ########   ########   ##     ##   ######        and
          ##  ##         ##         #########        ##        analysis
    ##    ##  ##         ##         ##     ##  ##    ##         of speech
     ######   ##         ##         ##     ##   ######

    Copyright (C) 2011-2026  Brigitte Bigi, CNRS
    Laboratoire Parole et Langage, Aix-en-Provence, France

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

    This banner notice must not be removed.

    -------------------------------------------------------------------------

The main class to control a multi media player.

Requires the following libraries:

 - sounddevice, installed by the audioplay feature;
 - opencv, installed by the videoplay feature.

"""

import os
import wx
import wx.lib.gizmos as gizmos

from sppas.core.config import paths  # used only in the Test Panel
from sppas.core.coreutils import info
from sppas.ui.wxapp.players.smmps import sppasMMPS
from sppas.ui.wxapp.windows.buttons import BitmapButton
from sppas.ui.wxapp.windows.buttons import ToggleButton
from sppas.ui.wxapp.windows.panels import sppasPanel

from ..datactrls.videoframe import VideoAnnotationFrame

from .mediaevents import MediaEvents
from .playerctrlspanel import sppasPlayerControlsPanel

# ---------------------------------------------------------------------------

SCROLL_TO_LEFT_TOOLTIP = info(9301, "ui")
ZOOM_ALL_TOOLTIP = info(9311, "ui")
ZOOM_IN_TOOLTIP = info(9321, "ui")
ZOOM_OUT_TOOLTIP = info(9331, "ui")
SCROLL_TO_SELECTION_TOOLTIP = info(9341, "ui")
ZOOM_TO_SELECTION_TOOLTIP = info(9351, "ui")
SCROLL_TO_RIGHT_TOOLTIP = info(9361, "ui")

SORT_FILES_TOOLTIP = info(9401, "ui")
INCREASE_OBJ_HEIGHT_TOOLTIP = info(9411, "ui")
DECREASE_OBJ_HEIGHT_TOOLTIP = info(9421, "ui")
TIER_ANN_OR_INFO_TOOLTIP = info(9431, "ui")
WAVEFORM_AUDIO_OR_INFO_TOOLTIP = info(9441, "ui")
FRAMES_RECT_VIDEO_OR_INFO_TOOLTIP = info(9451, "ui")

# ---------------------------------------------------------------------------


class sppasMMPCtrl(sppasPlayerControlsPanel):
    """Create a panel with controls to manage media.

    This class is inheriting a PlayerControl and embedding a SMMPS because
    it failed to instantiate when it was inheriting both.

    """

    def __init__(self, parent,
                 id=wx.ID_ANY,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=0,
                 name="smmpc_panel"):
        """Create a sppasPlayerControlsPanel embedding a sppasMMPS.

        :param parent: (wx.Window) Parent window must NOT be none
        :param id: (int) window identifier or -1
        :param pos: (wx.Pos) the control position
        :param size: (wx.Size) the control size
        :param style: (int) the underlying window style
        :param name: (str) the widget name.

        """
        super().__init__(parent, id, pos, size, style, name)

        self.__smmps = sppasMMPS(owner=self)
        self._create_mmpc_content()
        self._setup_mmpc_events()

        try:
            s = wx.GetApp().settings
            self.SetBackgroundColour(s.bg_color)
            self.SetForegroundColour(s.fg_color)
            self.SetFont(s.text_font)
        except AttributeError:
            self.InheritAttributes()

    # -----------------------------------------------------------------------

    def SetBackgroundColour(self, colour):
        """Set the background of our panel to the given color or hi-color."""
        wx.Panel.SetBackgroundColour(self, colour)
        hi_color = self.GetHighlightedBackgroundColour()

        for name in ("transport", "widgets_left", "widgets_right", "slider"):
            w = self.FindWindow(name + "_panel")
            w.SetBackgroundColour(colour)
            for c in w.GetChildren():
                if isinstance(c, ToggleButton) is True:
                    c.SetBackgroundColour(hi_color)
                elif c.GetName() == "time_ruler":
                    c.SetBackgroundColour(wx.Colour(250, 250, 165))
                else:
                    c.SetBackgroundColour(colour)

        self.led.SetBackgroundColour(colour)

    # -----------------------------------------------------------------------

    def SetForegroundColour(self, colour):
        """Set the foreground of our panel to the given color."""
        wx.Panel.SetForegroundColour(self, colour)
        self._set_led_fg_color()

        for name in ("transport", "widgets_left", "widgets_right", "slider"):
            w = self.FindWindow(name + "_panel")
            w.SetForegroundColour(colour)
            for c in w.GetChildren():
                if c != self.led:
                    c.SetForegroundColour(colour)

    # ----------------------------------------------------------------------

    def _set_led_fg_color(self):
        # The led has its own color, whatever the given one.
        period = self._timeslider.get_range()
        if period[0] == period[1]:
            # self.led.SetForegroundColour(self.GetBackgroundColour())
            self.led.SetForegroundColour(self.GetForegroundColour())
        else:
            if self._timeslider.is_selection() is True:
                # pinky-red
                self.led.SetForegroundColour(self._timeslider.SELECTION_FG_COLOUR)
            else:
                # blue like the toggled button
                self.led.SetForegroundColour(wx.Colour(30, 80, 210))

    # -----------------------------------------------------------------------

    def GetHighlightedBackgroundColour(self):
        """Return a color slightly different of the parent background one."""
        color = self.GetBackgroundColour()
        r, g, b, a = color.Red(), color.Green(), color.Blue(), color.Alpha()
        return wx.Colour(r, g, b, a).ChangeLightness(95)

    # -----------------------------------------------------------------------

    def Zoom(self, value):
        """Apply given zoom value to elements that can be zoomed.

        :param value: (int) Zoom level (percentage).

        """
        value = int(value)
        if value < 50:
            value = 50
        elif value > 300:
            value = 300
        self._timeslider.Zoom(value)

    # -----------------------------------------------------------------------
    # Manage the timeslider
    # -----------------------------------------------------------------------

    def show_range(self, value=True):
        """Show the indicator of the currently selected range of time. """
        self._timeslider.show_range(value)
        self.SetMinSize(self.DoGetBestSize())

    def show_rule(self, value=True):
        """Show the ruler of the current visible range of time. """
        self._timeslider.show_rule(value)
        self.SetMinSize(self.DoGetBestSize())

    def get_visible_range(self):
        """Return the visible time range."""
        return self._timeslider.get_visible_range()

    def set_visible_range(self, start, end):
        """Set the visible time range."""
        self._timeslider.set_visible_range(start, end)

    def get_selection_range(self):
        """Return the selection time range."""
        return self._timeslider.get_selection_range()

    def set_selection_range(self, start, end):
        """Set the selection time range."""
        self._timeslider.set_selection_range(start, end)

    def is_tiers_annotations(self):
        """Return true if the button to show tier annotations is toggled."""
        return self.FindWindow("tier_infos").GetValue()

    def is_audios_waveform(self):
        """Return true if the button to show audio waveform is toggled."""
        return self.FindWindow("sound_infos").GetValue()

    def is_video_film(self):
        """Return true if the button to show video film is toggled."""
        return self.FindWindow("video_infos").GetValue()

    def scroll_to_selection(self, to_notify=False):
        """Set visible range to center the selection on screen.

        Duration of the visible part is preserved.

        """
        # get the duration of the visible part
        start = self._timeslider.get_visible_start()
        end = self._timeslider.get_visible_end()
        dur = end - start
        # get selection time values to be centered
        sel_start = self._timeslider.get_selection_start()
        sel_end = self._timeslider.get_selection_end()
        # estimate the middle time
        sel_middle = sel_start + ((sel_end - sel_start) / 2.)
        shift = dur / 2.
        # Set visible range to center the selection without changing the duration
        self._timeslider.set_visible_range(sel_middle - shift, sel_middle + shift)
        self.__update_after_event(start, end, to_notify)

    # -----------------------------------------------------------------------
    # Construct the panel
    # -----------------------------------------------------------------------

    def _create_mmpc_content(self) -> None:
        """Add widgets to the content of this panel."""

        led = gizmos.LEDNumberCtrl(parent=self._transport_panel, style=wx.BORDER_NONE, name="moment_led")
        led.SetValue("0.000")
        led.SetAlignment(alignment=gizmos.LED_ALIGN_RIGHT)
        led.SetDrawFaded(drawFaded=False)
        led.SetMinSize(wx.Size(width=self.get_font_height() * 10, height=self._btn_size))
        self._transport_panel.GetSizer().Prepend(window=led,
                                                 proportion=0,
                                                 flag=wx.ALIGN_CENTER | wx.ALL,
                                                 border=sppasPanel.fix_size(2))
        # The LED has its own colors that we have to override
        self._set_led_fg_color()
        self.led.SetBackgroundColour(self.GetBackgroundColour())

        # -----------------------------------------------------------------------

        btn1 = BitmapButton(parent=self.widgets_left_panel, name="scroll_left")
        btn1.SetToolTip(SCROLL_TO_LEFT_TOOLTIP)
        self.SetButtonProperties(btn1)
        self.AddLeftWidget(btn1)
        btn1.Bind(event=wx.EVT_BUTTON, handler=self._process_button_event)

        btn7 = BitmapButton(parent=self.widgets_left_panel, name="scroll_zoom_all")
        btn7.SetToolTip(ZOOM_ALL_TOOLTIP)
        self.SetButtonProperties(btn7)
        self.AddLeftWidget(btn7)
        btn7.Bind(event=wx.EVT_BUTTON, handler=self._process_button_event)

        btn3 = BitmapButton(parent=self.widgets_left_panel, name="zoom_in")
        btn3.SetToolTip(ZOOM_IN_TOOLTIP)
        self.SetButtonProperties(btn3)
        self.AddLeftWidget(btn3)
        btn3.Bind(event=wx.EVT_BUTTON, handler=self._process_button_event)

        btn4 = BitmapButton(parent=self.widgets_left_panel, name="zoom_out")
        btn4.SetToolTip(ZOOM_OUT_TOOLTIP)
        self.SetButtonProperties(btn4)
        self.AddLeftWidget(btn4)
        btn4.Bind(event=wx.EVT_BUTTON, handler=self._process_button_event)

        btn5 = BitmapButton(parent=self.widgets_left_panel, name="scroll_to_selection")
        btn5.SetToolTip(SCROLL_TO_SELECTION_TOOLTIP)
        self.SetButtonProperties(btn5)
        self.AddLeftWidget(btn5)
        btn5.Bind(event=wx.EVT_BUTTON, handler=self._process_button_event)

        btn6 = BitmapButton(parent=self.widgets_left_panel, name="scroll_zoom_selection")
        btn6.SetToolTip(ZOOM_TO_SELECTION_TOOLTIP)
        self.SetButtonProperties(btn6)
        self.AddLeftWidget(btn6)
        btn6.Bind(event=wx.EVT_BUTTON, handler=self._process_button_event)

        btn2 = BitmapButton(parent=self.widgets_left_panel, name="scroll_right")
        btn2.SetToolTip(SCROLL_TO_RIGHT_TOOLTIP)
        self.SetButtonProperties(btn2)
        self.AddLeftWidget(btn2)
        btn2.Bind(event=wx.EVT_BUTTON, handler=self._process_button_event)

        # -----------------------------------------------------------------------

        btnr1 = ToggleButton(parent=self.widgets_right_panel, name="tier_infos")
        btnr1.SetToolTip(TIER_ANN_OR_INFO_TOOLTIP)
        self.SetButtonProperties(btnr1)
        self.AddRightWidget(btnr1)
        btnr1.Bind(event=wx.EVT_TOGGLEBUTTON, handler=self._process_button_event)

        btnr2 = ToggleButton(parent=self.widgets_right_panel, name="sound_infos")
        btnr2.SetToolTip(WAVEFORM_AUDIO_OR_INFO_TOOLTIP)
        self.SetButtonProperties(btnr2)
        self.AddRightWidget(btnr2)
        btnr2.Bind(event=wx.EVT_TOGGLEBUTTON, handler=self._process_button_event)

        btnr3 = ToggleButton(parent=self.widgets_right_panel, name="video_infos")
        btnr3.SetToolTip(FRAMES_RECT_VIDEO_OR_INFO_TOOLTIP)
        self.SetButtonProperties(btnr3)
        self.AddRightWidget(btnr3)
        btnr3.Bind(event=wx.EVT_TOGGLEBUTTON, handler=self._process_button_event)

        btn_up = BitmapButton(parent=self.widgets_right_panel, name="zoom_up")
        btn_up.SetToolTip(INCREASE_OBJ_HEIGHT_TOOLTIP)
        self.SetButtonProperties(btn_up)
        self.AddRightWidget(btn_up)
        btn_up.Bind(event=wx.EVT_BUTTON, handler=self._process_button_event)

        btn_down = BitmapButton(parent=self.widgets_right_panel, name="zoom_down")
        btn_down.SetToolTip(DECREASE_OBJ_HEIGHT_TOOLTIP)
        self.SetButtonProperties(btn_down)
        self.AddRightWidget(btn_down)
        btn_down.Bind(event=wx.EVT_BUTTON, handler=self._process_button_event)

        btn_sort = BitmapButton(parent=self.widgets_right_panel, name="sort")
        btn_sort.SetToolTip(SORT_FILES_TOOLTIP)
        self.SetButtonProperties(btn_sort)
        self.AddRightWidget(btn_sort)
        btn_sort.Bind(event=wx.EVT_BUTTON, handler=self._process_button_event)

    # -----------------------------------------------------------------------

    @property
    def led(self):
        return self.FindWindow("moment_led")

    # -----------------------------------------------------------------------
    # Overridden methods...
    # -----------------------------------------------------------------------

    def play(self):
        """Override. Start playing all the enabled media."""
        if self.__smmps.is_playing() is True or self.__smmps.is_loading() is True:
            return False

        # update the period in the smmps only if required (media no paused)
        # if self.__smmps.is_paused() is False:
        # get the period of the ruler & the period of the smmps
        ruler_start, ruler_end = self._timeslider.get_range()
        smmps_start, smmps_end = self.__smmps.get_period()
        # update the period in the smmps only if required
        if ruler_start != smmps_start or ruler_end != smmps_end:
            try:
                # fix the period of time.
                # seek at it's beginning if current position becomes invalid
                self.__smmps.set_period(ruler_start, ruler_end)
            except ValueError as e:
                wx.LogError(str(e))
                return False

        self.notify(action="play", value=None)
        self.__smmps.play()
        # self.prev_time = datetime.datetime.now()
        self.FindWindow("media_pause").SetValue(False)

        return True

    # -----------------------------------------------------------------------

    def pause(self):
        """Pause in playing the media."""
        pause_status = self.FindWindow("media_pause").GetValue()

        # It was asked to pause
        if pause_status is True:
            # and the audio is not already paused
            if self.__smmps.is_paused() is False:
                paused = self.__smmps.pause()
                if paused is not True:
                    # but paused was not done in the audio
                    self.FindWindow("media_pause").SetValue(False)
                else:
                    # Put the slider exactly at the right time position
                    position = self.__smmps.tell()
                    self._timeslider.set_value(position)
                    self.led.SetValue("{:.3f}".format(position))

        else:
            # it was asked to end pausing
            if self.__smmps.is_paused() is True:
                self.play()

    # -----------------------------------------------------------------------

    def play_frame(self, direction=1):
        """Play the previous or next frame of the video media.

        Play the next or previous frame if media state is stopped or paused.
        Direction indicates "how far" to play the next or the previous:
        1 = next, 2 = the 2nd next, 3 = the 3rd next, etc.

        :param direction: 1=next / -1=previous

        """
        if self.__smmps.is_playing() is True or self.__smmps.is_loading() is True:
            return False

        if direction == 1:
            direction = int(self._transport_panel.FindWindow("next_frame_direction_value").GetValue())
        if direction == -1:
            direction = -(int(self._transport_panel.FindWindow("previous_frame_direction_value").GetValue()))

        # get the period of the ruler & the period of the smmps
        ruler_start, ruler_end = self._timeslider.get_range()
        smmps_start, smmps_end = self.__smmps.get_period()
        # update the period in the smmps only if required
        if ruler_start != smmps_start or ruler_end != smmps_end:
            try:
                # fix the period of time.
                # seek at it's beginning if current position becomes invalid
                self.__smmps.set_period(ruler_start, ruler_end)
            except ValueError as e:
                wx.LogError(str(e))
                return False

        success = self.__smmps.play_frame(direction)
        if success is False and self.IsReplay() is True:
            # Try again at the beginning of the period
            self.stop()
            success = self.__smmps.play_frame(direction)

        if success is True:
            position = self.__smmps.tell()
            self._timeslider.set_value(position)
            self.led.SetValue("{:.3f}".format(position))

        return success

    # -----------------------------------------------------------------------

    def stop(self):
        """Stop to play the media."""
        self.__smmps.stop()
        # self.prev_time = None
        self.DeletePendingEvents()
        self.FindWindow("media_pause").SetValue(False)

        # Put the slider exactly at the right time position, i.e. the
        # beginning of the defined period (and not self.__smmps.tell())
        period = self._timeslider.get_range()
        position = period[0]
        self._timeslider.set_value(position)
        self.led.SetValue("{:.3f}".format(position))
        self.notify(action="stop", value=None)

    # -----------------------------------------------------------------------

    def media_rewind(self):
        """Seek media 10% earlier but no more than the beginning of the period."""
        d = self.__smmps.get_duration()
        d /= 10.
        cur = self.__smmps.tell()
        period = self._timeslider.get_range()

        self.__smmps.seek(max(period[0], cur - d))
        position = self.__smmps.tell()
        self._timeslider.set_value(position)
        self.led.SetValue("{:.3f}".format(position))

    # -----------------------------------------------------------------------

    def media_forward(self):
        """Seek media 10% later but no more than the end of the period."""
        duration = self.__smmps.get_duration()
        d = duration / 10.
        cur = self.__smmps.tell()
        period = self._timeslider.get_range()
        position = min(cur + d, period[1])

        # if we reach the end of the stream for the given period
        if position == period[1]:
            if self.IsReplay() is True:
                position = 0.  # restart from the beginning
            else:
                self.stop()
                return

        self.__smmps.seek(position)
        position = self.__smmps.tell()
        self._timeslider.set_value(position)
        self.led.SetValue("{:.3f}".format(position))

    # -----------------------------------------------------------------------

    def media_seek(self, value):
        """Seek media at given time value inside the period."""
        self.__smmps.seek(value)
        self._timeslider.set_value(value)
        self.led.SetValue("{:.3f}".format(value))

    # -----------------------------------------------------------------------

    def media_period(self, start, end):
        """Override. Set time period to media at given time range."""
        # no need to force to set the period to the media right now because
        # the media will get the period when needed.
        # self.__smmps.set_period(start, end)

        # but a change of period can imply a change of the moment value:
        value = self.__smmps.tell()
        self._timeslider.set_value(value)
        self.led.SetValue("{:.3f}".format(value))

    # -----------------------------------------------------------------------
    # Multi Media Player
    # -----------------------------------------------------------------------

    def add_audio(self, filename):
        """Load the files that filenames refers to.

        The event MediaLoaded or MediaNotLoaded is sent when the audio
        finished to load. Loaded successfully or not, the audio is disabled.

        :param filename: (str) Name of a file or list of file names
        :return: (bool) Always returns False

        """
        self.__smmps.add_audio(filename)
        # The media will send an EVT_MEDIA_XXX when loaded

    # -----------------------------------------------------------------------

    def add_video(self, filename, player=None):
        """Add a video into the list of media managed by this control.

        The new video is disabled.

        :param filename: (str) A filename or a list of file names
        :param player: (wx.Window) a window or a list of wx windows
        :return: (bool)

        """
        self.__smmps.add_video(filename, player)
        # The media will send an EVT_MEDIA_XXX when loaded

    # -----------------------------------------------------------------------

    def add_unsupported(self, filename, duration):
        """Add a file into the list managed by this control.

        :param filename: (str) A filename or a list of file names
        :param duration: (float) Duration of this file
        :return: (bool)

        """
        self.__smmps.add_unsupported(filename, duration)

        # Update the duration of the slider with the longest duration
        duration = self.__smmps.get_duration()
        self._timeslider.set_duration(duration)

    # -----------------------------------------------------------------------

    def add_media(self, media):
        """Add a media into the list of media managed by this control.

        The new media is disabled.

        :param media: (sppasBasePlayer)
        :return: (bool)

        """
        self.__smmps.add_media(media)

    # -----------------------------------------------------------------------

    def enable(self, filename, value=True):
        """Enable or disable the given media.

        When a media is disabled, it can't be paused nor played. It can only
        stay in the stopped state.

        :param filename: (str)
        :param value: (bool)
        :return: (bool)

        """
        self.__smmps.enable(filename, value)

    # -----------------------------------------------------------------------

    def remove_media(self, filename):
        """Remove a file of the list of media."""
        self.__smmps.remove_media(filename)

    # -----------------------------------------------------------------------

    def get_duration(self, filename=None):
        """Return the duration this player must consider (in seconds)."""
        return self.__smmps.get_duration(filename)

    def exists(self, filename):
        """Return True if the given filename is matching an existing media."""
        return self.__smmps.exists(filename)

    def is_enabled(self, filename=None):
        """Return True if any media or the given one is enabled."""
        return self.__smmps.is_enabled(filename)

    def is_unknown(self, filename=None):
        """Return True if any media or if the given one is unknown."""
        return self.__smmps.is_unknown(filename)

    def is_audio(self, filename=None):
        """Return True if any media or if the given one is an audio."""
        return self.__smmps.is_audio(filename)

    def is_video(self, filename=None):
        """Return True if any media or if the given one is a video."""
        return self.__smmps.is_video(filename)

    def get_nchannels(self, filename):
        """Return the number of channels."""
        return self.__smmps.get_nchannels(filename)

    def get_sampwidth(self, filename):
        return self.__smmps.get_sampwidth(filename)

    def get_framerate(self, filename):
        return self.__smmps.get_framerate(filename)

    def get_frames(self, filename):
        return self.__smmps.get_frames(filename)

    def get_video_width(self, filename):
        return self.__smmps.get_video_width(filename)

    def get_video_height(self, filename):
        return self.__smmps.get_video_height(filename)

    def is_loading(self):
        return self.__smmps.is_loading()

    # -----------------------------------------------------------------------
    # Events
    # -----------------------------------------------------------------------

    def _setup_mmpc_events(self):
        """Associate a handler function with the events. """
        # Custom event to inform the media is loaded
        # self.__smmps.Bind(MediaEvents.EVT_MEDIA_LOADED, self.__on_media_loaded)
        self.Bind(MediaEvents.EVT_MEDIA_LOADED, self.__on_media_loaded)
        self.Bind(MediaEvents.EVT_MEDIA_NOT_LOADED, self.__on_media_not_loaded)
        # Event received every X ms when the audio is playing
        self.Bind(wx.EVT_TIMER, self.__on_timer)

        # Capture keys
        self.Bind(wx.EVT_CHAR_HOOK, self._process_key_event)

    # -----------------------------------------------------------------------

    def _process_key_event(self, event):
        """Process a key event or skip it.

        https://www.wxpython.org/Phoenix/docs/html/wx.KeyCode.enumeration.html#wx-keycode

        :param event: (wx.Event)

        """
        key_code = event.GetKeyCode()

        if event.ControlDown() is True and event.AltDown() is False and event.ShiftDown() is False:
            if key_code == wx.WXK_LEFT:
                self.__scroll_left()
            elif key_code == wx.WXK_RIGHT:
                self.__scroll_right()
            elif key_code == 65:     # ctrl+a
                self.__zoom_all()
            elif key_code == 73:     # ctrl+i
                self.__zoom_in()
            elif key_code == 79:     # ctrl+o
                self.__zoom_out()
            else:
                event.Skip()

        elif event.ControlDown() is False and event.AltDown() is False and event.ShiftDown() is True:
            if key_code == wx.WXK_LEFT:
                self.play_frame(direction=-1)
            elif key_code == wx.WXK_RIGHT:
                self.play_frame(direction=1)
            else:
                event.Skip()

        elif key_code == wx.WXK_MEDIA_STOP:
            # The "stop" media key of the keyboard: do the same as the button.
            self.stop()

        elif key_code == wx.WXK_MEDIA_PLAY_PAUSE:
            # The "play/pause" media key of the keyboard is a toggle: do the
            # same as clicking either the play button or the pause one.
            if self.__smmps.is_playing() is True:
                self.FindWindow("media_pause").SetValue(True)
                self.pause()
            else:
                self.play()

        else:
            event.Skip()

    # ----------------------------------------------------------------------

    def _process_button_event(self, event):
        """A button of the toolbar was clicked.

        Scroll the visible part, depending on its current duration:
            - reduce of 50%
            - increase of 100%
            - shift 80% before
            - shift 80% after
        Show or hide annotations, waveform...

        """
        evt_obj = event.GetEventObject()

        if evt_obj.GetName() == "zoom_in":
            self.__zoom_in()

        elif evt_obj.GetName() == "zoom_out":
            self.__zoom_out()

        elif evt_obj.GetName() == "scroll_left":
            self.__scroll_left()

        elif evt_obj.GetName() == "scroll_right":
            self.__scroll_right()

        elif evt_obj.GetName() == "scroll_to_selection":
            self.scroll_to_selection(to_notify=True)

        elif evt_obj.GetName() == "scroll_zoom_selection":
            self.__zoom_sel()

        elif evt_obj.GetName() == "scroll_zoom_all":
            self.__zoom_all()

        elif evt_obj.GetName() == "sort":
            self.notify(action="sort_files", value=True)

        elif evt_obj.GetName() == "tier_infos":
            # value = False = show infos
            # value = True = show annotations
            self.notify(action="tiers_annotations", value=evt_obj.GetValue())

        elif evt_obj.GetName() == "sound_infos":
            # value = True = show waveform
            self.notify(action="audio_waveform", value=evt_obj.GetValue())

        elif evt_obj.GetName() == "video_infos":
            # value = True = show film
            self.notify(action="video_film", value=evt_obj.GetValue())

        elif evt_obj.GetName() in ("zoom_up", "zoom_down"):
            self.notify(action=evt_obj.GetName(), value=None)

        else:
            wx.LogError("Unknown visible action {}".format(evt_obj.GetName()))

    # ----------------------------------------------------------------------

    def __scroll_left(self):
        """Scroll to the left, before the current period."""
        start = self._timeslider.get_visible_start()
        if start > 0.:
            end = self._timeslider.get_visible_end()
            shift = 0.8 * (end - start)
            if start - shift < 0.:
                shift = start
            self._timeslider.set_visible_range(start - shift, end - shift)
            self.__update_after_event(start, end)

    # ----------------------------------------------------------------------

    def __scroll_right(self):
        """Scroll to the right, later than the current period."""
        end = self._timeslider.get_visible_end()
        if end < self._timeslider.get_duration():
            start = self._timeslider.get_visible_start()
            shift = 0.8 * (end - start)
            if end + shift > self._timeslider.get_duration():
                shift = self._timeslider.get_duration() - end
            self._timeslider.set_visible_range(start + shift, end + shift)
            self.__update_after_event(start, end)

    # ----------------------------------------------------------------------

    def __scroll_sel(self):
        """Scroll to display the currently selected ann in the period."""
        start = self._timeslider.get_visible_start()
        end = self._timeslider.get_visible_end()
        self.scroll_to_selection()
        self.__update_after_event(start, end)

    # ----------------------------------------------------------------------

    def __zoom_in(self):
        """Zoom to a shorter period inside the current one."""
        start = self._timeslider.get_visible_start()
        end = self._timeslider.get_visible_end()
        shift = (end - start) / 4.
        self._timeslider.set_visible_range(start + shift, end - shift)
        self.__update_after_event(start, end)

    # ----------------------------------------------------------------------

    def __zoom_out(self):
        """Zoom to a larger period outside the current one."""
        start = self._timeslider.get_visible_start()
        end = self._timeslider.get_visible_end()
        shift = (end - start) / 2.
        self._timeslider.set_visible_range(
            max(0., start - shift),
            min(self._timeslider.get_duration(), end + shift))
        self.__update_after_event(start, end)

    # ----------------------------------------------------------------------

    def __zoom_sel(self):
        """Zoom to the currently selected annotation period."""
        start = self._timeslider.get_visible_start()
        end = self._timeslider.get_visible_end()
        sel_start = self._timeslider.get_selection_start()
        sel_end = self._timeslider.get_selection_end()
        self._timeslider.set_visible_range(sel_start, sel_end)
        self.__update_after_event(start, end)

    # ----------------------------------------------------------------------

    def __zoom_all(self):
        """Zoom to the larger period as possible."""
        start = self._timeslider.get_visible_start()
        end = self._timeslider.get_visible_end()
        new_end = self.__smmps.get_duration()
        self._timeslider.set_duration(new_end)
        self._timeslider.set_visible_range(0., new_end)
        self.__update_after_event(start, end)

    # ----------------------------------------------------------------------

    def __update_after_event(self, start, end, to_notify=True):
        """Update and notify.

        :param start: start value before changes
        :param end: end value before changes

        TODO: check why start/end are not used... they should be!

        """
        # Refresh the timeline
        self._timeslider.Layout()
        self._timeslider.Refresh()

        # Update the led
        new_visible_start = self._timeslider.get_visible_start()
        new_visible_end = self._timeslider.get_visible_end()
        cur_pos = self.__smmps.tell()
        if new_visible_start < cur_pos < new_visible_end:
            self.led.SetValue("{:.3f}".format(cur_pos))
        else:
            self.led.SetValue("{:.3f}".format(self._timeslider.get_enabled_start()))
        self._set_led_fg_color()

        # Notify the parent if the visible part has changed.
        if to_notify is True:
            self.notify(action="visible", value=(new_visible_start, new_visible_end))

    # ----------------------------------------------------------------------

    def _process_period_changed(self, event):
        """Override. Handle the event of a change of time range in the slider."""
        self.stop()
        p = event.period
        self.media_period(p[0], p[1])
        cur_pos = self.__smmps.tell()
        if p[0] < cur_pos < p[1]:
            self.led.SetValue("{:.3f}".format(cur_pos))
        else:
            self.led.SetValue("{:.3f}".format(self._timeslider.get_enabled_start()))
        self._set_led_fg_color()
        self.led.Refresh()

    # -----------------------------------------------------------------------

    def _process_slider_action(self, event):
        """Process a button event: an action has to be performed.

        :param event: (wx.Event)

        """
        if event.action in ("scroll", "zoom"):
            s, e = event.value
            self.media_period(s, e)
            self.__update_after_event(s, e)
        else:
            event.Skip()

    # ----------------------------------------------------------------------

    def __on_media_loaded(self, event):
        filename = event.filename

        self.__smmps.enable(filename)
        self.FindWindow("media_play").Enable(True)
        self.FindWindow("media_pause").Enable(True)

        # Update the duration of the slider with the longest duration
        duration = self.__smmps.get_duration()
        self._timeslider.set_duration(duration)

        # Under MacOS, the following line enters in an infinite loop with the message:
        #   In file /Users/robind/projects/bb2/dist-osx-py38/build/ext/wxWidgets/src/unix/threadpsx.cpp at line 370: 'pthread_mutex_[timed]lock()' failed with error 0x00000023 (Resource temporarily unavailable).
        # Under Linux it crashes with the message:
        #   pure virtual method called
        self.__smmps.set_period(0., duration)

        wx.PostEvent(self.GetParent(), event)

    # ----------------------------------------------------------------------

    def __on_media_not_loaded(self, event):
        filename = event.filename
        wx.LogError("File {} not loaded".format(filename))
        # self.remove(filename)

    # ----------------------------------------------------------------------

    def __on_timer(self, event):
        # at least one audio is still playing
        if self.__smmps.is_playing() is True:
            # if we doesn't want to update the slider so frequently:
            # cur_time = datetime.datetime.now()
            # delta = cur_time - self.prev_time
            # delta_seconds = delta.seconds + delta.microseconds / 1000000.
            # if delta_seconds > self.delta_slider:
            # self.prev_time = cur_time
            time_pos = self.__smmps.tell()
            self._timeslider.set_value(time_pos)
            self.led.SetValue("{:.3f}".format(time_pos))

        # all enabled audio are now stopped
        elif self.__smmps.are_stopped() is True:
            self.stop()
            if self.IsReplay() is True:
                self.play()

# ---------------------------------------------------------------------------


class TestPanel(sppasPanel):

    def __init__(self, parent):
        super(TestPanel, self).__init__(parent, name="SMMPS + Controls")

        button1 = wx.Button(self, -1, size=(100, 50), label="LOAD with threads", name="load_button_1")
        button2 = wx.Button(self, -1, size=(100, 50), label="LOAD sequentially", name="load_button_2")
        self.smmc = sppasMMPCtrl(parent=self)
        self.smmc.SetMinSize(wx.Size(640, 120))

        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(button1, 0, wx.ALL, 8)
        s.Add(button2, 0, wx.ALL, 8)
        s.Add(self.smmc, 1, wx.EXPAND)
        self.SetSizer(s)

        button1.Bind(wx.EVT_BUTTON, self._on_load_1)
        button2.Bind(wx.EVT_BUTTON, self._on_load_2)
        self.FindWindow("media_play").Enable(False)

    # ----------------------------------------------------------------------

    def _on_load_1(self, event):
        self.load_files(with_threads=True)

    # ----------------------------------------------------------------------

    def _on_load_2(self, event):
        self.load_files(with_threads=False)

    # ----------------------------------------------------------------------

    def load_files(self, with_threads=True):
        self.FindWindow("load_button_1").Enable(False)
        self.FindWindow("load_button_2").Enable(False)

        # Loading the videos with threads make the app crashing under MacOS:
        # Python[31492:1498940] *** Terminating app due to uncaught exception
        # 'NSInternalInconsistencyException', reason: 'NSWindow drag regions
        # should only be invalidated on the Main Thread!'
        player = VideoAnnotationFrame(
            parent=self,  # if parent is destroyed, the frame will be too
            title="Video",
            style=wx.CAPTION | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX | wx.DIALOG_NO_PARENT)

        self.smmc.add_unsupported("a filename of a file", 65.)

        # To load files in parallel, with threads:
        if with_threads is True:
            self.smmc.add_audio(
                [os.path.join(paths.samples, "samples-fra", "F_F_B003_P8.wav"),
                 # os.path.join(paths.samples, "samples-fra", "F_F_B003_P9.wav"),
                 os.path.join(paths.samples, "samples-eng", "oriana1.wav"),
                 os.path.join(paths.samples, "samples-eng", "oriana2.WAV"),
                 ])
        else:
            # To load files sequentially, without threads:
            self.smmc.add_audio(os.path.join(paths.samples, "samples-fra", "F_F_B003_P8.wav"))
            # self.smmc.add_audio(os.path.join(paths.samples, "samples-fra", "F_F_B003_P9.wav"))
            self.smmc.add_audio(os.path.join(paths.samples, "samples-eng", "oriana1.wav"))
            self.smmc.add_audio(os.path.join(paths.samples, "samples-eng", "oriana2.WAV"))

        self.smmc.add_video([os.path.join(paths.samples, "faces", "video_sample.mp4")], player)

        while self.smmc.is_loading() is True:
            pass

        self.smmc.set_visible_range(1., 7.)
        self.smmc.set_selection_range(2., 4.)
