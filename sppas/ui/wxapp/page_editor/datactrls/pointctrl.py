# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.wxapp.page_editor.datactrls.pointctrl.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  Self-drawn control window to represent a point in a timeline

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

import enum
import wx
import wx.lib.newevent

from sppas.core.coreutils import sppasTypeError
from sppas.src.anndata import sppasPoint
from sppas.ui import _
from sppas.ui.wxapp.windows import sppasWindow, WindowState
from sppas.ui.wxapp.windows.cursors import sppasCursor

# ----------------------------------------------------------------------------
# Events
# ----------------------------------------------------------------------------


PointSelectedEvent, sppasEVT_POINT_SELECTED = wx.lib.newevent.NewEvent()
PointSelectedCommandEvent, sppasEVT_POINT_SELECTED_COMMAND = wx.lib.newevent.NewCommandEvent()

PointMovedEvent, sppasEVT_POINT_MOVED = wx.lib.newevent.NewEvent()
PointMovedCommandEvent, sppasEVT_POINT_MOVED_COMMAND = wx.lib.newevent.NewCommandEvent()

PointResizedEvent, sppasEVT_POINT_RESIZED = wx.lib.newevent.NewEvent()
PointResizedCommandEvent, sppasEVT_POINT_RESIZED_COMMAND = wx.lib.newevent.NewCommandEvent()

# ----------------------------------------------------------------------------
# Messages
# ----------------------------------------------------------------------------

MSG_SHORTCUT_CANCEL_DRAG = _("escape: cancel the current move or resize")

# ----------------------------------------------------------------------------
# Cursor pixmaps
# ----------------------------------------------------------------------------

cursor_move = [
"16 16 2 1",
" 	c None",
".	c #000000",
"       ..       ",
"       ..       ",
"       ..       ",
"       ..       ",
"   .   ..   .   ",
"  ..   ..   ..  ",
" ..... .. ..... ",
"...... .. ......",
"...... .. ......",
" ..... .. ..... ",
"  ..   ..   ..  ",
"   .   ..   .   ",
"       ..       ",
"       ..       ",
"       ..       ",
"       ..       "
]

cursor_expand = [
"16 16 2 1",
" 	c None",
".	c #000000",
"      .  .      ",
"      .  .      ",
"     ..  ..     ",
"    ...  ...    ",
"   ....  ....   ",
"  .....  .....  ",
" ......  ...... ",
".......  .......",
".......  .......",
" ......  ...... ",
"  .....  .....  ",
"   ....  ....   ",
"    ...  ...    ",
"     ..  ..     ",
"      .  .      ",
"      .  .      "
]

# ---------------------------------------------------------------------------


