# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.wxapp.windows.slider.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: a self-drawn slider, not built on native controls.

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

"""

import logging
import wx
import wx.lib.newevent
import os

from sppas.core.config import paths

from .basedcwindow import sppasImageDCWindow

# ---------------------------------------------------------------------------


SliderEvent, sppasEVT_SLIDER = wx.lib.newevent.NewEvent()
SliderCommandEvent, sppasEVT_SLIDER_COMMAND = wx.lib.newevent.NewCommandEvent()

# ---------------------------------------------------------------------------


class sppasSlider(sppasImageDCWindow):
    """A window imitating a slider but with the same look on all platforms.

    """

    POINT_COLOUR1 = wx.Colour(10, 60, 190)
    POINT_COLOUR2 = wx.Colour(40, 90, 220)
    POINT_COLOUR3 = wx.Colour(75, 125, 255)

    # -----------------------------------------------------------------------

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.NO_FULL_REPAINT_ON_RESIZE | wx.BORDER_NONE,
                 name="slider_panel"):
        """Create a self-drawn window to display a value into a range.

        """
        super(sppasSlider, self).__init__(parent, id, pos=pos, size=size, style=style, name=name)

        self._start = 0
        self._end = 0
        self.__pos = 0
        self._vert_border_width = 0
        self._horiz_border_width = 1
        self._min_width = 48
        self._show_startend = False

        # Members indicating the current state
        self._drag = None
        self._drag_range = None
        self._key = False
        self._allow_changes = True

        # Handling mouse&keys.
        self.Bind(wx.EVT_MOUSE_EVENTS, self.onMouseEvents)

    # -----------------------------------------------------------------------

    def set_allows_changes(self, value: bool = True):
        """Allows to change the range and notify parent."""
        self._allow_changes = value

    # -----------------------------------------------------------------------

    def get_range(self):
        """Return the (start, end) values."""
        return self._start, self._end

    # -----------------------------------------------------------------------

    def set_range(self, start: float, end: float):
        """Fix the range of values the slider is considering.

        Do not refresh.

        :param start: (float)
        :param end: (float)
        :return: (float) current position: either the current one, start or end.

        """
        start = float(start)
        end = float(end)
        if start > end:
            raise ValueError("Start {} can't be greater then end {}".format(start, end))
        self._start = start
        self._end = end

    # -----------------------------------------------------------------------

    def get_value(self):
        """Return the current position value."""
        return self.__pos

    # -----------------------------------------------------------------------

    def set_value(self, pos: float):
        """Fix the current position value.

        Do not refresh.

        :param pos: (float) A position in the current range.
        :return: (float) current position: either the given one, start or end.

        """
        pos = float(pos)
        self.__pos = pos

        if self.__pos < self._start:
            self.__pos = self._start
        if self.__pos > self._end:
            self.__pos = self._end
        return self.__pos

    # -----------------------------------------------------------------------

    def show_startend(self, value: bool = True):
        """Show/Hide start and end values.

        :param value: (bool)

        """
        self._show_startend = bool(value)

    # -----------------------------------------------------------------------

    @staticmethod
    def formats_label(value):
        return str(value)

    # -----------------------------------------------------------------------

    def Notify(self, action, value):
        """Send event to parent requesting for a new range."""
        evt = SliderEvent(action=action, value=value)
        evt.SetEventObject(self)
        wx.PostEvent(self.GetParent(), evt)

    # -----------------------------------------------------------------------
    # Draw
    # -----------------------------------------------------------------------

    def DrawContent(self, dc, gc):
        """Override."""
        self._DrawLabels(dc, gc)
        self._DrawMoment(dc, gc)

    # -----------------------------------------------------------------------

    def _DrawLabels(self, dc, gc):
        """Draw left-right values."""
        if self._show_startend is True:
            x, y, w, h = self.GetContentRect()

            # Start label
            label = self.formats_label(self._start)
            tw, th = self.get_text_extend(dc, gc, label)
            self.DrawLabel(label, dc, gc, 2, (h - th) // 2)

            # End label
            label = self.formats_label(self._end)
            tw, th = self.get_text_extend(dc, gc, label)
            self.DrawLabel(label, dc, gc, w - tw - 2, (h - th) // 2)

    # -----------------------------------------------------------------------

    def _DrawMoment(self, dc, gc):
        """Draw a vertical line to indicate the current position."""
        x, y, w, h = self.GetContentRect()

        # Draw the value of the current position at left or at right
        pos_x = 0
        total_dur = self._end - self._start
        pos_dur = self.__pos - self._start
        if total_dur > 0.:
            ratio = pos_dur / total_dur
            pos_x = int(w * ratio)

        # Vertical line indicating the proportional position
        if total_dur > 0.:
            pen = wx.Pen(sppasSlider.POINT_COLOUR3, 1, wx.PENSTYLE_SOLID)
            dc.SetPen(pen)
            gc.SetPen(pen)
            dc.DrawLine(pos_x, y, pos_x, y+h)
            pen = wx.Pen(sppasSlider.POINT_COLOUR2, 1, wx.PENSTYLE_SOLID)
            dc.SetPen(pen)
            gc.SetPen(pen)
            dc.DrawLine(pos_x+1, y, pos_x+1, y+h)
            dc.DrawLine(pos_x-1, y, pos_x-1, y+h)
            pen = wx.Pen(sppasSlider.POINT_COLOUR1, 1, wx.PENSTYLE_SOLID)
            dc.SetPen(pen)
            gc.SetPen(pen)
            dc.DrawLine(pos_x+2, y, pos_x+2, y+h)
            dc.DrawLine(pos_x-2, y, pos_x-2, y+h)

    # ------------------------------------------------------------------------

    def onMouseEvents(self, event):
        """Event handler used when the mouse is operated."""
        if event.Entering():
            pass

        elif event.Leaving():
            pass

        elif event.LeftDown():
            if self._allow_changes is True:
                self.onMouseLeftDown(event)

        elif event.LeftUp():
            if self._allow_changes is True:
                self.onMouseLeftUp(event)

        elif event.Moving():
            # moving without a button pressed
            self.onMouseMotion(event)

        elif event.Dragging():
            if self._allow_changes is True:
                if event.ControlDown():   # CTRL, or CMD on MacOS
                    # moving while a key is pressed = Zoom
                    self._key = True
                self.onMouseDragging(event)

        elif event.GetWheelRotation() > 0:
            pass

        elif event.GetWheelRotation() < 0:
            pass

        event.Skip()

    # ------------------------------------------------------------------------

    def onMouseMotion(self, event):
        """Respond to mouse motion event."""
        if self._drag is None:
            self.Notify(action="mouse_time", value=self.x2time(event.X))

    # ------------------------------------------------------------------------

    def onMouseLeftDown(self, event):
        """Respond to mouse left down event."""
        self._drag = wx.Point(event.X, event.Y)
        self._drag_range = (self._start, self._end)

    # ------------------------------------------------------------------------
    def x2time(self, x):
        _, _, w, _ = self.GetContentRect()
        d = self._end - self._start
        return x * d / w

    # ------------------------------------------------------------------------

    def onMouseLeftUp(self, event):
        """Respond to mouse left up. """
        (_x, _y) = wx.Point(event.X, event.Y)
        if self._drag is not None:
            _, _, w, h = self.GetContentRect()
            distance = self._drag.x - _x
            coeff = float(distance) / float(w)
            # Scroll or Zoom proportionally to the mouse dragged distance.
            if self._key is True:
                action = "zoom"
                self.__Zoom(coeff)
            else:
                action = "scroll"
                self.__Scroll(coeff)
            # The gesture is finished. Request the range the slider is showing,
            # whatever the way it was reached during the drag.
            if self._drag_range != (self._start, self._end):
                self.Notify(action=action, value=(self._start, self._end))

        self._drag = None
        self._drag_range = None
        self._key = False

    # ------------------------------------------------------------------------

    def onMouseDragging(self, event):
        """Respond to dragging mouse event."""
        if self._drag is not None:
            _, _, w, h = self.GetContentRect()
            (_x, _y) = wx.Point(event.GetX(), event.GetY())
            distance = self._drag.x - _x
            coeff = float(distance) / float(w)
            # update the period. Scroll proportionally to the mouse dragged distance.
            if abs(distance) > 10:
                if self._key is True:
                    self.__Zoom(coeff)
                else:
                    self.__Scroll(coeff)
                self._drag = wx.Point(event.GetX(), event.GetY())

    # -----------------------------------------------------------------------

    def __Scroll(self, coeff: float):
        """Scroll proportionally the displayed range. Do not notify the parent.

        :param coeff: (float) any value except 0.

        """
        if coeff == 0.:
            return
        duration = self._end - self._start
        scroll_duration = coeff * duration
        start = self._start + scroll_duration
        end = self._end + scroll_duration
        self.set_range(start, end)
        self.Refresh()

    # -----------------------------------------------------------------------

    def __Zoom(self, coeff: float):
        """Zoom proportionally the displayed range. Do not notify the parent.

        :param coeff: (float) any value except 0.

        """
        if coeff == 0.:
            return
        duration = self._end - self._start
        zoom_duration = (coeff * duration) / 2.
        start = self._start + zoom_duration
        end = self._end - zoom_duration
        self.set_range(start, end)
        self.Refresh()

# ----------------------------------------------------------------------------
# Panel for tests
# ----------------------------------------------------------------------------


class TestPanel(wx.Panel):

    img = os.path.join(paths.images, "bg1.png")

    def __init__(self, parent):
        super(TestPanel, self).__init__(
            parent,
            name="Test Slider")

        s1 = sppasSlider(self, pos=(0, 0), size=wx.Size(120, 20), name="s1")

        s2 = sppasSlider(self, pos=(0, 50), size=wx.Size(120, 20), name="s2")
        s2.SetForegroundColour(wx.Colour(208, 200, 166))
        s2.SetBackgroundImage(TestPanel.img)
        s2.set_range(0, 10)
        s2.set_value(6)
        s2.show_startend(True)

        s3 = sppasSlider(self, style=wx.NO_FULL_REPAINT_ON_RESIZE | wx.BORDER_SIMPLE, name="s3")
        s3.set_range(0, 3245)
        s3.set_value(4567)

        s4 = sppasSlider(self, name="s4")
        s4.set_range(0, 345)
        s4.set_value(56)
        s4.show_startend(True)
        s4.set_allows_changes(False)

        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(s1, 0, wx.EXPAND)
        s.Add(s2, 0, wx.EXPAND)
        s.Add(s3, 1, wx.EXPAND)
        s.Add(s4, 1, wx.EXPAND)
        self.SetSizer(s)

        self.Bind(sppasEVT_SLIDER, self.onSlider)

    def onSlider(self, event):
        # Which slider?
        slider = event.GetEventObject()
        logging.info("{} {} {}".format(slider.GetName(), event.action, event.value))
