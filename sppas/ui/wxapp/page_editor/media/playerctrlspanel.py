# -*- coding : UTF-8 -*-
"""
:filename: sppas.ui.wxapp.page_editor.media.playerctrlspanel.py
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

    Copyright (C) 2011-2023  Brigitte Bigi, CNRS
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

Some methods must be overridden to be able to play/pause/stop/...

Can play audio and video, based on our customs audioplayer/videoplayer.
Requires the following libraries:

 - sounddevice, installed by the audioplay feature;
 - opencv, installed by the videoplay feature.

"""

import wx
import logging

from sppas.core.coreutils import info
from sppas.ui.wxapp.windows.buttons import ToggleButton
from sppas.ui.wxapp.windows.buttons import BitmapTextButton, BitmapButton
from sppas.ui.wxapp.windows.panels import sppasPanel
from sppas.ui.wxapp.windows.slider import sppasEVT_SLIDER, SliderEvent

from .mediaevents import MediaEvents
from .timeslider import TimeSliderPanel

# ---------------------------------------------------------------------------


PLAY_TOOLTIP = info(9501, "ui")
PAUSE_TOOLTIP = info(9511, "ui")
STOP_TOOLTIP = info(9521, "ui")
REWIND_TOOLTIP = info(9531, "ui")
FORWARD_TOOLTIP = info(9541, "ui")
REPEAT_TOOLTIP = info(9551, "ui")

PLAY_PREV_FRAME_TOOLTIP = info(9601, "ui")
PLAY_NEXT_FRAME_TOOLTIP = info(9611, "ui")
PREVIOUS_FRAME_DIRECTION_VALUE_TOOLTIP = info(9621, "ui")
NEXT_FRAME_DIRECTION_VALUE_TOOLTIP = info(9631, "ui")

# ---------------------------------------------------------------------------


class TogglePause(ToggleButton):
    """A toggle button with a specific design and properties.

    """

    FG_COLOUR = wx.Colour(255, 106, 77)

    def __init__(self, parent,
                 id=wx.ID_ANY,
                 label="",
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize):
        """Default class constructor.

        :param parent: the parent (required);
        :param id: window identifier.
        :param label: label text of the check button;
        :param pos: the position;
        :param size: the size.

        The name of the button is "media_pause" by default; use SetName()
        to change it after creation.

        """
        super(TogglePause, self).__init__(parent, id, label, pos, size, "media_pause")
        self.Enable(False)
        self.SetValue(False)


# ---------------------------------------------------------------------------


class PressPlay(BitmapButton):
    """A bitmap button with a specific design and properties.

    """

    FG_COLOUR = wx.Colour(88, 118, 177)

    # -----------------------------------------------------------------------

    def __init__(self, parent,
                 id=wx.ID_ANY,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize):
        """Default class constructor.

        :param parent: the parent (required);
        :param id: window identifier.
        :param pos: the position;
        :param size: the size.

        The name of the button is "media_play" by default; use SetName()
        to change it after creation.

        """
        super(PressPlay, self).__init__(parent, id, pos, size, "media_play")
        self.Enable(False)

    # -----------------------------------------------------------------------

    def Enable(self, value=True):
        BitmapButton.Enable(self, value)
        if self.IsEnabled() is True:
            self.SetForegroundColour(PressPlay.FG_COLOUR)
        else:
            self.SetForegroundColour(self.GetParent().GetForegroundColour())


# ---------------------------------------------------------------------------


