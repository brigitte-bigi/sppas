# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.wxapp.windows.datactrls.waveform.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  Self-drawn control window to draw the amplitude of a channel.

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
import os
import wx
from audioopy.aio import open as audio_open
from audioopy import AudioFrames

from sppas.core.config import paths
from sppas.core.coreutils import sppasTypeError
from sppas.ui.wxapp.windows import sppasDCWindow

from .audiodatavalues import AudioDataValues

# ---------------------------------------------------------------------------


class sppasWaveformWindow(sppasDCWindow):
    """A base window with a DC to draw amplitude of a channel of an audio.

    """

    def __init__(self, parent, id=-1,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.BORDER_NONE | wx.TRANSPARENT_WINDOW | wx.TAB_TRAVERSAL | wx.WANTS_CHARS | wx.FULL_REPAINT_ON_RESIZE,
                 name="waveform"):
        """Initialize a new sppasWaveformWindow instance.

        :param parent: Parent window. Must not be None.
        :param id:     A value of -1 indicates a default value.
        :param pos:    If the position (-1, -1) is specified
                       then a default position is chosen.
        :param size:   If the default size (-1, -1) is specified
                       then a default size is chosen.
        :param style:  often LC_REPORT
        :param name:   Window name.

        """
        super(sppasWaveformWindow, self).__init__(parent, id, pos, size, style, name)
        self._vert_border_width = 0
        self._horiz_border_width = 0

        # Adjust automatically the height of the amplitude
        self._auto_scroll = False

        # Style of the waveform: lines or bars
        self._pen_width = 1
        self._draw_style = "lines"

        # An instance of AudioDataValues()
        self._audiodata = None

        # The amplitude values (min-max) to draw for each step value
        self._audiodatastep = dict()

        self.Bind(wx.EVT_SIZE, self._on_size)

    # -----------------------------------------------------------------------

    def _on_size(self, event):
        # in case the width has changed, re-calculate the values of each step
        self.__reset_datastep()
        self.Refresh()

    # -----------------------------------------------------------------------
    # How the waveform will look...
    # -----------------------------------------------------------------------

    def SetLineStyle(self, style="lines"):
        """Set the draw style: lines or bars."""
        if style not in ("lines", "bars"):
            style = "lines"
        self._draw_style = style

    # -----------------------------------------------------------------------

    def SetPenWidth(self, value):
        value = int(value)
        if value < 1:
            value = 1
        if value > 20:
            value = 20
        self._pen_width = value

    # -----------------------------------------------------------------------

    def SetAutoScroll(self, value):
        value = bool(value)
        if value != self._auto_scroll:
            self._auto_scroll = value
            if self._audiodata is not None:
                # The min and the max are the ones of the audio: they can be
                # evaluated only when there is one.
                self.__reset_minmax()

    # -----------------------------------------------------------------------
    # Samples to draw
    # -----------------------------------------------------------------------

    def set_audiodata(self, audiodata):
        """Set the audio with the pre-evaluated values for a fixed number of steps.

        To draw the waveform, we are interested in the second (min) and
        third (max) values of the data.

        """
        if isinstance(audiodata, AudioDataValues) is False:
            raise sppasTypeError(type(audiodata), "AudioData")

        if audiodata.get_nframes() == 0:
            logging.error("Invalid audio data: No frames")
            return False
        if audiodata.get_framerate() is None:
            logging.error("Invalid audio data: No sample framerate")
            return False
        if audiodata.get_sampwidth() is None:
            logging.error("Invalid audio data: No sample witdth")
            return False
        if audiodata.get_nchannels() is None:
            logging.error("Invalid audio data: unknown number of channels")
            return False

        self._audiodata = audiodata
        self.__reset_minmax()
        self.__reset_datastep()
        return True

    # -----------------------------------------------------------------------

    def __reset_minmax(self):
        # Min and max amplitude values for this sampwidth (2=>32k)
        self._audiodata_max = AudioFrames().get_maxval(self._audiodata.get_sampwidth())
        self._audiodata_min = -self._audiodata_max

        # Min and max amplitude values observed in the samples of the period
        if self._auto_scroll is True:
            min_val, max_val = self.__get_minmax_values()

            # autoscroll is limited to at least 10% of what is possible
            # and the same range for all channels
            self._audiodata_max = int(max(float(max_val) * 1.1, float(self._audiodata_max) * 0.1))
            self._audiodata_min = int(min(float(min_val) * 1.1, float(self._audiodata_min) * 0.1))

    # -----------------------------------------------------------------------

    def __get_minmax_values(self):
        """Min and max amplitude values observed in the samples of the period.

        A step without any sample value is None: it happens when the period is
        so short that there are more steps than samples. These steps are
        ignored, they can't be compared to a number.

        """
        min_val = AudioFrames().get_maxval(self._audiodata.get_sampwidth())
        max_val = -self._audiodata_max
        for c in range(len(self._audiodata.values)):
            min_values = [v for v in self._audiodata.values[c][1] if v is not None]
            if len(min_values) > 0:
                min_val_channel = min(min_values)
                if min_val_channel < min_val:
                    min_val = min_val_channel

            max_values = [v for v in self._audiodata.values[c][2] if v is not None]
            if len(max_values) > 0:
                max_val_channel = max(max_values)
                if max_val_channel > max_val:
                    max_val = max_val_channel

        return min_val, max_val

    # -----------------------------------------------------------------------

    def GetContentRect(self):
        """Override. Adjust the width with the period to draw."""
        x, y, w, h = sppasDCWindow.GetContentRect(self)
        if self._audiodata is None:
            return x, y, w, h
        audio_duration = self._audiodata.get_duration()

        if audio_duration < self._audiodata.get_end_period():
            total_visible = self._audiodata.get_end_period() - self._audiodata.get_start_period()
            audio_visible = audio_duration - self._audiodata.get_start_period()
            w = int((w * audio_visible) / total_visible)

        return x, y, w, h

    # -----------------------------------------------------------------------

    def __reset_datastep(self):
        self._audiodatastep = dict()
        if self._audiodata is None:
            return
        if len(self._audiodata.values) != self._audiodata.get_nchannels():
            logging.warning("problem with audio data: {:d} != {:d}"
                            "".format(len(self._audiodata.values), self._audiodata.get_nchannels()))
            return

        # Fill in the data of each step.
        # They depend on the view: bars, lines, oversampled
        x, y, w, h = self.GetContentRect()
        if w < 2:
            # out of period, nothing to draw.
            return
        # There are more values than pixels
        for c in range(self._audiodata.get_nchannels()):
            self._audiodatastep[c] = list()

        if self._draw_style == "bars":
            xstep = float(self._pen_width) + (float(self._pen_width) / 3.)
        else:
            xstep = float(self._pen_width)
        x += int(xstep / 2.)

        for c in range(self._audiodata.get_nchannels()):
            xcur = x
            coeff = float(len(self._audiodata.values[c][0])) / float(w)
            while xcur < (x + w):
                # the range of values we'll use for this xcur
                dcur = int(float(xcur - x) * coeff)
                dnext = int((float(xcur) + xstep - float(x)) * coeff)
                if dnext > len(self._audiodata.values[c][1]):
                    dnext = len(self._audiodata.values[c][1])

                # get min and max values, by ignoring None
                minv = None
                maxv = None
                for i in range(dcur, dnext):
                    if self._audiodata.values[c][1][i] is not None:
                        if minv is None or minv > self._audiodata.values[c][1][i]:
                            minv = self._audiodata.values[c][1][i]
                    if self._audiodata.values[c][2][i] is not None:
                        if maxv is None or maxv < self._audiodata.values[c][2][i]:
                            maxv = self._audiodata.values[c][2][i]

                if minv is not None and maxv is not None:
                    # we have samples in this range
                    self._audiodatastep[c].append((xcur, minv, maxv))
                else:
                    self._audiodatastep[c].append(None)

                # next step
                xcur += int(xstep)

    # -----------------------------------------------------------------------
    # Draw
    # -----------------------------------------------------------------------

    def DrawContent(self, dc, gc):
        """Draw the amplitude values as a waveform."""
        if self._audiodata is None:
            return
        if self._audiodata.get_nchannels() < 1:
            return

        x, y, w, h = self.GetContentRect()
        ch = h // self._audiodata.get_nchannels()

        for i in range(self._audiodata.get_nchannels()):
            # Draw horizontal lines
            self.__draw_horiz_axes(dc, gc, x, y + (i*ch), w, ch)
            if len(self._audiodatastep) == 0:
                # At least one channel in the data is required!
                continue

            # Draw the i-th channel in the given rectangle.
            if self._audiodata.get_oversampled() is False:
                # Draw amplitude values either with bars or continuous lines
                if self._draw_style == "bars":
                    self.__draw_amplitude_as_bars(i, dc, x, y + (i*ch), w, ch)
                else:
                    self.__draw_amplitude_as_lines(i, dc, x, y + (i*ch), w, ch)
            else:
                # More pixels than values to draw... i.e. high zoom level.
                self.__draw_amplitude_oversampled(i, dc, x, y + (i*ch), w, ch)

    # -----------------------------------------------------------------------

    def __draw_horiz_axes(self, dc, gc, x, y, w, h):
        """Draw an horizontal line at the middle (indicate 0 value). """
        p = h // 100
        y_center = y + (h // 2)
        pen = wx.Pen(wx.Colour(128, 128, 212, 128), p, wx.PENSTYLE_SOLID)
        pen.SetCap(wx.CAP_BUTT)
        dc.SetPen(pen)

        # Line at the centre
        th, tw = self.get_text_extend(dc, gc, "-0.0")
        dc.DrawLine(x, y_center, x + w, y_center)
        self.DrawLabel("0", dc, gc, x, y_center - (th // 3))

        if self._auto_scroll is False:
            # Lines at top and bottom
            dc.DrawLine(x, y + (p//2), x + w, y + (p//2))
            dc.DrawLine(x, h - (p//2), x + w, h - (p//2))

            # Scale at top and bottom
            self.DrawLabel("1", dc, gc, x, y)
            self.DrawLabel("-1", dc, gc, x, h - (th//2))

            if h > 200:
                pen = wx.Pen(wx.Colour(128, 128, 212, 196), 1, wx.PENSTYLE_DOT)
                pen.SetCap(wx.CAP_BUTT)
                dc.SetPen(pen)
                dc.DrawLine(x, h//4, x + w, h//4)
                dc.DrawLine(x, y_center + h//4, x + w, y_center + h//4)

        else:
            if self._audiodata.get_nframes() > 0:
                pen = wx.Pen(wx.Colour(128, 128, 212, 196), 2, wx.PENSTYLE_DOT)
                pen.SetCap(wx.CAP_BUTT)
                dc.SetPen(pen)
                # the height we should use to draw the whole scale
                audio_data_max = AudioFrames().get_maxval(self._audiodata.get_sampwidth())
                min_val, max_val = self.__get_minmax_values()
                viewed_ratio = float(max_val) / float(audio_data_max)
                viewed_ratio = round(viewed_ratio, 1)
                value = viewed_ratio * float(audio_data_max)

                # Lines at top and bottom
                ypixels = int(value * (float(h) / 2.0) / float(self._audiodata_max))
                dc.DrawLine(x, y_center - ypixels, x + w, y_center - ypixels)
                self.DrawLabel(str(viewed_ratio), dc, gc, x, y_center - ypixels - (th // 3))

                dc.DrawLine(x, y_center + ypixels, x + w, y_center + ypixels)
                self.DrawLabel(str(-viewed_ratio), dc, gc, x, y_center + ypixels - (th // 3))

    # -----------------------------------------------------------------------

    def __draw_amplitude_as_lines(self, channel, dc, x, y, w, h):
        """Draw the waveform as joint lines.

        Current min/max observed values are joint to the next ones by a
        line. It looks like an analogic signal more than a discrete one.

        """
        y_center = y + (h // 2)
        ypixelsminprec = y_center

        # Fix the pen style and color
        pen = wx.Pen(self.GetPenForegroundColour(), self._pen_width, wx.PENSTYLE_SOLID)
        dc.SetPen(pen)

        for step in range(len(self._audiodatastep[channel])):

            if self._audiodatastep[channel][step] is None:
                break

            (xcur, datamin, datamax) = self._audiodatastep[channel][step]
            if datamin is None:
                break

            # Convert the data into a "number of pixels" -- height
            ypixelsmax = int(float(datamax) * (float(h) / 2.0) / float(self._audiodata_max))
            if self._audiodata_min != 0:
                ypixelsmin = int(float(datamin) * (float(h) / 2.0) / float(abs(self._audiodata_min)))
            else:
                ypixelsmin = 0

            # draw a line between current value to next value
            if xcur != x:
                dc.DrawLine(xcur, y_center - ypixelsminprec, xcur, y_center - ypixelsmax)
                if step+1 < len(self._audiodatastep[channel]):
                    if self._audiodatastep[channel][step+1] is not None:
                        (xnext, datamin, datamax) = self._audiodatastep[channel][step+1]
                        dc.DrawLine(xnext, y_center - ypixelsmin, xnext, y_center - ypixelsmax)

            ypixelsminprec = ypixelsmin

    # -----------------------------------------------------------------------

    def __draw_amplitude_as_bars(self, channel, dc, x, y, w, h):
        """Draw the waveform as vertical bars.

        Current min/max observed values are drawn by a vertical line.

        """
        y_center = y + (h // 2)

        # Fix the pen style and color
        pen = wx.Pen(self.GetPenForegroundColour(), self._pen_width, wx.PENSTYLE_SOLID)
        dc.SetPen(pen)

        for step in range(len(self._audiodatastep[channel])):

            if self._audiodatastep[channel][step] is None:
                continue

            (xcur, datamin, datamax) = self._audiodatastep[channel][step]

            # Convert the data into a "number of pixels" -- height
            ypixelsmax = int(float(datamax) * (float(h) / 2.0) / float(self._audiodata_max))
            if self._audiodata_min != 0:
                ypixelsmin = int(float(datamin) * (float(h) / 2.0) / float(abs(self._audiodata_min)))
            else:
                ypixelsmin = 0

            # draw a vertical line
            if xcur != x:
                dc.DrawLine(xcur, y_center - ypixelsmax, xcur, y_center - ypixelsmin)

    # -----------------------------------------------------------------------

    def __draw_amplitude_oversampled(self, channel, dc, x, y, w, h):
        """Draw the data with vertical lines.

        Apply only if there are less data values than pixels to draw them.

        """
        y_center = y + (h // 2)
        if w < 10:
            return
        nb_values = 0
        for value in self._audiodatastep[channel]:
            if value is not None:
                nb_values += 1

        point_size = max(3, round(float(w) / float(nb_values)))
        prev = (0, y_center)
        for step in range(len(self._audiodatastep[channel])):
            if self._audiodatastep[channel][step] is None:
                continue
            # oversampling means that min and max have the same value
            # because there is only one value in this time interval!
            (xcur, value, datamax) = self._audiodatastep[channel][step]

            # Convert the data into a "number of pixels" -- height
            pen = wx.Pen(self.GetPenForegroundColour(), 1, wx.PENSTYLE_SOLID)
            dc.SetPen(pen)
            if value > 0:
                # convert the data into a "number of pixels" -- height
                y_pixels = int(float(value) * (float(h) / 2.0) / float(self._audiodata_max))
            else:
                y_pixels = int(float(value) * (float(h) / 2.0) / float(abs(self._audiodata_min)))

            # draw a line
            if prev[0] > 0:
                pen = wx.Pen(self.GetPenForegroundColour(), 1, wx.PENSTYLE_DOT)
                dc.SetPen(pen)
                dc.DrawLine(prev[0], prev[1], xcur, y_center - y_pixels)

            # Draw a circle at the exact value
            pen = wx.Pen(self.GetPenForegroundColour(), point_size, wx.PENSTYLE_SOLID)
            dc.SetPen(pen)
            dc.DrawPoint(xcur, y_center - y_pixels)
            prev = (xcur, y_center - y_pixels)

# ----------------------------------------------------------------------------
# Panels to test
# ----------------------------------------------------------------------------


class TestPanel(wx.Panel):

    def __init__(self, parent):
        super(TestPanel, self).__init__(
            parent,
            style=wx.BORDER_NONE | wx.WANTS_CHARS,
            name="Test Waveform")
        sizer = wx.BoxSizer(wx.VERTICAL)

        sample = os.path.join(paths.samples, "samples-fra", "F_F_B003_P8.wav")   # mono
        self._audio = audio_open(sample)
        w0 = self.__draw_waveform(18., 22.)
        sizer.Add(w0, 1, wx.EXPAND)

        w1 = self.__draw_waveform(18., 19.)
        w1.SetPenWidth(9)
        w1.SetLineStyle("bars")
        w1.SetAutoScroll(True)
        sizer.Add(w1, 1, wx.EXPAND)

        w2 = self.__draw_waveform(3.340, 3.360)
        sizer.Add(w2, 1, wx.EXPAND)

        sample_stereo = os.path.join(paths.samples, "samples-eng", "oriana3.wave")
        self._audios = audio_open(sample_stereo)
        ws = self.__draw_stereo_waveform(10, 14.)
        sizer.Add(ws, 1, wx.EXPAND)

        self.SetSizer(sizer)

    def __draw_waveform(self, start_time, end_time):
        audiodata = AudioDataValues()
        frames = self._audio.read_frames(self._audio.get_nframes())
        audiodata.set_audio_data(self._audio.get_nchannels(),
                                 self._audio.get_sampwidth(),
                                 self._audio.get_framerate(),
                                 frames=frames)
        self._audio.seek(0)
        audiodata.set_period(start_time, end_time)

        w = sppasWaveformWindow(self)
        w.set_audiodata(audiodata)
        return w

    def __draw_stereo_waveform(self, start_time, end_time):
        audiodata = AudioDataValues()
        frames = self._audios.read_frames(self._audios.get_nframes())
        audiodata.set_audio_data(self._audios.get_nchannels(),
                                 self._audios.get_sampwidth(),
                                 self._audios.get_framerate(),
                                 frames=frames)
        audiodata.set_period(start_time, end_time)
        logging.debug(" ... draw stereo waveform: %d" % self._audios.get_nchannels())

        w = sppasWaveformWindow(self)
        w.set_audiodata(audiodata)
        return w
