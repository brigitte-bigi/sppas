# -*- coding : UTF-8 -*-
"""
:filename: sppas.ui.wxapp.page_editor.media.ticksslider.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  A custom slider.

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

    Copyright (C) 2011-2021  Brigitte Bigi, CNRS
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
import math

from sppas.ui.wxapp.windows.slider import sppasEVT_SLIDER
from sppas.ui.wxapp.windows.slider import sppasSlider

from ..datactrls.filmctrl import FRAME_FILL_COLOUR

# ----------------------------------------------------------------------------


class TicksLabel:
    """Label holds information about a particular tick in sppasTicksSlider.

    """

    def __init__(self, pos=-1, lx=-1, ly=-1, text=""):
        self.pos = pos
        self.lx = lx
        self.ly = ly
        self.text = text

# ----------------------------------------------------------------------------


class sppasTicksSlider(sppasSlider):


    def __init__(self, *args, **kwargs):
        """Create a self-drawn window to display a value into a range.

        """
        super(sppasTicksSlider, self).__init__(*args, **kwargs)
        self.SetMinSize(wx.Size(-1, 24))
        self._vert_border_width = 0
        self._horiz_border_width = 1

        # Internal values, used to estimate position of ticks and labels
        self._tick_height = 4  # is estimated when drawing
        self._digits = 0
        self._minor = 0
        self._major = 0
        self._max_width = 0
        self._max_height = 0
        self._bits = list()
        self._middlepos = list()
        self._indicators = dict()  # key = time value, value = wx.Colour()
        self._startend = False
        self.__show_labels = True
        self.__show_ticks = True

        # Text indicating values
        self._major_labels = list()
        self._minor_labels = list()

    # -----------------------------------------------------------------------

    @staticmethod
    def formats_label(value):
        return "{:.3f}".format(value)

    # -----------------------------------------------------------------------
    # Manage the set of indicators
    # -----------------------------------------------------------------------

    def add_indicator(self, seconds, colour=FRAME_FILL_COLOUR):
        """Add an indicator to draw in the ruler.

        :param seconds: (float) Time value
        :param colour: (wx.Colour) Colour of the indicator line

        """
        seconds = float(seconds)
        if seconds not in self._indicators:
            self._indicators[seconds] = colour

    # -----------------------------------------------------------------------

    def reset_indicators(self):
        """Remove all existing indicators. Do not refresh."""
        self._indicators = dict()

    # -----------------------------------------------------------------------

    def get_indicator_times(self):
        """Return the list of indicated time values."""
        return list(self._indicators.keys())

    # -----------------------------------------------------------------------

    def show_labels(self, value: bool = True):
        """Show/Hide labels.

        :param value: (bool)

        """
        self.__show_labels = bool(value)

    # -----------------------------------------------------------------------

    def show_ticks(self, value: bool = True):
        """Show/Hide ticks.

        :param value: (bool)

        """
        self.__show_ticks = bool(value)

    # -----------------------------------------------------------------------
    # Draw
    # -----------------------------------------------------------------------

    def GetMajorFont(self):
        font = self.GetFont()
        f = wx.Font(int(float(font.GetPointSize()) * 1.20),
                    wx.FONTFAMILY_SWISS,   # family,
                    wx.FONTSTYLE_NORMAL,   # style,
                    wx.FONTWEIGHT_NORMAL,  # weight,
                    underline=False,
                    faceName=font.GetFaceName(),
                    encoding=wx.FONTENCODING_SYSTEM)
        return f

    # -----------------------------------------------------------------------

    def GetMinorFont(self):
        font = self.GetFont()
        f = wx.Font(int(float(font.GetPointSize()) * 0.80),
                    wx.FONTFAMILY_SWISS,   # family,
                    wx.FONTSTYLE_NORMAL,   # style,
                    wx.FONTWEIGHT_NORMAL,  # weight,
                    underline=False,
                    faceName=font.GetFaceName(),
                    encoding=wx.FONTENCODING_SYSTEM)
        return f

    # -----------------------------------------------------------------------

    def DrawContent(self, dc, gc):
        """Override."""
        x, y, w, h = self.GetContentRect()

        # Height of the ticks
        lw, lh = self.get_text_extend(dc, gc, "Any Text")
        max_tick_height = h - lh - 4
        if max_tick_height <= 4:
            self._tick_height = 4
        else:
            self._tick_height = int(float(max_tick_height) * 0.9)

        # update all the ticks calculation
        self._update_ticks(dc)

        if self.__show_ticks is True:
            # Draw major ticks
            dc.SetPen(wx.Pen(self.GetForegroundColour(), 2, wx.PENSTYLE_SOLID))
            dc.SetFont(self.GetMajorFont())
            for label in self._major_labels:
                pos = label.pos
                dc.DrawLine(x + pos, y, x + pos, y + self._tick_height)
                dc.DrawLine(x + pos, h, x + pos, h - 3)
            # Draw minor ticks
            dc.SetFont(self.GetMinorFont())
            dc.SetPen(wx.Pen(self.GetForegroundColour(), 1, wx.PENSTYLE_SOLID))
            for label in self._minor_labels:
                pos = label.pos
                dc.DrawLine(x + pos, y, x + pos, y + (self._tick_height // 2))

        if self.__show_labels is True:
            # Draw major labels
            dc.SetPen(wx.Pen(self.GetForegroundColour(), 2, wx.PENSTYLE_SOLID))
            dc.SetFont(self.GetMajorFont())
            for label in self._major_labels:
                if label.text != "":
                    dc.DrawText(label.text, label.lx, label.ly)
            # Draw minor labels
            dc.SetFont(self.GetMinorFont())
            dc.SetPen(wx.Pen(self.GetForegroundColour(), 1, wx.PENSTYLE_SOLID))
            for label in self._minor_labels:
                if label.text != "":
                    dc.DrawText(label.text, label.lx, label.ly)

        # draw the indicators
        self._DrawIndicators(dc, gc)

        # draw the start and end values, at left and right respectively
        self._DrawLabels(dc, gc)

        # draw the current position
        self._DrawMoment(dc, gc)

    # -----------------------------------------------------------------------

    def _DrawLabels(self, dc, gc):
        """Override. Draw left-right values."""
        if self._show_startend is True:
            self._DrawValue(dc, gc, self._start, self.GetBackgroundColour(), self.GetForegroundColour())
            self._DrawValue(dc, gc, self._end, self.GetBackgroundColour(), self.GetForegroundColour())

    # -----------------------------------------------------------------------

    def _DrawIndicators(self, dc, gc):
        """Draw indicators as a stamp."""
        x, y, w, h = self.GetContentRect()
        UPP = (self._end - self._start) / float(w)  # Units Per Pixel
        dc.SetFont(self.GetMajorFont())

        for seconds in self._indicators:
            colour = self._indicators[seconds]
            self._DrawValue(dc, gc, seconds, wx.Colour(240, 255, 60), colour)

    # -----------------------------------------------------------------------

    def _DrawValue(self, dc, gc, value, fg_colour, bg_colour):
        """Draw a specific time value as a stamp.

        """
        x, y, w, h = self.GetContentRect()
        UPP = (self._end - self._start) / float(w)  # Units Per Pixel
        dc.SetFont(self.GetMajorFont())

        dc.SetPen(wx.Pen(self.GetPenForegroundColour(), 3, wx.PENSTYLE_SOLID))
        dc.SetBrush(wx.Brush(bg_colour, wx.BRUSHSTYLE_SOLID))
        # Draw indicator only if the current time range
        if self._start <= value <= self._end:
            duration = value - self._start
            position = 0
            if UPP > 0.:
                position = max(0, int(round(duration / UPP, 0)))
            # The vertical line to indicate the position
            dc.DrawLine(x + position, y, x + position, h)
            # A label to indicate the time value, with a clean background (no tick, etc).
            dc.SetPen(wx.Pen(fg_colour, 3, wx.PENSTYLE_SOLID))
            dc.SetTextForeground(fg_colour)
            label = self.formats_label(value)
            pos = x + self.__eval_label_pos(dc, label, w, x + position)
            strw, strh = dc.GetTextExtent(label)
            if position + strw < w:
                dc.DrawRectangle(max(0, x + pos),
                                 y + 1,
                                 strw + 8,  # pen width + 1
                                 min(h, strh + 4))
                dc.DrawText(label, x + pos + 4, y + 2)
            else:
                dc.DrawRectangle(max(0, x + pos - 4),
                                 y + 1,
                                 w - 3,  # pen width + 1
                                 min(h, strh + 4))
                dc.DrawText(label, x + pos, y + 2)

    # -----------------------------------------------------------------------
    # Private: Estimation of ticks and labels
    # -----------------------------------------------------------------------

    def _update_ticks(self, dc):
        """Updates all the ticks calculations."""
        self._invalidate_ticks()

        # This gets called when something has been changed
        # (i.e. we've been invalidated). Recompute all tick positions.
        x, y, w, h = self.GetContentRect()

        self._max_width = w
        self._max_height = 0

        self._bits = [0] * (w + 1)
        self._middlepos = list()

        UPP = (self._end - self._start) / float(w)  # Units per pixel
        self._find_linear_tick_sizes(UPP)
        sg = ((UPP > 0.0) and [1.0] or [-1.0])[0]

        # Major ticks
        d = self._start - UPP / 2.
        majorint = int(math.floor(sg * d / self._major))
        ii = -1

        while ii <= w:
            ii = ii + 1
            d = d + UPP
            if int(math.floor(sg * d / self._major)) > majorint:
                majorint = int(math.floor(sg * d / self._major))
                self._Tick(dc, ii, sg * majorint * self._major, major=True)

        # Minor ticks
        d = self._start - UPP / 2.
        minorint = int(math.floor(sg*d/self._minor))
        ii = -1

        while ii <= w:
            ii = ii + 1
            d = d + UPP
            if int(math.floor(sg*d/self._minor)) > minorint:
                minorint = int(math.floor(sg*d/self._minor))
                self._Tick(dc, ii, sg * minorint * self._minor, major=False)

    # -----------------------------------------------------------------------

    def _Tick(self, dc, pos, d, major):
        """Tick a particular position."""
        x, y, w, h = self.GetContentRect()

        label = TicksLabel()
        label.pos = pos
        label.lx = -1  # don't display
        label.ly = -1  # don't display
        label.text = ""
        if major:
            self._major_labels.append(label)
        else:
            self._minor_labels.append(label)

        if major:
            dc.SetFont(self.GetMajorFont())
        else:
            # a font with a smaller size
            dc.SetFont(self.GetMinorFont())

        l = self._label_string(d)
        strpos = x + self.__eval_label_pos(dc, l, w, pos)
        strlen, strh = dc.GetTextExtent(l)
        strleft = x + strpos
        strtop = y + self._tick_height
        self._max_height = max(self._max_height, h - self._tick_height)

        # See if any of the pixels we need to draw this label is already covered
        for ii in range(strlen):
            if self._bits[strpos+ii]:
                return

        # If not, position the label and give it text
        label.lx = strleft
        label.ly = strtop
        label.text = l
        if major:
            self._major_labels[-1] = label
        else:
            self._minor_labels[-1] = label

        # And mark these pixels, plus some surrounding
        # ones (the spacing between labels), as covered

        leftmargin = self._tick_height // 2
        if strpos < leftmargin:
            leftmargin = strpos

        strpos = strpos - leftmargin
        strlen = strlen + leftmargin
        rightmargin = self._tick_height // 2

        if strpos + strlen > w - 2:
            rightmargin = w - strpos - strlen
        strlen = strlen + rightmargin

        for ii in range(strlen):
            if strpos+ii < len(self._bits):
                self._bits[strpos+ii] = 1

    # -----------------------------------------------------------------------

    def __eval_label_pos(self, dc, text, w, ticks_x):
        """Return label_x, x value relatively to ticks_x."""
        strw, strh = dc.GetTextExtent(text)
        strpos = ticks_x - strw // 2
        if strpos < 0:
            strpos = 0
        if strpos + strw >= w:
            strpos = w - strw
        return strpos

    # -----------------------------------------------------------------------

    def _find_linear_tick_sizes(self, UPP):
        """Used internally.

        Given the dimensions of the slider, the range of values it
        has to display figure out how many units are in one Minor tick,
        and in one Major tick.

        The goal is to always put tick marks on nice round numbers that are
        easy for humans to grok. This is the most tricky with time.

        :param UPP: (float) Unit-per-pixel

        """
        # As a heuristic, we want at least 16 pixels between each minor tick
        units = 16.0*abs(UPP)
        d = 0.000001
        self._digits = 6

        while 1:
            if units < d:
                self._minor = d
                self._major = d * 5.0
                return

            d = d * 5.0
            if units < d:
                self._minor = d
                self._major = d * 2.0
                return

            d = d * 2.0
            self._digits = self._digits - 1

    # -----------------------------------------------------------------------

    def _label_string(self, d):
        """Used internally.

        Given a value, turn it into a string. The number of digits of
        accuracy depends on the resolution of the slider,
        i.e. how far zoomed in or out you are.

        """
        s = ""
        if d < 0.0 and d + self._minor > 0.0:
            d = 0.0

        if self._minor >= 1.0:
            s = "%d" % int(math.floor(d+0.5))
        else:
            s = (("%." + str(self._digits) + "f") % d).strip()

        return s

    # -----------------------------------------------------------------------

    def _invalidate_ticks(self):
        self._digits = 0
        self._minor = 0
        self._major = 0
        self._max_width = 0
        self._max_height = 0
        self._bits = list()
        self._middlepos = list()

        # Text indicating values
        self._major_labels = list()
        self._minor_labels = list()

# ----------------------------------------------------------------------------
# Panel for tests
# ----------------------------------------------------------------------------


class TestPanel(wx.Panel):

    def __init__(self, parent):
        super(TestPanel, self).__init__(
            parent,
            name="Ticks & Labels Slider")
        self.SetMinSize(wx.Size(320, 20))

        # Default behaviours
        p1 = sppasTicksSlider(self)
        p1.SetBackgroundColour(wx.YELLOW)
        p1.set_range(1.234, 6.6789987)
        p1.set_value(4.345)
        p1.SetMinSize(wx.Size(-1, 32))

        # No range or invalid one.
        p2 = sppasTicksSlider(self)
        p2.set_range(0.0, 0.0)

        # With options:
        # ------------

        # a value
        p3 = sppasTicksSlider(self)
        p3.set_range(1.234, 3676.6789987)
        p3.set_value(467.345)
        p3.SetMinSize(wx.Size(-1, 32))

        # a value, and indicators
        p4 = sppasTicksSlider(self)
        p4.set_range(1., 2.)
        p4.set_value(1.4)
        p4.add_indicator(1.33)
        p4.add_indicator(1.66)
        p4.SetMinSize(wx.Size(-1, 32))

        # value, start-end, no ticks, no labels
        p5 = sppasTicksSlider(self)
        p5.show_startend(True)
        p5.show_labels(False)
        p5.show_ticks(False)
        p5.set_range(1., 2.)
        p5.SetMinSize(wx.Size(-1, 32))

        # indicators and start-end
        p6 = sppasTicksSlider(self)
        p6.show_startend(True)
        p6.set_range(1., 2.)
        p6.add_indicator(1.33)
        p6.add_indicator(1.66)
        p6.SetMinSize(wx.Size(-1, 64))

        # value, start-end, no ticks, no labels
        p7 = sppasTicksSlider(self)
        p7.SetBackgroundColour(wx.WHITE)
        p7.show_startend(True)
        p7.show_labels(False)
        p7.show_ticks(False)
        p7.set_range(1., 2.)
        p7.set_value(1.66)
        p7.SetMinSize(wx.Size(-1, 32))
        p7.set_allows_changes(False)

        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(p1, 0, wx.EXPAND | wx.BOTTOM, 10)
        s.Add(p2, 0, wx.EXPAND | wx.BOTTOM, 10)
        s.Add(p3, 0, wx.EXPAND | wx.BOTTOM, 10)
        s.Add(p4, 0, wx.EXPAND | wx.BOTTOM, 10)
        s.Add(p5, 0, wx.EXPAND | wx.BOTTOM, 10)
        s.Add(p6, 0, wx.EXPAND | wx.BOTTOM, 10)
        s.Add(p7, 0, wx.EXPAND | wx.BOTTOM, 10)

        self.SetSizer(s)
        self.Bind(sppasEVT_SLIDER, self.onSlider)

    def onSlider(self, event):
        # Which slider?
        slider = event.GetEventObject()
        logging.info("{} {} {}".format(slider.GetName(), event.action, event.value))
