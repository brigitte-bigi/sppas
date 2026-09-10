# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.wxapp.page_editor.media.timesslider.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  The main slider to browse throw periods of time.

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

A selection bar to mimic the one into Praat software tool; it allows to
indicate a moment in time and to select different periods of time, named:

    - whole duration;
    - visible part;
    - selected part;
    - a time ruler.

"""

import wx
import logging

from sppas.ui import _
from sppas.ui.wxapp.windows.buttons import ToggleTextButton
from sppas.ui.wxapp.windows.panels import sppasPanel
from sppas.ui.wxapp.windows.slider import sppasEVT_SLIDER
from sppas.ui.wxapp.windows.slider import sppasSlider

from .tickslider import sppasTicksSlider
from .mediaevents import MediaEvents

# ---------------------------------------------------------------------------


MSG_TOTAL_DURATION = _("Total duration: ")
MSG_VISIBLE_DURATION = _("Visible part: ")
SECONDS_UNIT = _("seconds")

# ----------------------------------------------------------------------------


class ToggleSelection(ToggleTextButton):
    """A toggle button with a specific design and properties.

    """

    # The selection has its own colors
    SELECTION_BG_COLOUR = wx.Colour(250, 170, 180)
    SELECTION_FG_COLOUR = wx.Colour(200, 70, 80)

    # -----------------------------------------------------------------------

    def __init__(self, parent,
                 id=wx.ID_ANY,
                 label="",
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 name=wx.ButtonNameStr):
        """Default class constructor.

        :param parent: the parent (required);
        :param id: window identifier.
        :param label: label text of the check button;
        :param pos: the position;
        :param size: the size;
        :param name: the name of the bitmap.

        """
        super(ToggleSelection, self).__init__(parent, id, label, pos, size, name)
        ToggleTextButton.SetValue(self, False)
        self._bg_false_colour = self.GetBackgroundColour()
        self.SetHorizBorderWidth(1)
        self.SetFocusWidth(0)
        self.SetBorderColour(self.SELECTION_FG_COLOUR)

    # -----------------------------------------------------------------------

    def SetForegroundColour(self, colour):
        """Override. Our fg can't be changed."""
        ToggleTextButton.SetForegroundColour(self, ToggleSelection.SELECTION_FG_COLOUR)

    # -----------------------------------------------------------------------

    def SetValue(self, value):
        ToggleTextButton.SetValue(self, value)
        if self.GetValue() is True:
            self._bg_false_colour = self.GetBackgroundColour()
            self.SetBackgroundColour(ToggleSelection.SELECTION_BG_COLOUR)
        else:
            self.SetBackgroundColour(self._bg_false_colour)

        self.SetBorderColour(self.SELECTION_FG_COLOUR)

# ----------------------------------------------------------------------------


class ToggleSlider(ToggleTextButton):
    """A toggle button with a specific design and properties.

    """

    # Foreground of the pressed toggle is blue if pressed
    FG_TRUE_COLOUR = wx.Colour(30, 80, 210)

    # BG_IMAGE = os.path.join(paths.etc, "images", "bg_brushed_metal2.jpg")

    # -----------------------------------------------------------------------

    def __init__(self, parent,
                 id=wx.ID_ANY,
                 label="",
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 name=wx.ButtonNameStr):
        """Default class constructor.

        :param parent: the parent (required);
        :param id: window identifier.
        :param label: label text of the check button;
        :param pos: the position;
        :param size: the size;
        :param name: the name of the bitmap.

        """
        super(ToggleSlider, self).__init__(parent, id, label, pos, size, name)
        ToggleTextButton.SetValue(self, False)
        self._fg_false_colour = self.GetForegroundColour()
        self.SetHorizBorderWidth(1)
        self.SetFocusWidth(0)

    # -----------------------------------------------------------------------

    def SetBackgroundColour(self, colour):
        ToggleTextButton.SetBackgroundColour(self, colour)
        border_color = self.GetHighlightedColour(colour, 30)
        self.SetBorderColour(border_color)

    # -----------------------------------------------------------------------

    def SetValue(self, value):
        ToggleTextButton.SetValue(self, value)
        if self.GetValue() is True:
            self._fg_false_colour = self.GetForegroundColour()
            wx.Window.SetForegroundColour(self, ToggleSlider.FG_TRUE_COLOUR)
        else:
            self.SetForegroundColour(self._fg_false_colour)