class sppasPointWindow(sppasWindow):
    """A window with a DC to draw a sppasPoint().

    A point can be left/right resized by dragging, i.e. only its width can be
    changed with the mouse.
    A point can be moved to left or right, i.e. only x-position can be changed
    by dragging with the mouse.

    """

    class DragType(enum.Enum):
        NONE = 0
        MOVE = 1
        SIZE = 2

    def __init__(self, parent, id=-1,
                 data=None,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 name="pointctrl"):
        """Initialize a new sppasPointWindow instance.

        :param parent: Parent window. Must not be None.
        :param id:     A value of -1 indicates a default value.
        :param data:   Data to draw.
        :param pos:    If the position (-1, -1) is specified
                       then a default position is chosen.
        :param size:   If the default size (-1, -1) is specified
                       then a default size is chosen.
        :param name:   Window name.

        """
        style = wx.BORDER_NONE | wx.WANTS_CHARS | wx.FULL_REPAINT_ON_RESIZE
        super(sppasPointWindow, self).__init__(parent, id, pos, size, style, name)

        # override base class members
        self._min_width = 3
        self._min_height = 4
        self._vert_border_width = 0
        self._horiz_border_width = 0
        self._focus_width = 0
        self._focus_spacing = 0

        # The sppasPoint() this window is representing
        self.__point = None

        # Allows to move/resize the PointCtrl
        self.__drag = sppasPointWindow.DragType.NONE
        self.__x_dragging = 0         # x position of drag
        self.__start_drag_x = 0       # x of this window before dragging
        self.__start_drag_w = 0       # w of this window before dragging
        self.__min_x = None           # to not allow to move before this x
        self.__max_x = None           # to not allow to move after this x

        # Cursors while moving or resizing
        self._cursor_move = sppasCursor(cursor_move, hotspot=8).create()
        self._cursor_size = sppasCursor(cursor_expand, hotspot=8).create()

        # size was fixed during the construction but we redefined min values
        self.SetSize(size)
        self.Bind(event=wx.EVT_KEY_DOWN, handler=self._process_key_down)

    # -----------------------------------------------------------------------
    # Data represented by this window
    # -----------------------------------------------------------------------

    def set_point(self, point):
        """Set the sppasPoint represented by this window.

        Does refresh.

        :param point: (sppasPoint)
        :raise: TypeError

        """
        if isinstance(point, sppasPoint):
            self.__point = point
            self.SetToolTip(wx.ToolTip(self._tooltip()))
            self.Refresh()
        else:
            raise sppasTypeError(point, "sppasPoint")

    # -----------------------------------------------------------------------

    def get_point(self):
        """Return the point represented by this window."""
        return self.__point

    # -----------------------------------------------------------------------

    def cancel_point(self):
        """Cancel the point represented by this window."""
        self.__point = None

    # -----------------------------------------------------------------------

    def get_midpoint(self):
        """Return the midpoint value of the point or None."""
        if self.__point is not None:
            return self.__point.get_midpoint()
        return None

    # -----------------------------------------------------------------------

    def drag_min_x(self, x_value):
        """Min x-position of the midpoint of this window when dragging.

         :param x_value: (int)

         """
        self.__min_x = x_value

    # -----------------------------------------------------------------------

    def drag_max_x(self, x_value):
        """Max x-position of the midpoint of this window when dragging.

         :param x_value: (int)

         """
        self.__max_x = x_value

    # -----------------------------------------------------------------------

    def is_dragging(self):
        """Return True of the point is currently dragging."""
        return self.__drag != sppasPointWindow.DragType.NONE

    # -----------------------------------------------------------------------
    # Draw the window
    # -----------------------------------------------------------------------

    def SetVertBorderWidth(self, value):
        """Override. UN-Set the width of the left/right borders.

        :param value: (int) Border size. Not applied if not appropriate.

        """
        return

    # -----------------------------------------------------------------------

    def SetHorizBorderWidth(self, value):
        """Override. UN-Set the width of the top/bottom borders.

        :param value: (int) Border size. Not applied if not appropriate.

        """
        return

    # -----------------------------------------------------------------------

    def DrawBackground(self, dc, gc):
        """Draw the background with a gradient color from midpoint."""
        w, h = self.GetClientSize()
        bg_color = self.GetPenBackgroundColour()
        brush = wx.Brush(bg_color, wx.BRUSHSTYLE_SOLID)
        if brush is not None:
            dc.SetBackground(brush)
            dc.Clear()
        dc.SetBrush(brush)

        if self.HasFocus() is False:
            c1 = self.GetPenForegroundColour()
            c2 = bg_color
        else:
            c1 = bg_color
            c2 = self.GetPenForegroundColour()

        if w > 7:
            # Fill in the content with a gradient color
            mid = w // 2
            box_rect = wx.Rect(0, 0, mid, h)
            dc.GradientFillLinear(box_rect, c1, c2, wx.EAST)
            box_rect = wx.Rect(mid, 0, mid, h)
            dc.GradientFillLinear(box_rect, c1, c2, wx.WEST)
        else:
            # Fill in the content with a solid color
            pen = wx.Pen(c1, 1, wx.PENSTYLE_SOLID)
            pen.SetCap(wx.CAP_BUTT)
            # pen.SetJoin(wx.JOIN_INVALID)  # not supported under Windows
            dc.SetPen(pen)
            for i in range(max(self._min_width, w)):
                dc.DrawLine(i, 0, i, h)

    # -----------------------------------------------------------------------

    def DrawContent(self, dc, gc):
        """Override. """
        # nothing to do... the point is represented only with a background.
        return

    # -----------------------------------------------------------------------

    def _tooltip(self):
        """Set a tooltip string with the midpoint and radius of the point."""
        if self.__point is not None:
            tooltip = "Midpoint: " + str(self.__point.get_midpoint())
            if self.__point.get_radius() is not None:
                tooltip += "\nRadius: " + str(self.__point.get_radius())
            return tooltip + "\n" + MSG_SHORTCUT_CANCEL_DRAG

        return ""

    # -----------------------------------------------------------------------

    def RestorePosition(self):
        """Set the position at the one of the beginning of the dragging."""
        _, y = self.GetPosition()
        if self.__start_drag_x is not None:
            self.SetPosition(wx.Point(self.__start_drag_x, y))

    # -----------------------------------------------------------------------

    def RestoreSize(self):
        """Set the size at the one of the beginning of the dragging."""
        _, h = self.GetSize()
        if self.__start_drag_w is not None:
            self.SetSize(wx.Size(self.__start_drag_w, h))

    # -----------------------------------------------------------------------
    # Events
    # -----------------------------------------------------------------------

    def OnMouseEnter(self, event):
        """Handle the wx.EVT_ENTER_WINDOW event: change state and cursor.

        :param event: a wx.MouseEvent event to be processed.

        """
        if self._state[1] == WindowState().normal:
            self._set_state(WindowState().focused)
            self.SetCursor(wx.Cursor(wx.CURSOR_HAND))

    # -----------------------------------------------------------------------

    def OnMouseLeave(self, event):
        """Handle the wx.EVT_LEAVE_WINDOW event.

        The mouse can be at left, at right, above or below this window.

        The mouse is leaving either while its button is pressed (the state
        is selected) or not (the state is focused). In both cases, we switch
        to normal state.

        :param event: a wx.MouseEvent event to be processed.

        """
        if self._state[1] != WindowState().disabled:
            # The window is not currently dragging.
            if self.__drag == sppasPointWindow.DragType.NONE:
                self._set_state(WindowState().normal)
                self.SetCursor(wx.NullCursor)

    # -----------------------------------------------------------------------

    def OnMouseLeftDown(self, event):
        """Handle the wx.EVT_LEFT_DOWN event.

        :param event: a wx.MouseEvent event to be processed.

        """
        if self.IsEnabled() is False:
            return

        # Direct all mouse inputs to this window
        self.CaptureMouse()
        self._set_state(WindowState().selected)

        x, _ = self.GetPosition()
        w, _ = self.GetSize()
        self.__start_drag_x = x    # current x of this window before dragging
        self.__start_drag_w = w    # current w of this window before dragging

    # -----------------------------------------------------------------------

    def OnMouseDragging(self, event):
        """Respond to mouse dragging event."""
        if self._state[1] == WindowState().selected:
            if self.__drag == sppasPointWindow.DragType.NONE:
                # first dragging event
                # relative position of the mouse in the window
                (ex, ey) = event.GetPosition()
                if event.ShiftDown() is True:
                    self.__start_drag(sppasPointWindow.DragType.SIZE, ex)
                else:
                    self.__start_drag(sppasPointWindow.DragType.MOVE, ex)

            if event.ShiftDown() is True:
                self.__on_drag_resize(event)
            else:
                self.__on_drag_move(event)

    # -----------------------------------------------------------------------

    def OnMouseLeftUp(self, event):
        """Handle the wx.EVT_LEFT_UP event.

        :param event: a wx.MouseEvent event to be processed.

        """
        if not self.IsEnabled():
            return

        # Mouse was down outside of the window (but is up inside)
        if not self.HasCapture():
            return

        # Directs all mouse input to this window
        self.ReleaseMouse()

        # If the button was down when the mouse was released...
        if self._state[1] == WindowState().selected:
            self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
            self._set_state(WindowState().selected)

            if self.__drag == sppasPointWindow.DragType.NONE:
                # no dragging was performed before left up -- clicked only
                evt = PointSelectedEvent()
                evt.SetEventObject(self)
                wx.PostEvent(self.GetParent(), evt)

            else:
                # some dragging was performed before left up. Notify the parent
                # and stop dragging the window.
                if self.__drag == sppasPointWindow.DragType.SIZE:
                    evt = PointResizedEvent(pos=self.GetPosition(), size=self.GetSize())
                else:
                    evt = PointMovedEvent(pos=self.GetPosition(), size=self.GetSize())
                evt.SetEventObject(self)
                wx.PostEvent(self.GetParent(), evt)
                self.__end_drag()

    # -----------------------------------------------------------------------

    def _process_key_down(self, event: wx.KeyEvent) -> None:
        # if the window is selected, is in a drag state and the key pressed is
        # "Escape", cancel dragging or resizing the selected point
        if self._state[1] == WindowState().selected \
                and self.__drag != sppasPointWindow.DragType.NONE \
                and event.GetKeyCode() == wx.WXK_ESCAPE:
            # switch-back to the initial position and size
            _, h = self.GetSize()
            _, y = self.GetPosition()
            self.SetPosition(wx.Point(self.__start_drag_x, y))
            self.SetSize(wx.Size(self.__start_drag_w, h))

            # stop dragging
            self.__end_drag()

            # set normal window state
            self._set_state(WindowState().normal)

            # set default cursor
            self.SetCursor(wx.NullCursor)

    # -----------------------------------------------------------------------
    # -- Private --
    # -----------------------------------------------------------------------

    def __on_drag_move(self, event):
        self.SetCursor(self._cursor_move)
        x, y = self.GetPosition()     # absolute
        ex, ey = event.GetPosition()  # relative
        w, h = self.GetSize()

        shift = x + ex - self.__x_dragging
        if shift != 0:
            self.__x_dragging = self.__x_dragging + shift
            # We can't shift out of the frame...
            if self.__min_x is None:
                xx = max(0 - (w//2), x + shift)
            else:
                xx = max(self.__min_x - (w//2), x + shift)
            if self.__max_x is None:
                win_w, win_h = self.GetTopLevelParent().GetSize()
                new_x = min(xx, win_w - (w//2))
            else:
                new_x = min(xx, self.__max_x - (w//2))
            #
            self.SetPosition(wx.Point(new_x, y))

    # -----------------------------------------------------------------------

    def __on_drag_resize(self, event):
        self.SetCursor(self._cursor_size)
        x, y = self.GetPosition()     # absolute
        ex, ey = event.GetPosition()  # relative
        w, h = self.GetSize()
        direction = 2  # must be an even number, not odd

        if (self.__x_dragging - x - ex) > 0:
            direction = -direction

        if direction > 0 or w > 2:
            shift = direction // 2
            if self.__min_x is None:
                xx = max(0, x - shift)
            else:
                xx = max(self.__min_x, x - shift)
            shift = x - xx

            self.__x_dragging = self.__x_dragging + shift
            p = wx.Point(xx, y)
            s = wx.Size(w + 2*shift, h)
            self.SetPosition(p)
            self.SetSize(s)

    # -----------------------------------------------------------------------

    def __start_drag(self, drag_type, drag_x):
        x, _ = self.GetPosition()
        self.__drag = drag_type
        self.__x_dragging = x + drag_x

    # -----------------------------------------------------------------------

    def __end_drag(self):
        self.__drag = sppasPointWindow.DragType.NONE
        self.__x_dragging = 0

# ----------------------------------------------------------------------------
# Panels to test
# ----------------------------------------------------------------------------


class TestPanel(wx.Panel):

    def __init__(self, parent):
        super(TestPanel, self).__init__(parent, style=wx.BORDER_NONE | wx.WANTS_CHARS, name="Test PointCtrl")

        p1 = sppasPointWindow(self, pos=(50, 50), size=(20, 100), name="p1")
        p1.drag_min_x(10)
        p1.drag_max_x(150)
        p2 = sppasPointWindow(self, pos=(150, 50), size=(5, 100), name="p2")
        p3 = sppasPointWindow(self, pos=(250, 50), size=(10, 100), name="p3")
        p3.set_point(sppasPoint(12., 0.02))
        p4 = sppasPointWindow(self, pos=(350, 50), size=(1, 100), name="p4")
        p4.set_point(sppasPoint(12))

        self.Bind(sppasEVT_POINT_SELECTED, self._process_selected)
        self.Bind(sppasEVT_POINT_MOVED, self._process_moved)
        self.Bind(sppasEVT_POINT_RESIZED, self._process_resized)

    # ----------------------------------------------------------------------------

    def _process_selected(self, event):
        pointctrl = event.GetEventObject()
        wx.LogMessage("The pointctrl {:s} was selected".format(pointctrl.GetName()))

    def _process_moved(self, event):
        pointctrl = event.GetEventObject()
        wx.LogMessage("The pointctrl {:s} was moved".format(pointctrl.GetName()))

    def _process_resized(self, event):
        pointctrl = event.GetEventObject()
        wx.LogMessage("The pointctrl {:s} was resized".format(pointctrl.GetName()))
