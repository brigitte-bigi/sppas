# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.wxapp.page_editor.timeline.videovista.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  Video viewer in a timeline.

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

import wx

from sppas.ui import _
from sppas.ui.wxapp.windows.panels import sppasPanel

from ..datactrls.filmctrl import SppasFilmWindow
from ..datactrls.videodatavalues import VideoDataValues

# ---------------------------------------------------------------------------


MSG_INFOS_LABEL = _("{fps:.3f}fps, {seconds:.3f}s, {width:d}×{height:d}px")
MSG_NO_VIDEO_AVAILABLE_LABEL = _("No video available")

# ---------------------------------------------------------------------------


class sppasVideoVista(sppasPanel):
    """Create a panel to display a summary of a video.

    Events emitted by this class:

        - MediaEvents.MediaActionEvent

    """

    # -----------------------------------------------------------------------
    # This object size.
    # By default, it is a DFHD aspect ratio (super ultra-wide displays) 32:9
    MIN_WIDTH = 178
    MIN_HEIGHT = 50

    # -----------------------------------------------------------------------
    # Default height of each element of this control
    INFOS_HEIGHT = 20
    FILM_HEIGHT = 20

    # -----------------------------------------------------------------------

    def __init__(self,
                 parent: wx.Window,
                 id: int = wx.ID_ANY,
                 pos: wx.Position = wx.DefaultPosition,
                 name: str = "videovista_panel"):
        """Create an instance of sppasVideoVista.

        :param parent: (wx.Window) parent window. Must not be None;
        :param id: (int) window identifier. -1 indicates a default value;
        :param pos: the control position. (-1, -1) indicates a default
        position, chosen by either the windowing system or wxPython,
        depending on platform;
        :param name: (str) Name of the media panel.

        """
        super(sppasVideoVista, self).__init__(parent=parent,
                                              id=id,
                                              pos=pos,
                                              size=wx.Size(sppasVideoVista.MIN_WIDTH, sppasVideoVista.MIN_HEIGHT),
                                              style=wx.BORDER_NONE | wx.TRANSPARENT_WINDOW | wx.TAB_TRAVERSAL |
                                              wx.WANTS_CHARS | wx.FULL_REPAINT_ON_RESIZE,
                                              name=name)

        # All possible views
        self.__infos = None
        self.__film = None

        # Zoom level
        self._zoom = 100

        self._create_content()

    # -----------------------------------------------------------------------

    def set_visible_period(self, start: float, end: float) -> None:
        """Set a time period to draw the content and lay out the video film.

        :param start: (float) start time in seconds.
        :param end: (float) end time in seconds.

        """
        changed = self.__film.set_visible_period(start=start, end=end)
        if changed is True and self.__film.IsShown() is True:
            self.__film.Refresh()

    # -----------------------------------------------------------------------

    def set_sel_frames_period(self, start: float, end: float) -> None:
        """Set a period of time to highlight and lay out the video film.

        :param start: (float) start time in seconds.
        :param end: (float) end time in seconds.

        """
        self.__film.set_sel_frames_period(start=start, end=end)
        if self.__film.IsShown():
            # self.__film.Layout()
            self.__film.Refresh()

    # -----------------------------------------------------------------------

    def UpdateVideoInfos(self, video_data: VideoDataValues) -> None:
        video_prop = MSG_INFOS_LABEL.format(fps=video_data.framerate,
                                            seconds=video_data.duration,
                                            width=video_data.width,
                                            height=video_data.height)

        self.__infos.SetLabel(video_prop)
        self.__infos.Refresh()
        self.__film.set_video_data(video_data)
        self.__film.Refresh()

    # -----------------------------------------------------------------------
    # Enable/Disable views
    # -----------------------------------------------------------------------

    def show_infos(self, value) -> None:
        """Show or hide the video infos.

        Can't be disabled if the video failed to be loaded.

        `value`'s negation will be used to show or hide the film.

        :param value: whether to show infos (bool)

        """
        if self.__infos is None:
            return
        value = bool(value)
        self.__infos.Show(value)
        self.__film.Show(not value)
        self.SetMinSize(wx.Size(-1, self.get_min_height()))

    # -----------------------------------------------------------------------

    def show_film(self, value) -> None:
        """Show or hide the film, a sequence of pictures of the video.

        `value`'s negation will be used to show or hide the info panel.

        :param value: (bool) whether to show the film

        """
        value = bool(value)
        self.__film.Show(value)
        self.__infos.Show(not value)
        self.SetMinSize(wx.Size(-1, self.get_min_height()))

    # -----------------------------------------------------------------------

    def infos_shown(self):
        return self.__infos.IsShown()

    # -----------------------------------------------------------------------
    # Height of the views
    # -----------------------------------------------------------------------

    def get_infos_height(self) -> int:
        """Return the height required to draw the video information."""
        h = int(float(sppasVideoVista.INFOS_HEIGHT) * float(self._zoom) / 100.)
        try:
            # Adjust proportionally to the font size
            h = sppasPanel.fix_size(h)
        except AttributeError:
            pass
        return h

    # -----------------------------------------------------------------------

    def get_film_height(self) -> int:
        """Return the height required to draw the film."""
        h = int(float(sppasVideoVista.FILM_HEIGHT) * float(self._zoom) / 100.)
        try:
            h = sppasPanel.fix_size(h)
        except AttributeError:
            pass
        return h

    # -----------------------------------------------------------------------

    def get_min_height(self) -> int:
        """Return the min height required to draw all views."""
        h = 0
        if self.__infos is not None:
            if self.__infos.IsShown():
                h += self.get_infos_height()
        if self.__film is not None:
            if self.__film.IsShown():
                h += self.get_film_height()

        return h

    # -----------------------------------------------------------------------

    def get_zoom(self) -> int:
        """Return the current zoom percentage value."""
        return self._zoom

    # -----------------------------------------------------------------------

    def set_zoom(self, value) -> None:
        """Fix the zoom percentage value.

        This coefficient is applied to the min size of each view panel.

        :param value: (int) Percentage of zooming, in range 25 .. 400.

        """
        value = float(value)
        if value < 25:
            value = 25
        if value > 400:
            value = 400

        self._zoom = value

        if self.__infos is not None:
            self.__infos.SetMinSize(wx.Size(width=-1, height=self.get_infos_height()))
        if self.__film is not None:
            self.__film.SetMinSize(wx.Size(width=-1, height=self.get_film_height()))

        self.SetMinSize(wx.Size(width=-1, height=self.get_min_height()))
        self.SendSizeEventToParent()

    # -----------------------------------------------------------------------
    # Create the panel content
    # -----------------------------------------------------------------------

    def _create_content(self) -> None:
        """Construct our panel, made only of an info panel and a film."""
        s = wx.BoxSizer(wx.VERTICAL)
        self.__infos = self.__create_infos_panel()
        self.__film = self.__create_film_panel()
        s.Add(self.__infos, 0, wx.EXPAND, border=0)
        s.Add(self.__film, 0, wx.EXPAND, border=0)
        self.SetSizerAndFit(s)
        self.SetAutoLayout(True)
        self.SetMinSize(wx.Size(width=-1, height=self.get_min_height()))

    # -----------------------------------------------------------------------

    def __create_infos_panel(self) -> wx.StaticText:
        st = wx.StaticText(parent=self, id=-1, label=MSG_NO_VIDEO_AVAILABLE_LABEL, name="infos_panel")
        st.SetMinSize(wx.Size(width=-1, height=self.get_infos_height()))
        return st

    # -----------------------------------------------------------------------

    def __create_film_panel(self) -> SppasFilmWindow:
        wp = SppasFilmWindow(self)
        wp.SetMinSize(wx.Size(width=-1, height=self.get_film_height()))
        return wp