# ----------------------------------------------------------------------------


class TimeSliderPanel(sppasPanel):
    """A panel embedding information about time: start, end, selected, etc.

    The range of the slider depends on the selected button. It's one of:
        - from the beginning of the visible part to the beginning of the selection;
        - the period during the selection;
        - the period after the selection until the end of the visible part;
        - the whole visible part;
        - the whole period, from 0 to duration.

    """

    # The selection has its own colors
    SELECTION_BG_COLOUR = wx.Colour(250, 170, 180)
    SELECTION_FG_COLOUR = wx.Colour(200, 70, 80)

    # -----------------------------------------------------------------------

    def __init__(self, parent, name="time_slider_panel"):
        """Create the panel to display time information.

        """
        super(TimeSliderPanel, self).__init__(
            parent,
            id=wx.ID_ANY,
            pos=wx.DefaultPosition,
            size=wx.DefaultSize,
            style=wx.NO_FULL_REPAINT_ON_RESIZE | wx.BORDER_NONE,
            name=name)

        # Members
        self.__duration = 0.
        self.__start_visible = 0.
        self.__end_visible = 0.
        self.__start_selection = 0.
        self.__end_selection = 0.

        # Create the GUI
        self._create_content()
        self._setup_events()

        # Look&feel
        try:
            settings = wx.GetApp().settings
            self._zoom = settings.editor_timeline_zoom
            self.SetBackgroundColour(settings.bg_color)
            self.SetForegroundColour(settings.fg_color)
            self.SetFont(settings.text_font)
        except AttributeError:
            self.InheritAttributes()
            self._zoom = 100

        self.__update_height()

    # -----------------------------------------------------------------------
    # Setters of the GUI
    # -----------------------------------------------------------------------

    def show_range(self, value=True):
        """Show the currently selected range."""
        if bool(value) is True:
            self._ruler.show_startend(True)
        else:
            self._ruler.show_startend(False)
        self.__update_height()

    # -----------------------------------------------------------------------

    def show_rule(self, value=True):
        """Show a ruler of the visible part."""
        if bool(value) is True:
            self._ruler.Show()
        else:
            self._ruler.Hide()
        self.__update_height()

    # -----------------------------------------------------------------------
    # Toggle buttons value
    # -----------------------------------------------------------------------

    def is_selection(self):
        """Return True if the toggle button of the selection is pressed."""
        return self._btn_selection.GetValue()

    # -----------------------------------------------------------------------

    def is_visible(self):
        """Return True if the toggle button of the selection is pressed."""
        return self._btn_visible.GetValue()

    # -----------------------------------------------------------------------

    def is_duration(self):
        """Return True if the toggle button of the selection is pressed."""
        return self._btn_duration.GetValue()

    # -----------------------------------------------------------------------
    # Slider
    # -----------------------------------------------------------------------

    def get_range(self):
        """Return the current range value of the slider."""
        if self._btn_visible.GetValue() is True:
            return self.__start_visible, self.__end_visible

        if self._btn_before.GetValue() is True:
            return self.__start_visible, self.__start_selection

        if self._btn_selection.GetValue() is True:
            return self.__start_selection, self.__end_selection

        if self._btn_after.GetValue() is True:
            return self.__end_selection, self.__end_visible

        return 0., self.__duration

    # -----------------------------------------------------------------------

    def get_value(self):
        """Return the current position value of the slider."""
        return self._ruler.get_value()

    # -----------------------------------------------------------------------

    def set_value(self, pos):
        """Set the current position value of the slider."""
        pos = float(pos)
        if pos < 0.:
            return False
        if pos > self.__duration:
            return False
        current = self._ruler.get_value()
        if current != pos:
            self._ruler.set_value(pos)
            self._ruler.Refresh()
            return True
        return False

    # -----------------------------------------------------------------------
    # Whole duration - i.e. the max value
    # -----------------------------------------------------------------------

    def get_duration(self):
        """Return the duration value (float)"""
        return self.__duration

    # -----------------------------------------------------------------------

    def set_duration(self, value=0.):
        """Fix the duration value.

        :param value: (float) Time value in seconds.

        """
        value = float(value)
        if value < 0.:
            raise ValueError("The duration can't be negative. Got {}.".format(value))

        self.__duration = value
        self._btn_duration.SetLabel("{:s} {:s} {:s}".format(MSG_TOTAL_DURATION, self.__seconds_label(value), SECONDS_UNIT))

        # if other values are out of duration range, they need update.
        if self.__end_visible > value:
            self.__end_visible = value
        if self.__end_selection > value:
            self.__end_selection = value
        if self.__start_visible > value:
            self.__start_visible = value
        if self.__start_selection > value:
            self.__start_selection = value

        # Disable all other buttons. Enable duration toggle button.
        if value == 0.:
            self.set_visible_range(0., 0.)
            self.__choose_toggle(None)
        else:
            self.__choose_toggle(self._btn_duration)

        # Update the ruler
        self.__update_select_buttons()
        self.__update_ruler()
        self.Refresh()

    # -----------------------------------------------------------------------
    # Visible part - must be less than duration
    # -----------------------------------------------------------------------

    def get_visible_start(self):
        """Return start time value of the visible part."""
        return self.__start_visible

    # -----------------------------------------------------------------------

    def get_visible_end(self):
        """Return end time value of the visible part."""
        return self.__end_visible

    # -----------------------------------------------------------------------

    def get_visible_range(self):
        """Return (start, end) time values of the visible part."""
        return self.__start_visible, self.__end_visible

    # -----------------------------------------------------------------------

    def set_visible_range(self, start, end):
        """Set the visible time range."""
        start = float(start)
        end = float(end)
        if start < 0.:
            start = 0.
        if end < start:
            raise ValueError("The end {} of the visible range is before its "
                             "start {}.".format(end, start))

        if end > self.__duration:
            # The visible period can't be after the end. Enlarging the duration
            # here would make believe the caller that its range was accepted.
            logging.warning(
                "Given end visible value {} is greater than duration {}. "
                "It is reduced to the duration.".format(end, self.__duration))
            end = self.__duration
            if start > end:
                start = end

        self.__start_visible = start
        self.__end_visible = end
        dur = end - start
        self._btn_visible.SetLabel("{:s} {:s} {:s}".format(MSG_VISIBLE_DURATION, self.__seconds_label(dur), SECONDS_UNIT))
        self._ruler.set_range(start, end)
        if dur == 0.:
            self.__choose_toggle(self._btn_duration)
        else:
            self.__choose_toggle(self._btn_visible)

        # Update others
        self.__update_select_buttons()
        self.Refresh()

    # -----------------------------------------------------------------------
    # Set selected part - must be less than duration
    # -----------------------------------------------------------------------

    def get_selection_start(self):
        """Return start time value of the selected part."""
        return self.__start_selection

    # -----------------------------------------------------------------------

    def get_selection_end(self):
        """Return end time value of the selected part."""
        return self.__end_selection

    # -----------------------------------------------------------------------

    def get_selection_range(self):
        """Return (start, end) time values of the selected part."""
        return self.__start_selection, self.__end_selection

    # -----------------------------------------------------------------------

    def set_selection_range(self, start, end):
        """Set the selected time range."""
        start = float(start)
        end = float(end)
        if end < start:
            raise ValueError("The end {} of the selection is before its "
                             "start {}.".format(end, start))
        if start < 0.:
            raise ValueError("The start {} of the selection can't be "
                             "negative.".format(start))

        if end > self.__duration:
            # Same as the visible range: the selection is inside the media.
            logging.warning(
                "Given end selection value {} is greater than duration {}. "
                "It is reduced to the duration.".format(end, self.__duration))
            end = self.__duration
            if start > end:
                start = end

        self.__start_selection = start
        self.__end_selection = end
        self.__update_select_buttons()

        # Update the slider
        self.__update_ruler()
        self.Refresh()

    # -----------------------------------------------------------------------
    # enabled
    # -----------------------------------------------------------------------

    def get_enabled_start(self):
        """Return the start value of the enabled button."""
        if self._btn_visible.GetValue() is True:
            return self.__start_visible

        if self._btn_before.GetValue() is True:
            return self.__start_visible

        if self._btn_selection.GetValue() is True:
            return self.__start_selection

        if self._btn_after.GetValue() is True:
            return self.__end_selection

        return 0.

    # -----------------------------------------------------------------------
    # Look&feel
    # -----------------------------------------------------------------------

    def SetFont(self, font):
        """Override. """
        # The font of this panel is used only to control its height
        f = wx.Font(int(float(font.GetPointSize()) * 1.2),
                    wx.FONTFAMILY_SWISS,   # family,
                    wx.FONTSTYLE_NORMAL,   # style,
                    wx.FONTWEIGHT_NORMAL,  # weight,
                    underline=False,
                    faceName=font.GetFaceName(),
                    encoding=wx.FONTENCODING_SYSTEM)
        wx.Panel.SetFont(self, f)

        # The font that is displaying message is inside the children
        for c in self.GetChildren():
            f = wx.Font(int(float(font.GetPointSize()) * 0.8),
                        font.GetFamily(),        # family,
                        wx.FONTSTYLE_NORMAL,     # style,
                        wx.FONTWEIGHT_NORMAL,    # weight,
                        underline=False,
                        faceName=font.GetFaceName(),
                        encoding=wx.FONTENCODING_SYSTEM)
            c.SetFont(f)

        # Update height of each panel and layout
        self.__update_height()

    # -----------------------------------------------------------------------

    def SetBackgroundColour(self, colour):
        """Override. """
        wx.Panel.SetBackgroundColour(self, colour)
        for child in self.GetChildren():
            if child.GetName() == "time_ruler":
                child.SetBackgroundColour(wx.Colour(250, 250, 165))
            else:
                child.SetBackgroundColour(colour)

    # -----------------------------------------------------------------------

    def SetForegroundColour(self, colour):
        """Override. """
        wx.Panel.SetForegroundColour(self, colour)
        for child in self.GetChildren():
            if isinstance(child, ToggleTextButton) is True and child.GetValue() is True:
                child.SetForegroundColour(ToggleSlider.FG_TRUE_COLOUR)
            else:
                child.SetForegroundColour(colour)
                for c in child.GetChildren():
                    if isinstance(child, ToggleTextButton) is True and child.GetValue() is True:
                        child.SetForegroundColour(ToggleSlider.FG_TRUE_COLOUR)
                    else:
                        if c.GetName() == "selection_button":
                            c.SetForegroundColour(TimeSliderPanel.SELECTION_FG_COLOUR)
                        elif c.GetName() == "time_ruler":
                            c.SetForegroundColour(wx.Colour(0, 0, 20))
                        else:
                            c.SetForegroundColour(colour)

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
        self._zoom = value
        self.__update_height()

    # -----------------------------------------------------------------------

    def OnSize(self, event):
        self.__update_select_buttons()
        self.Refresh()
        event.Skip()

    # -----------------------------------------------------------------------
    # Construct the GUI
    # -----------------------------------------------------------------------

    def _create_content(self):
        """Create the content of the panel."""
        btn_dur = ToggleSlider(self, label="--", name="total_button")
        btn_part = ToggleSlider(self, label="--", name="visible_part_button")

        panel_sel = sppasPanel(self, name="selection_panel")
        btn_before_sel = ToggleSlider(panel_sel, label="--", name="before_sel_button")
        btn_before_sel.Hide()
        btn_after_sel = ToggleSlider(panel_sel, label="--", name="after_sel_button")
        btn_after_sel.Hide()
        btn_during_sel = ToggleSelection(panel_sel, label="--", name="selection_button")
        btn_during_sel.Hide()

        slider = sppasSlider(self, name="time_slider")
        slider.set_allows_changes(False)

        ruler = sppasTicksSlider(self, name="time_ruler")
        ruler.show_startend(True)
        ruler.set_allows_changes(True)
        ruler.set_range(0., 0.)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(slider, 0, wx.EXPAND, 0)      # indicate the range of the current toggled
        sizer.Add(btn_dur, 0, wx.EXPAND, 0)
        sizer.Add(btn_part, 0, wx.EXPAND, 0)
        sizer.Add(panel_sel, 0, wx.EXPAND, 0)
        sizer.Add(ruler, 0, wx.EXPAND, 0)       # a rule on the visible part
        self.SetSizer(sizer)

    # -----------------------------------------------------------------------

    @property
    def _btn_duration(self):
        return self.FindWindow("total_button")

    @property
    def _btn_visible(self):
        return self.FindWindow("visible_part_button")

    @property
    def _ruler(self):
        return self.FindWindow("time_ruler")

    @property
    def _btn_before(self):
        return self.FindWindow("before_sel_button")

    @property
    def _btn_after(self):
        return self.FindWindow("after_sel_button")

    @property
    def _btn_selection(self):
        return self.FindWindow("selection_button")

    @property
    def _selection(self):
        return self.FindWindow("selection_panel")

    # -----------------------------------------------------------------------

    def _setup_events(self):
        """Bind events."""
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self._btn_before.Bind(wx.EVT_TOGGLEBUTTON, self._process_toggle_event)
        self._btn_selection.Bind(wx.EVT_TOGGLEBUTTON, self._process_toggle_event)
        self._btn_after.Bind(wx.EVT_TOGGLEBUTTON, self._process_toggle_event)
        self._btn_visible.Bind(wx.EVT_TOGGLEBUTTON, self._process_toggle_event)
        self._btn_duration.Bind(wx.EVT_TOGGLEBUTTON, self._process_toggle_event)
        self.Bind(sppasEVT_SLIDER, self._process_slider_event)

    # -----------------------------------------------------------------------

    def _process_toggle_event(self, event):
        """Process a change of time range."""
        # Only the button which was toggled is kept pressed
        self.__choose_toggle(event.GetEventObject())

        modified = self.__update_ruler()
        if modified is True:
            self.Refresh()
            evt = MediaEvents.MediaPeriodEvent(period=self._ruler.get_range())
            evt.SetEventObject(self)
            wx.PostEvent(self.GetParent(), evt)

    # -----------------------------------------------------------------------

    def _process_slider_event(self, event):
        """Process a change of time range requested by the ruler."""
        if event.action in ("scroll", "zoom"):
            start, end = event.value
            if start < 0.:
                start = 0.
            if end > self.__duration:
                end = self.__duration
            self.set_visible_range(start, end)
            event.value = (start, end)
            wx.PostEvent(self.GetParent(), event)
        else:
            event.Skip()

    # -----------------------------------------------------------------------

    def __update_ruler(self):
        """Set the ruler to the visible period.

        :return: (bool) True if the range of the ruler was changed

        """
        old_start, old_end = self._ruler.get_range()

        # The ruler is showing the visible period. It is NOT showing the period
        # given by get_range(), the one the toggle buttons are enabling: they
        # are choosing which part of the visible period is played, and scaling
        # the ticks again at each of these choices would be misleading.
        self._ruler.set_range(self.__start_visible, self.__end_visible)

        new_start, new_end = self._ruler.get_range()
        if old_start != new_start or old_end != new_end:
            self._ruler.Refresh()
            return True
        else:
            return False

    # -----------------------------------------------------------------------

    def __choose_toggle(self, btn):
        self._btn_before.SetValue(False)
        self._btn_after.SetValue(False)
        self._btn_selection.SetValue(False)
        self._btn_duration.SetValue(False)
        self._btn_visible.SetValue(False)
        if btn is not None:
            btn.SetValue(True)

    # -----------------------------------------------------------------------

    def __has_toggle(self):
        return any((self._btn_before.GetValue(),
                   self._btn_selection.GetValue(),
                   self._btn_after.GetValue(),
                   self._btn_visible.GetValue(),
                   self._btn_duration.GetValue()))

    # -----------------------------------------------------------------------

    def __update_select_buttons(self):
        w = self.GetSize().GetWidth()
        visible_duration = self.__end_visible - self.__start_visible
        wb = 0  # width of the button before
        wa = 0  # width of the button after

        # If the selection is totally outside of the visible segment
        if self.__start_selection >= self.__end_visible or self.__end_selection <= self.__start_visible:
            # De-select the button
            if self._btn_before.GetValue() is True:
                self.__choose_toggle(self._btn_visible)
            elif self._btn_selection.GetValue() is True:
                self.__choose_toggle(self._btn_visible)
            elif self._btn_after.GetValue() is True:
                self.__choose_toggle(self._btn_visible)

            # Hide the selection buttons.
            self._btn_before.Hide()
            self._btn_selection.Hide()
            self._btn_after.Hide()

        else:
            # The selection is inside or overlaps the visible segment

            # overlap at the beginning. no before button
            before_duration = self.__start_selection - self.__start_visible
            if before_duration <= 0.:
                if self._btn_before.GetValue() is True:
                    self.__choose_toggle(self._btn_visible)
                self._btn_before.Hide()
                before_duration = 0.
            else:
                self._btn_before.Show()
                wb = int(float(w) * before_duration / visible_duration)
                self._btn_before.SetSize(wx.Size(wb, -1))

            # overlap at the end. no after button
            after_duration = self.__end_visible - self.__end_selection
            if after_duration <= 0.:
                if self._btn_after.GetValue() is True:
                    self.__choose_toggle(self._btn_visible)
                self._btn_after.Hide()
                after_duration = 0.
            else:
                self._btn_after.Show()
                wa = int(float(w) * after_duration / visible_duration)
                self._btn_after.SetSize(wx.Size(wa, -1))

            # selection button
            self._btn_selection.Show()
            selection_duration = self.__end_selection - self.__start_selection
            self._btn_selection.SetSize(wx.Size((w - wb - wa), -1))

            # Fix labels
            self._btn_before.SetLabel(self.__seconds_label(before_duration))
            self._btn_selection.SetLabel(self.__seconds_label(selection_duration))
            self._btn_after.SetLabel(self.__seconds_label(after_duration))

        self._btn_before.SetPosition(wx.Point(0, 0))
        self._btn_selection.SetPosition(wx.Point(wb, 0))
        self._btn_after.SetPosition(wx.Point(w - wa, 0))

        self._selection.Refresh()

    # -----------------------------------------------------------------------

    def __update_height(self):
        h = self.GetFont().GetPixelSize()[1]

        self._selection.SetMinSize(wx.Size(-1, h))
        self._btn_duration.SetMinSize(wx.Size(-1, h))
        self._btn_visible.SetMinSize(wx.Size(-1, h))
        panel_height = 3 * h

        ruler_height = int(float(h)*1.8*self._zoom/100.)
        self._ruler.SetMinSize(wx.Size(-1, ruler_height))
        if self._ruler.IsShown():
            panel_height += ruler_height

        self.SetMinSize(wx.Size(-1, panel_height))
        self.Layout()

    # -----------------------------------------------------------------------

    def __seconds_label(self, value):
        return "{:.3f}".format(value)

