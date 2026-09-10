# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.wxapp.page_editor.timeline.baseview_risepanel.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  A base class for any object displaying the content of a file in a timeline.

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

"""

import wx
import os
import random

from sppas.core.config import paths
from sppas.core.coreutils import info  # todo: add tooltip in po with info index
from sppas.core.coreutils import msg

from sppas.ui.wxapp.windows.panels import sppasPanel
from sppas.ui.wxapp.windows.panels import sppasBaseRisePanel
from sppas.ui.wxapp.windows.buttons import BitmapButton
from sppas.ui.wxapp.windows.buttons import ToggleButton
from sppas.ui.wxapp.windows.popup import PopupLabel

from .timedatatype import TimelineType
from .timeevents import TimelineViewEvent
from .timeevents import EVT_TIMELINE_VIEW

# ---------------------------------------------------------------------------


TOOLTIP_LABEL = info(9701, "ui")
TOOLTIP_ZOOM_UP = info(9411, "ui")
TOOLTIP_ZOOM_DOWN = info(9421, "ui")
TOOLTIP_CLOSE = msg("Close", "ui")

# ---------------------------------------------------------------------------


class sppasFileViewPanel(sppasBaseRisePanel):
    """A vert- oriented rise panel with an horiz- toolbar when collapsed.

    The expected content is a file, displaying its content on a given
    period of time.

    """

    # -----------------------------------------------------------------------
    # List of accepted percentages of zooming when zooming up or down.
    # Must be sorted from the minimum to the maximum.
    ZOOMS = (25, 50, 75, 100, 125, 150, 200, 250, 300, 400)
    DEFAULT_ZOOM = ZOOMS[3]
    # -----------------------------------------------------------------------

    def __init__(self, parent, id=wx.ID_ANY, label="", pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0, name="collapsible_panel",
                 filename=None):
        """Create a sppasFileViewPanel to display a file in a rise panel.

        :param parent: (wx.Window) Parent window must NOT be none
        :param id: (int) window identifier or -1
        :param label: (string) Label of the button
        :param pos: (wx.Pos) the control position
        :param size: (wx.Size) the control size
        :param style: (int) the underlying window style
        :param name: (str) the widget name.
        :param filename: (str) the name of the file of this panel.

        The parent can Bind:

            - wx.EVT_COLLAPSIBLEPANE_CHANGED.
            - EVT_TIMELINE_VIEW with action is one of: close, zoom_up, zoom_down

        """
        self._collapsed_tools_panel = None
        self.__label_popup = None
        super(sppasFileViewPanel, self).__init__(
            parent, id, label, pos, size, style, name=name)

        # Members
        self._ft = TimelineType().unknown
        self._dirty = False
        self._filename = filename

        # Default background color ranges
        self._rgb1 = (150, 150, 150)
        self._rgb2 = (220, 220, 220)

        # Create a toolbar and show it only when collapsed.
        self._collapsed_tools_panel = sppasPanel(self)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._collapsed_tools_panel.SetSizer(sizer)
        self._collapsed_tools_panel.Show(False)

        # Add 4 buttons to this toolbar
        label_btn = self._create_tool_button("slashdot")
        label_btn.SetToolTip(TOOLTIP_LABEL)
        zoomup_btn = self._create_tool_button("zoom_up")
        zoomup_btn.SetToolTip(TOOLTIP_ZOOM_UP)
        zoomdown_btn = self._create_tool_button("zoom_down")
        zoomdown_btn.SetToolTip(TOOLTIP_ZOOM_DOWN)
        close_btn = self._create_tool_button("close")
        close_btn.SetToolTip(TOOLTIP_CLOSE)
        sizer.Add(label_btn, 0, wx.FIXED_MINSIZE | wx.TOP, 1)
        sizer.Add(zoomup_btn, 0, wx.FIXED_MINSIZE | wx.TOP, 1)
        sizer.Add(zoomdown_btn, 0, wx.FIXED_MINSIZE | wx.TOP, 1)
        sizer.Add(close_btn, 0, wx.FIXED_MINSIZE | wx.TOP, 1)

        # Bind events of these buttons
        close_btn.Bind(wx.EVT_BUTTON, self._process_close_event)
        label_btn.Bind(wx.EVT_BUTTON, self._process_label_event)
        zoomup_btn.Bind(wx.EVT_BUTTON, self._process_zoom_event)
        zoomdown_btn.Bind(wx.EVT_BUTTON, self._process_zoom_event)

        # To be overriden: create the GUI & setup events
        try:
            self._create_content()
            self._setup_events()
        except NotImplementedError:
            pass

        try:
            settings = wx.GetApp().settings
            self._zoom = settings.editor_timeline_zoom
            self.GetPane().set_zoom(self._zoom)
        except AttributeError:
            self._zoom = sppasFileViewPanel.DEFAULT_ZOOM

        # Apply the SPPAS font but not its colours
        try:
            self.SetRandomColours()
            settings = wx.GetApp().settings
            self.SetFont(settings.text_font)
        except AttributeError:
            self.InheritAttributes()

        self.Layout()

    # ------------------------------------------------------------------------
    # About the file
    # ------------------------------------------------------------------------

    def is_unknown(self):
        return self._ft == TimelineType().unknown

    def is_audio(self):
        return self._ft == TimelineType().audio

    def is_video(self):
        return self._ft == TimelineType().video

    def is_trs(self):
        return self._ft == TimelineType().trs

    def is_image(self):
        return self._ft == TimelineType().image

    # ------------------------------------------------------------------------

    def get_filename(self):
        """Return the filename this panel is displaying."""
        return self._filename

    # ------------------------------------------------------------------------

    def set_filename(self, name):
        """Set a new name to the file.

        :param name: (str) Name of a file. It is not verified.

        """
        self._filename = name
        self.SetLabel(name)
        self._dirty = True

        # The popup is showing the previous name: it can't be shown again.
        if self.__label_popup is not None and bool(self.__label_popup) is True:
            self.__label_popup.Destroy()
        self.__label_popup = None

    # ------------------------------------------------------------------------

    def is_modified(self):
        """Return True if the content of the file has changed."""
        return self._dirty

    # -----------------------------------------------------------------------
    # Visible part
    # -----------------------------------------------------------------------

    def set_visible_period(self, start, end):
        """Fix the period of time to display (seconds).

        :param start: (int)
        :param end: (int) Time in seconds

        """
        try:
            self.GetPane().set_visible_period(start, end)
        except AttributeError:
            pass

    # -----------------------------------------------------------------------

    def set_selection_period(self, start, end):
        """Fix a period of time to highlight (seconds).

        :param start: (int)
        :param end: (int) Time in seconds

        """
        try:
            self.GetPane().set_selection_period(start, end)
        except AttributeError:
            pass

    # -----------------------------------------------------------------------
    # Methods to extend UI possibilities of this panel
    # -----------------------------------------------------------------------

    def GetZoomLevel(self) -> int:
        """Return the current zoom percentage value."""
        return self._zoom

    # -----------------------------------------------------------------------

    def Zoom(self, value: int) -> None:
        """Set the zoom percentage value and apply it to the panel.

        This value is applied to the min size of the child panel.

        :param value: (int) Percentage of zooming, in range 25 .. 400.

        """
        value = int(value)
        if value < 25:
            value = 25
        if value > 400:
            value = 400
        self._zoom = value
        try:
            self.GetPane().set_zoom(value)
        except AttributeError:
            pass

        # Adapt our size to the new content size and the parent updates its layout
        self.Freeze()
        self.InvalidateBestSize()
        self.Thaw()
        best_size = self.GetBestSize()
        self.SetStateChange(best_size)

    # -----------------------------------------------------------------------

    def ZoomUp(self) -> None:
        """Increase the zoom percentage value and apply it to the panel. """
        if self._zoom in sppasFileViewPanel.ZOOMS:
            next_cur_zoom_idx = self.ZOOMS.index(self._zoom) + 1
        else:
            # a custom zoom value is in use. Find the next higher one.
            next_cur_zoom_idx = 0
            while next_cur_zoom_idx < len(sppasFileViewPanel.ZOOMS):
                if sppasFileViewPanel.ZOOMS[next_cur_zoom_idx] > self._zoom:
                    break
                next_cur_zoom_idx += 1

        if next_cur_zoom_idx < len(self.ZOOMS):
            self._zoom = sppasFileViewPanel.ZOOMS[next_cur_zoom_idx]

        # Apply the zoom value.
        self.Zoom(self._zoom)

    # -----------------------------------------------------------------------

    def ZoomDown(self) -> None:
        """Decrease the zoom percentage value and apply it to the panel. """
        if self._zoom in sppasFileViewPanel.ZOOMS:
            prev_cur_zoom_idx = self.ZOOMS.index(self._zoom) - 1
        else:
            # a custom zoom value is in use. Find the next lower one.
            prev_cur_zoom_idx = len(sppasFileViewPanel.ZOOMS) - 1
            while prev_cur_zoom_idx >= 0:
                if sppasFileViewPanel.ZOOMS[prev_cur_zoom_idx] < self._zoom:
                    break
                prev_cur_zoom_idx -= 1

        # The index is -1 if the minimum of the zooms is already applied.
        if prev_cur_zoom_idx >= 0:
            self._zoom = self.ZOOMS[prev_cur_zoom_idx]

        # Apply the zoom value.
        self.Zoom(self._zoom)

    # -----------------------------------------------------------------------

    def EnableButton(self, icon, value):
        """Enable or disable a button of the tools panel.

        :param icon: (str) Name of the .png file of the icon
        :param value: (bool)

        """
        btn = self._collapsed_tools_panel.FindWindow(icon)
        if btn is None or btn == self._btn:
            return
        btn.Enable(value)

    # -----------------------------------------------------------------------

    def FindButton(self, icon):
        """Return the button with the given icon name or None."""
        for child in self._collapsed_tools_panel.GetChildren():
            if child.GetName() == icon and child != self._btn:
                return child
        return None

    # -----------------------------------------------------------------------

    def AddButton(self, icon, index=0):
        """Append a button into the toolbar.

        :param icon: (str) Name of the .png file of the icon or None
        :param index: (int) Index of the button

        """
        btn = self._create_tool_button(icon, label=None)
        self._collapsed_tools_panel.GetSizer().Insert(index, btn, 0, wx.TOP, 1)

        return btn

    # -----------------------------------------------------------------------

    def GetButtonWidth(self):
        """Return the width of the buttons in the toolbar."""
        return int(float(self.get_font_height()) * 1.8)

    # -----------------------------------------------------------------------

    def SetBackgroundColour(self, colour):
        """Override. Do not set background color."""
        pass

    def SetForegroundColour(self, colour):
        """Override. Do not set foreground color."""
        pass

    # -----------------------------------------------------------------------

    def SetRandomColours(self):
        """Set background and foreground colors from our range of rgb colors."""
        # Fix the color of the background
        r, g, b = self.PickRandomBackgroundColour()
        color = wx.Colour(r, g, b)

        if (r + g + b) > 384:
            hi_color = color.ChangeLightness(90)
        else:
            hi_color = color.ChangeLightness(110)

        # Set the colors to the panel itself and to its children
        wx.Panel.SetBackgroundColour(self, color)
        self._child_panel.SetBackgroundColour(color)
        self._tools_panel.SetBackgroundColour(hi_color)
        self._collapsed_tools_panel.SetBackgroundColour(hi_color)

        min_i = min(self._rgb1 + self._rgb2 + (196,))
        fg = wx.Colour(r - min_i, g - min_i, b - min_i)
        self._child_panel.SetForegroundColour(fg)
        self._tools_panel.SetForegroundColour(fg)
        self._collapsed_tools_panel.SetForegroundColour(fg)

    # ------------------------------------------------------------------------

    def PickRandomBackgroundColour(self):
        """Return a tuple of (r,g,b) values."""
        r = random.randint(min(self._rgb1[0], self._rgb2[0]), max(self._rgb1[0], self._rgb2[0]))
        g = random.randint(min(self._rgb1[1], self._rgb2[1]), max(self._rgb1[1], self._rgb2[1]))
        b = random.randint(min(self._rgb1[2], self._rgb2[2]), max(self._rgb1[2], self._rgb2[2]))

        return r, g, b

    # -----------------------------------------------------------------------

    def SetInitialSize(self, size=None):
        """Calculate and set a good size.

        :param size: an instance of wx.Size.

        """
        tb_w, tb_h = self._tools_panel.GetMinSize()
        min_w = tb_w
        min_h = tb_h
        self.SetMinSize(wx.Size(min_w, min_h))

        if size is None:
            size = wx.DefaultSize
        wx.Window.SetInitialSize(self, size)

    SetBestSize = SetInitialSize

    # -----------------------------------------------------------------------

    def DoGetBestSize(self):
        """Get the size which best suits the window."""
        if self.IsExpanded() is True:
            tb_w, tb_h = self._tools_panel.DoGetBestSize()
        else:
            tb_w, tb_h = self._tools_panel.GetMinSize()

        best_w = tb_w
        best_h = tb_h

        if self.IsExpanded() and self._child_panel:
            child_w, child_h = self._child_panel.GetBestSize()
            best_w = tb_w + child_w
            best_h = max(child_h, tb_h)

        return wx.Size(best_w, best_h)

    # -----------------------------------------------------------------------

    def Layout(self):
        """Do the layout."""
        # we need to complete the creation first
        if not self._tools_panel or not self._child_panel:
            return False

        w, h = self.GetClientSize()
        tw = self.GetButtonWidth()
        th = self.GetButtonWidth()
        sizer = self._tools_panel.GetSizer()

        if self.IsExpanded():
            th *= sizer.GetItemCount()
            th = max(h, th)
            # fix pos and size of the child window
            x = tw
            y = 0
            pw = w - x
            ph = th - y

            self._child_panel.SetSize(wx.Size(pw, ph))
            self._child_panel.SetPosition((x, y))
            self._child_panel.Show(True)
            self._child_panel.Layout()
            if self._collapsed_tools_panel is not None:
                self._collapsed_tools_panel.Show(False)
        else:
            # fix pos and size of the child window
            x = tw
            y = 0
            pw = w - x

            self._child_panel.Show(False)
            if self._collapsed_tools_panel is not None:
                self._collapsed_tools_panel.SetSize(wx.Size(pw, th))
                self._collapsed_tools_panel.SetPosition((x, y))
                self._collapsed_tools_panel.Show(True)

        # fix pos and size of the left panel with tools
        self._tools_panel.SetPosition((0, 0))
        self._tools_panel.SetSize(wx.Size(tw, th))
        self._tools_panel.SetMinSize(wx.Size(tw, th))

        return True

    # -----------------------------------------------------------------------
    # Construct the GUI
    # -----------------------------------------------------------------------

    def _create_content(self):
        """Create the content of the panel."""
        raise NotImplementedError

    # -----------------------------------------------------------------------

    def _create_toolbar(self):
        """Create a panel with only the collapsible button."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        self._btn = self._create_collapsible_button()
        sizer.Add(self._btn, 0, wx.FIXED_MINSIZE, 0)
        self._tools_panel.SetSizer(sizer)
        w = self.GetButtonWidth()
        self._tools_panel.SetMinSize(wx.Size(w, w*2))

    # -----------------------------------------------------------------------

    def _create_collapsible_button(self):
        img_name = self._img_expanded
        if self.IsCollapsed():
            img_name = self._img_collapsed
        btn = BitmapButton(self._tools_panel, name=img_name)
        btn.SetAlign(wx.ALIGN_CENTER)
        btn.SetFocusWidth(0)
        btn.SetSpacing(0)
        btn.SetBorderWidth(0)
        btn_w = self.GetButtonWidth()
        btn.SetSize(wx.Size(btn_w, btn_w))
        btn.SetMinSize(wx.Size(btn_w, btn_w))
        return btn

    # -----------------------------------------------------------------------

    def _create_tool_button(self, icon, label=None):
        btn = BitmapButton(self._collapsed_tools_panel, name=icon)
        btn.SetAlign(wx.ALIGN_CENTER)
        btn.SetFocusWidth(0)
        btn.SetSpacing(0)
        btn.SetBorderWidth(0)
        btn_w = self.GetButtonWidth()
        btn.SetSize(wx.Size(btn_w, btn_w))
        btn.SetMinSize(wx.Size(btn_w, btn_w))
        return btn

    # -----------------------------------------------------------------------

    def _create_tool_togglebutton(self, icon, label=None):
        btn = ToggleButton(self._collapsed_tools_panel, name=icon)
        btn.SetAlign(wx.ALIGN_CENTER)
        btn.SetFocusWidth(0)
        btn.SetSpacing(0)
        btn.SetBorderWidth(0)
        btn_h = self.GetButtonWidth()
        btn.SetSize(wx.Size(btn_h, btn_h))
        btn.SetMinSize(wx.Size(btn_h, btn_h))
        return btn

    # -----------------------------------------------------------------------
    # Events management
    # -----------------------------------------------------------------------

    def update_ui(self):
        """Adapt our size to the new child size and the parent updates its layout."""
        self.Freeze()
        self.InvalidateBestSize()
        self.Thaw()
        best_size = self.GetBestSize()
        self.SetStateChange(best_size)

    # -----------------------------------------------------------------------

    def _setup_events(self):
        """Bind events for this panel."""
        pass

    # -----------------------------------------------------------------------

    def notify(self, action, value=None):
        """Notify the parent of a BaseViewEvent.

        The parent can catch the event with EVT_TIMELINE_VIEW.

        """
        evt = TimelineViewEvent(action=action, value=value)
        evt.SetEventObject(self)
        wx.PostEvent(self.GetParent(), evt)

    # -----------------------------------------------------------------------

    def _process_close_event(self, event):
        """Handle the wx.EVT_BUTTON event of the close button.

        :param event: (wx.Event)

        """
        obj = event.GetEventObject()
        name = obj.GetName()

        if name == "close":
            self.notify("close")

        else:  # we shouldn't be here
            event.Skip()

    # ------------------------------------------------------------------------

    def _process_label_event(self, event):
        """Handle the wx.EVT_BUTTON event of the label button.

        :param event: a CommandEvent event to be processed.

        """
        evt_obj = event.GetEventObject()
        if evt_obj.GetName() == "slashdot":
            # Creating a window is slow, so the popup is created once and it is
            # shown again at each click. It is destroying itself when it is
            # clicked in: in that case only, another one is created.
            if self.__label_popup is None or bool(self.__label_popup) is False:
                self.__label_popup = PopupLabel(
                    self.GetTopLevelParent(), wx.SIMPLE_BORDER, self._filename)

            # Show the "window" with the label
            win = self.__label_popup
            # Show the popup right below
            # depending on available screen space...
            pos = evt_obj.ClientToScreen((0, self.fix_size(self.get_font_height())))
            # the label popup will hide the button.
            win.Position(pos, (0, 0))
            # Popup() is arming the dismissal by a click outside of it, which
            # is hiding it. Show() is only showing it, so it could be closed
            # by a click inside only -- which is destroying it.
            win.Popup()

        else:  # we shouldn't be here
            event.Skip()

    # -----------------------------------------------------------------------

    def _process_zoom_event(self, event):
        """Handle the wx.EVT_BUTTON event of the zoom_up or zoom_down button.

        :param event: (wx.Event)

        """
        evt_obj = event.GetEventObject()
        evt_name = evt_obj.GetName()
        if evt_name in ("zoom_up", "zoom_down"):
            self.notify(evt_name)

        else:  # we shouldn't be here
            event.Skip()