# ---------------------------------------------------------------------------


class TestPanel(wx.Panel):

    def __init__(self, parent: wx.Window):
        super(TestPanel, self).__init__(
            parent, -1, style=wx.TAB_TRAVERSAL | wx.CLIP_CHILDREN, name="VideoVista Panel")

        btn5 = wx.Button(self, -1, "Zoom in")
        self.Bind(wx.EVT_BUTTON, self._on_zoom_in, btn5)
        btn6 = wx.Button(self, -1, "Zoom 100%")
        self.Bind(wx.EVT_BUTTON, self._on_zoom, btn6)
        btn7 = wx.Button(self, -1, "Zoom out")
        self.Bind(wx.EVT_BUTTON, self._on_zoom_out, btn7)

        self.ap = sppasVideoVista(self)

        sp = wx.BoxSizer()
        sp.Add(btn5, 0, wx.ALL, 4)
        sp.Add(btn6, 0, wx.ALL, 4)
        sp.Add(btn7, 0, wx.ALL, 4)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sp, 0, wx.EXPAND, 4)
        sizer.Add(self.ap, 0, wx.EXPAND)
        self.SetSizer(sizer)

    # ----------------------------------------------------------------------

    # noinspection PyUnusedLocal
    def _on_zoom_in(self, evt):
        zoom = self.ap.get_zoom()
        zoom *= 1.25
        self.ap.set_zoom(zoom)

    # ----------------------------------------------------------------------

    # noinspection PyUnusedLocal
    def _on_zoom_out(self, evt):
        zoom = self.ap.get_zoom()
        zoom *= 0.75
        self.ap.set_zoom(zoom)

    # ----------------------------------------------------------------------

    # noinspection PyUnusedLocal
    def _on_zoom(self, evt):
        self.ap.set_zoom(100.)