class sppasPlayerControlsPanel(sppasPanel):
    """Create a panel with controls to manage media.

    Three children are to be created and organized into a BoxSizer:
        - widgets_panel: a customizable panel, free to be used to add widgets
        - transport_panel: all buttons to play a media
        - slider_panel: a panel to indicate duration, selection, position...

    Any action of the user (click on a button, move a slider...) is sent to
    the parent by the event: EVT_MEDIA_ACTION.

    Any widget added to the widgets panel will send its own events.

    """

    def __init__(self,
                 parent: wx.Window,
                 id: int = wx.ID_ANY,
                 pos: wx.Position = wx.DefaultPosition,
                 size: wx.Size = wx.DefaultSize,
                 style: int = 0,
                 name: str = "player_controls_panel"):
        """Create a `sppasPlayerControlsPanel` instance.

        :param parent: (wx.Window) the parent window, which must not be None
        :param id: (int) the window identifier or `-1`
        :param pos: (wx.Position) the control position
        :param size: (wx.Size) the control size
        :param style: (int) the underlying window style
        :param name: (str) the widget name

        """
        super(sppasPlayerControlsPanel, self).__init__(parent, id, pos, size, style, name)

        self._btn_size = sppasPanel.fix_size(24)
        self._focus_color = wx.Colour(red=128, green=128, blue=128, alpha=128)
        self._create_content()
        self._setup_events()

        self.Layout()

    # -----------------------------------------------------------------------
    # Public methods, for the controls
    # -----------------------------------------------------------------------

    def SetFocusColour(self, colour: wx.Colour) -> None:
        self._focus_color = colour
        self.FindWindow("media_play").SetFocusColour(colour)
        self.FindWindow("media_pause").SetFocusColour(colour)
        self.FindWindow("media_play_next_frame").SetFocusColour(colour)
        self.FindWindow("media_play_prev_frame").SetFocusColour(colour)
        self.FindWindow("media_stop").SetFocusColour(colour)
        self.FindWindow("media_rewind").SetFocusColour(colour)
        self.FindWindow("media_forward").SetFocusColour(colour)
        self.FindWindow("media_repeat").SetFocusColour(colour)

    # -----------------------------------------------------------------------

    def AddLeftWidget(self, window: wx.Window) -> bool:
        """Add a widget into the customizable panel.

        :param window: (wx.Window) the window of the widget to add
        :return: True if added, False if parent does not match.

        """
        return self.__add_widget(self.widgets_left_panel, window)

    # -----------------------------------------------------------------------

    def AddRightWidget(self, window: wx.Window) -> bool:
        """Add a widget into the customizable panel.

        :param window: (wx.Window) the window of the widget to add
        :return: True if added, False if parent does not match.

        """
        return self.__add_widget(self.widgets_right_panel, window)

    # -----------------------------------------------------------------------

    @staticmethod
    def __add_widget(widget_panel: sppasPanel, window: wx.Window) -> bool:
        """Add a widget into a widget panel and show the panel.

        :param widget_panel: (sppasPanel) the widget panel
        :param window: (wx.Window) the window of the widget to add
        :return: True if added, False if parent does not match.

        """
        if window.GetParent() != widget_panel:
            return False
        widget_panel.GetSizer().Add(window=window,
                                    proportion=0,
                                    flag=wx.ALIGN_CENTER | wx.ALL,
                                    border=sppasPanel.fix_size(2))
        widget_panel.Show(True)
        return True

    # -----------------------------------------------------------------------

    def SetButtonWidth(self, value: int) -> None:
        """Fix the width/height of the buttons.

        The given value will be adjusted to a proportion of the font height.
        Min is 12, max is 128.
        The buttons are not refreshed.

        :param value: (int) the value to use

        """
        value = sppasPanel.fix_size(value)
        self._btn_size = min(value, sppasPanel.fix_size(128))
        self._btn_size = max(self._btn_size, sppasPanel.fix_size(12))

        for name in ("rewind", "forward"):
            btn = self.FindWindow("media_" + name)
            btn.SetMinSize(wx.Size(2 * self._btn_size // 3, self._btn_size))

        for name in ("pause", "stop", "repeat", "play_next_frame", "play_prev_frame"):
            btn = self.FindWindow("media_" + name)
            btn.SetMinSize(wx.Size(self._btn_size, self._btn_size))

        btn = self.FindWindow("media_play")
        btn.SetMinSize(wx.Size(5 * self._btn_size // 4, self._btn_size))

    # -----------------------------------------------------------------------

    def ShowSlider(self, value: bool = True) -> None:
        self._timeslider.Show(value)

    # -----------------------------------------------------------------------

    def ShowLeftWidgets(self, value: bool = True) -> None:
        self.widgets_left_panel.Show(value)

    # -----------------------------------------------------------------------

    def ShowRightWidgets(self, value: bool = True) -> None:
        self.widgets_right_panel.Show(value)

    # -----------------------------------------------------------------------

    def IsReplay(self) -> bool:
        """Return True if the button to replay is enabled."""
        return self._transport_panel.FindWindow("media_repeat").IsPressed()

    # -----------------------------------------------------------------------

    def EnableReplay(self, enable: bool = True) -> None:
        """Enable or disable the Replay button.

        The replay button should be disabled if several media of different
        durations have to be played...

        :param enable: (bool)

        """
        self._transport_panel.FindWindow("media_repeat").Enable(enable)

    # -----------------------------------------------------------------------

    def EnablePlay(self, enable: bool = True) -> None:
        """Enable or disable the Play button.

        :param enable: (bool)

        """
        self._transport_panel.FindWindow("media_play").Enable(enable)

    # -----------------------------------------------------------------------
    # Public methods, for the media. To be overridden.
    # -----------------------------------------------------------------------

    def play(self) -> None:
        """To be overridden. Start playing media."""
        self.notify(action="play", value=None)

    # -----------------------------------------------------------------------

    def pause(self) -> None:
        """To be overridden. Pause in playing media."""
        self.notify(action="pause", value=None)

    # -----------------------------------------------------------------------

    def play_frame(self, direction=1) -> None:
        """To be overridden. Play the next frame in playing media.

        Direction indicates which "next/previous" frame to play.

        :param direction: positive value = next; negative value = previous

        """
        self.notify(action="play_frame", value=direction)

    # -----------------------------------------------------------------------

    def stop(self) -> None:
        """To be overridden. Stop playing media."""
        self.notify(action="stop", value=None)

    # -----------------------------------------------------------------------

    def media_rewind(self) -> None:
        """To be overridden. Seek media to some time earlier."""
        self.notify(action="rewind", value=None)

    # -----------------------------------------------------------------------

    def media_forward(self) -> None:
        """To be overridden. Seek media to some time later."""
        self.notify(action="forward", value=None)

    # -----------------------------------------------------------------------

    def media_seek(self, value) -> None:
        """To be overridden. Seek media to the given time value."""
        self.notify(action="seek", value=value)

    # -----------------------------------------------------------------------

    def media_period(self, start, end) -> None:
        """To be overridden."""
        self.notify(action="period", value=(start, end))

    # -----------------------------------------------------------------------
    # Construct the GUI
    # -----------------------------------------------------------------------

    def SetButtonProperties(self, btn: BitmapTextButton) -> None:
        """Set the properties of a button.

        :param btn: (BitmapTextButton) a button on which setting the
        properties

        """
        btn.SetBackgroundColour(self.GetBackgroundColour())
        btn.SetFocusColour(self._focus_color)
        btn.SetFocusStyle(wx.PENSTYLE_SOLID)
        btn.SetFocusWidth(1)
        btn.SetSpacing(0)
        btn.SetMinSize(wx.Size(width=self._btn_size, height=self._btn_size))

    # -----------------------------------------------------------------------

    def _create_content(self) -> None:
        """Create the content of the panel."""
        nav_panel = sppasPanel(parent=self, name="nav_panel")
        panel1 = self.__create_widgets_left_panel(nav_panel)
        panel3 = self.__create_widgets_right_panel(nav_panel)
        panel2 = self.__create_transport_panel(nav_panel)

        nav_sizer = wx.BoxSizer(wx.HORIZONTAL)
        nav_sizer.Add(panel1, 1, wx.EXPAND | wx.RIGHT, sppasPanel.fix_size(2))
        nav_sizer.AddStretchSpacer(1)
        nav_sizer.Add(panel2, 1, wx.EXPAND)
        nav_sizer.AddStretchSpacer(1)
        nav_sizer.Add(panel3, 1, wx.EXPAND | wx.LEFT, sppasPanel.fix_size(2))
        nav_panel.SetSizerAndFit(nav_sizer)

        slider = TimeSliderPanel(self, name="slider_panel")

        # Under macOS and Linux, the scrollbar is transparent over a window, so
        # its size won't change if it appears or disappears. BUT, under Windows,
        # the scrollbar is drawn beside the window so its size (actually only
        # the width) is changed!!!! If we want that our slider is vertically
        # aligned with some other panels into a scrolled panel, we need to have
        # a border at right.
        border = 0
        if wx.Platform == "__WXMSW__":
            # get the width of a scrollbar
            s = wx.ScrollBar(self, style=wx.SB_VERTICAL)
            w, _ = s.GetSize()
            s.Destroy()
            # and use it for the border at right
            border = w

        # Organize the panels into the main sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(nav_panel, 0, wx.EXPAND | wx.RIGHT, border)
        sizer.Add(slider, 0, wx.EXPAND | wx.RIGHT, border)

        self.SetSizer(sizer)

    # -----------------------------------------------------------------------

    @property
    def _transport_panel(self):
        """Return the panel embedding buttons to manage the media."""
        return self.FindWindow("transport_panel")

    # -----------------------------------------------------------------------

    @property
    def _timeslider(self) -> TimeSliderPanel:
        """Return the slider to indicate offsets, duration, etc."""
        return self.FindWindow("slider_panel")

    # -----------------------------------------------------------------------

    @property
    def widgets_left_panel(self) -> sppasPanel:
        """Return the widgets left panel to be customized."""
        return self.FindWindow("widgets_left_panel")

    # -----------------------------------------------------------------------

    @property
    def widgets_right_panel(self) -> sppasPanel:
        """Return the widgets right panel to be customized."""
        return self.FindWindow("widgets_right_panel")

    # -----------------------------------------------------------------------

    @staticmethod
    def __create_widgets_left_panel(parent: wx.Window) -> sppasPanel:
        """Return an empty panel with a sizer."""
        panel = sppasPanel(parent=parent, name="widgets_left_panel")
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel.SetSizer(sizer)
        return panel

    # -----------------------------------------------------------------------

    @staticmethod
    def __create_widgets_right_panel(parent: wx.Window) -> sppasPanel:
        """Return an empty panel with a sizer."""
        panel = sppasPanel(parent=parent, name="widgets_right_panel")
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel.SetSizer(sizer)
        return panel

    # -----------------------------------------------------------------------

    def __create_transport_panel(self, parent: wx.Window) -> sppasPanel:
        """Return a panel with the buttons to control media playback.

        :param parent: (wx.Window) the parent window

        """
        play_frame_choices = [str(i) for i in range(1, 100)]

        panel = sppasPanel(parent=parent, name="transport_panel")

        btn_rewind = BitmapTextButton(parent=panel, name="media_rewind")
        btn_rewind.SetToolTip(REWIND_TOOLTIP)
        btn_rewind.SetName("media_rewind")
        self.SetButtonProperties(btn_rewind)
        btn_rewind.SetMinSize(wx.Size(width=self._btn_size // 2, height=self._btn_size))

        btn_play = PressPlay(parent=panel)
        btn_play.SetToolTip(PLAY_TOOLTIP)
        self.SetButtonProperties(btn_play)

        btn_pause = TogglePause(parent=panel)
        btn_pause.SetToolTip(PAUSE_TOOLTIP)
        self.SetButtonProperties(btn_pause)

        btn_forward = BitmapTextButton(parent=panel, name="media_forward")
        btn_forward.SetToolTip(FORWARD_TOOLTIP)
        btn_forward.SetName("media_forward")
        self.SetButtonProperties(btn_forward)
        btn_forward.SetMinSize(wx.Size(width=self._btn_size // 2, height=self._btn_size))

        btn_stop = BitmapTextButton(parent=panel, name="media_stop")
        btn_stop.SetToolTip(STOP_TOOLTIP)
        self.SetButtonProperties(btn_stop)
        btn_stop.SetFocus()

        btn_replay = ToggleButton(parent=panel, name="media_repeat")
        btn_replay.SetToolTip(REPEAT_TOOLTIP)
        self.SetButtonProperties(btn_replay)

        spinctrl_prev_play_frame = wx.ComboBox(parent=panel,
                                               size=wx.Size(width=75, height=-1),
                                               value="3",
                                               choices=play_frame_choices,
                                               name="previous_frame_direction_value")
        spinctrl_prev_play_frame.SetToolTip(PREVIOUS_FRAME_DIRECTION_VALUE_TOOLTIP)

        btn_play_prev_frame = BitmapTextButton(parent=panel, name="media_play_prev_frame")
        btn_play_prev_frame.SetToolTip(PLAY_PREV_FRAME_TOOLTIP)
        btn_play_prev_frame.SetName("media_play_prev_frame")
        self.SetButtonProperties(btn_play_prev_frame)
        btn_play_prev_frame.SetMinSize(wx.Size(width=self._btn_size, height=self._btn_size))

        btn_play_next_frame = BitmapTextButton(parent=panel, name="media_play_next_frame")
        btn_play_next_frame.SetToolTip(PLAY_NEXT_FRAME_TOOLTIP)
        btn_play_next_frame.SetName("media_play_next_frame")
        self.SetButtonProperties(btn_play_next_frame)
        btn_play_next_frame.SetMinSize(wx.Size(width=self._btn_size, height=self._btn_size))

        spinctrl_next_play_frame = wx.ComboBox(parent=panel,
                                               size=wx.Size(width=75, height=-1),
                                               value="5",
                                               choices=play_frame_choices,
                                               name="next_frame_direction_value")
        spinctrl_next_play_frame.SetToolTip(NEXT_FRAME_DIRECTION_VALUE_TOOLTIP)

        border = sppasPanel.fix_size(2)
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # suppress useless duplicate code warning
        # noinspection DuplicatedCode
        sizer.Add(window=btn_rewind, proportion=0, flag=wx.LEFT | wx.ALIGN_CENTER, border=border)
        sizer.Add(window=btn_play, proportion=0, flag=wx.LEFT | wx.ALIGN_CENTER, border=border)
        sizer.Add(window=btn_pause, proportion=0, flag=wx.LEFT | wx.ALIGN_CENTER, border=border)
        sizer.Add(window=btn_stop, proportion=0, flag=wx.LEFT | wx.ALIGN_CENTER, border=border)
        sizer.Add(window=btn_forward, proportion=0, flag=wx.LEFT | wx.ALIGN_CENTER, border=border)
        sizer.Add(window=btn_replay, proportion=0, flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER, border=border)

        sizer.Add(window=wx.Window(parent=panel,
                                   id=-1,
                                   size=wx.Size(width=sppasPanel.fix_size(10), height=-1)),
                  flag=wx.LEFT | wx.RIGHT,
                  border=border)
        sizer.Add(window=spinctrl_prev_play_frame,
                  proportion=0,
                  flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER,
                  border=border)

        # suppress useless duplicate code warning
        # noinspection DuplicatedCode
        sizer.Add(window=btn_play_prev_frame, proportion=0, flag=wx.RIGHT | wx.ALIGN_CENTER, border=border)
        sizer.Add(window=btn_play_next_frame, proportion=0, flag=wx.RIGHT | wx.ALIGN_CENTER, border=border)
        sizer.Add(window=spinctrl_next_play_frame, proportion=0, flag=wx.RIGHT | wx.ALIGN_CENTER, border=border)

        panel.SetSizer(sizer)

        return panel

    # -----------------------------------------------------------------------
    # Manage events
    # -----------------------------------------------------------------------

    def notify(self, action: str, value: any = None):
        """The parent has to be informed that an action is required.

        An action can be:
            - play/stop/rewind/forward, without value;
            - seek, the slider value (a percentage by default).

        :param action: (str) Name of the action to perform
        :param value: (any) Any kind of value linked to the action

        """
        wx.LogDebug("Send action event to parent {:s}".format(self.GetParent().GetName()))
        evt = MediaEvents.MediaActionEvent(action=action, value=value)
        evt.SetEventObject(self)
        wx.PostEvent(self.GetParent(), evt)

    # -----------------------------------------------------------------------

    def _setup_events(self) -> None:
        """Associate a handler function with the events.

        It means that when an event occurs then the process handler function
        will be called.

        """
        # The user clicked (LeftDown - LeftUp) an action button of the toolbar
        self.FindWindow("media_play").Bind(wx.EVT_BUTTON, self._process_action)
        self.FindWindow("media_stop").Bind(wx.EVT_BUTTON, self._process_action)
        self.FindWindow("media_rewind").Bind(wx.EVT_BUTTON, self._process_action)
        self.FindWindow("media_forward").Bind(wx.EVT_BUTTON, self._process_action)
        self.FindWindow("media_pause").Bind(wx.EVT_TOGGLEBUTTON, self._process_action)
        self.FindWindow("media_play_next_frame").Bind(wx.EVT_BUTTON, self._process_action)
        self.FindWindow("media_play_prev_frame").Bind(wx.EVT_BUTTON, self._process_action)

        # Event received when the period has changed
        self.Bind(MediaEvents.EVT_MEDIA_PERIOD, self._process_period_changed)
        self.Bind(sppasEVT_SLIDER, self._process_slider_action)

    # -----------------------------------------------------------------------

    def _process_action(self, event: wx.Event) -> None:
        """Process a button event: an action has to be performed.

        :param event: (wx.Event)

        """
        obj = event.GetEventObject()
        name = obj.GetName()
        # wx.LogDebug("Action to perform: {}".format(name.replace("media_", "")))

        if name == "media_play":
            self.play()

        elif name == "media_pause":
            self.pause()

        elif name == "media_play_prev_frame":
            try:
                value = int(self._transport_panel.FindWindow("previous_frame_direction_value").GetValue())
            except Exception as e:
                logging.error(str(e))
            else:
                self.play_frame(direction=-value)

        elif name == "media_play_next_frame":
            try:
                value = int(self._transport_panel.FindWindow("next_frame_direction_value").GetValue())
            except Exception as e:
                logging.error(str(e))
            else:
                self.play_frame(direction=value)

        elif name == "media_stop":
            self.stop()

        elif name == "media_rewind":
            self.media_rewind()

        elif name == "media_forward":
            self.media_forward()

        else:
            event.Skip()

    # ----------------------------------------------------------------------

    def _process_period_changed(self, event: MediaEvents.MediaPeriodEvent) -> None:
        """Handle the event of a change of time range in the slider."""
        p = event.period
        self.media_period(p[0], p[1])

    # -----------------------------------------------------------------------

    def _process_slider_action(self, event: SliderEvent) -> None:
        """Process a button event: an action has to be performed.

        :param event: (wx.Event)

        """
        if event.action in ("scroll", "zoom"):
            s, e = event.value
            self.media_period(s, e)
        else:
            event.Skip()


# ---------------------------------------------------------------------------


class TestPanel(sppasPanel):

    def __init__(self, parent: wx.Window):
        super(TestPanel, self).__init__(parent=parent, name="PlayControls Panel")

        panel = sppasPlayerControlsPanel(self)
        panel.SetMinSize(wx.Size(width=640, height=120))
        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(window=panel, proportion=1, flag=wx.EXPAND)
        self.SetSizer(s)