# ---------------------------------------------------------------------------


class TestPanel(wx.Panel):

    FILENAME = os.path.join(paths.samples, "samples-fra", "F_F_B003_P8.wav")

    def __init__(self, parent):
        super(TestPanel, self).__init__(parent, name="Base FileViewPanel")
        s = wx.BoxSizer(wx.VERTICAL)
        p1 = self._create_panel("p1")
        p2 = self._create_panel("p2")
        s.Add(p1, 0, wx.EXPAND)
        s.Add(p2, 0, wx.EXPAND)
        self.SetSizer(s)

    def _create_panel(self, name="p1"):
        rise = sppasFileViewPanel(self, filename=TestPanel.FILENAME, name=name)
        panel = sppasPanel(rise)
        st = wx.StaticText(panel, -1, TestPanel.FILENAME, pos=(10, 100))
        sz = st.GetBestSize()
        panel.SetSize((sz.width + 20, sz.height + 20))
        rise.SetPane(panel)
        rise.Collapse(False)
        rise.Bind(EVT_TIMELINE_VIEW, self._process_timeview)
        return rise

    def _process_timeview(self, event):
        obj = event.GetEventObject()
        if event.action == "zoom_up":
            obj.ZoomUp()
        elif event.action == "zoom_down":
            obj.ZoomDown()