# ----------------------------------------------------------------------------
# Panel for tests
# ----------------------------------------------------------------------------


class TestPanel(wx.Panel):

    def __init__(self, parent):
        super(TestPanel, self).__init__(
            parent,
            name="Time Slider Panel")
        self.SetMinSize(wx.Size(320, 20))

        btn2 = ToggleTextButton(self, label="Show/Hide ruler")
        btn2.SetMinSize(wx.Size(120, 32))
        btn2.SetValue(True)

        p1 = TimeSliderPanel(self, name="tsp1")
        p1.set_duration(12.123456)
        p1.set_selection_range(5.567, 6.87)
        p1.set_visible_range(3.45, 7.08765)
        p1.set_value(6.)
        p1.show_range(True)
        p1.show_rule(True)

        p2 = TimeSliderPanel(self, name="tsp2")
        p2.show_range(False)
        p2.show_rule(True)
        p2.SetBackgroundColour(wx.WHITE)

        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(btn2, 0, wx.ALL, 4)
        s.Add(p1, 0, wx.EXPAND | wx.BOTTOM, 20)
        s.Add(p2, 0, wx.EXPAND | wx.BOTTOM)
        self.SetSizer(s)

        self.Bind(MediaEvents.EVT_MEDIA_PERIOD, self._on_period_changed)
        self.Bind(sppasEVT_SLIDER, self._on_slider)
        btn2.Bind(wx.EVT_TOGGLEBUTTON, self._on_show_ruler)
        self.Layout()

    def _on_period_changed(self, event):
        p = event.period
        wx.LogDebug("Slider range from {} to {}".format(p[0], p[1]))

    def _on_show_ruler(self, evt):
        self.FindWindow("tsp1").show_rule(evt.GetEventObject().GetValue())
        self.Layout()

    def _on_slider(self, event):
        wx.LogDebug("Slider action={}, value={}".format(event.action, event.value))
