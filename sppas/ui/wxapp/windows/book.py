# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.wxapp.windows.book.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  Custom books.

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

# ---------------------------------------------------------------------------


class sppasChoicebook(wx.Choicebook):
    """A notebook is a control, which manages multiple pages with tabs.

    Possible constructors:
        - sppasNotebook()
        - sppasNotebook(parent, id=ID_ANY, pos=DefaultPosition,
            size=DefaultSize, style=0, name=NotebookNameStr)

    """

    def __init__(self, *args, **kw):
        super(sppasChoicebook, self).__init__(*args, **kw)
        try:
            s = wx.GetApp().settings
            self.SetBackgroundColour(s.bg_color)
            self.SetForegroundColour(s.fg_color)
            self.SetFont(s.text_font)
        except AttributeError:
            self.InheritAttributes()

    # -----------------------------------------------------------------------

    def SetBackgroundColour(self, colour):
        """Override."""
        wx.Choicebook.SetBackgroundColour(self, colour)
        for i in range(self.GetPageCount()):
            page = self.GetPage(i)
            page.SetBackgroundColour(colour)

    # -----------------------------------------------------------------------

    def SetForegroundColour(self, colour):
        """Override."""
        wx.Choicebook.SetForegroundColour(self, colour)
        for i in range(self.GetPageCount()):
            page = self.GetPage(i)
            page.SetForegroundColour(colour)

    # -----------------------------------------------------------------------

    def SetFont(self, font):
        """Override."""
        wx.Choicebook.SetFont(self, font)
        for i in range(self.GetPageCount()):
            page = self.GetPage(i)
            page.SetFont(font)

# ---------------------------------------------------------------------------


class sppasNotebook(wx.Notebook):
    """A notebook is a control, which manages multiple pages with tabs.

    Possible constructors:
        - sppasNotebook()
        - sppasNotebook(parent, id=ID_ANY, pos=DefaultPosition,
            size=DefaultSize, style=0, name=NotebookNameStr)

    """

    def __init__(self, *args, **kw):
        super(sppasNotebook, self).__init__(*args, **kw)
        try:
            s = wx.GetApp().settings
            self.SetBackgroundColour(s.bg_color)
            self.SetForegroundColour(s.fg_color)
            self.SetFont(s.text_font)
        except AttributeError:
            self.InheritAttributes()

    # -----------------------------------------------------------------------

    def SetBackgroundColour(self, colour):
        """Override."""
        wx.Notebook.SetBackgroundColour(self, colour)
        for i in range(self.GetPageCount()):
            page = self.GetPage(i)
            page.SetBackgroundColour(colour)

    # -----------------------------------------------------------------------

    def SetForegroundColour(self, colour):
        """Override."""
        wx.Notebook.SetForegroundColour(self, colour)
        for i in range(self.GetPageCount()):
            page = self.GetPage(i)
            page.SetForegroundColour(colour)

    # -----------------------------------------------------------------------

    def SetFont(self, font):
        """Override."""
        wx.Notebook.SetFont(self, font)
        for i in range(self.GetPageCount()):
            page = self.GetPage(i)
            page.SetFont(font)


# ---------------------------------------------------------------------------


class sppasSimplebook(wx.Simplebook):
    """A simple is a control, which manages multiple pages.

    It is showing exactly one of its several pages.

    Possible constructors:
        - sppasSimplebook()
        - sppasSimplebook(parent, id=ID_ANY, pos=DefaultPosition,
            size=DefaultSize, style=0, name=NotebookNameStr)

    Possible effects:
        - wx.SHOW_EFFECT_NONE 	No effect.
        - wx.SHOW_EFFECT_ROLL_TO_LEFT 	Roll window to the left.
        - wx.SHOW_EFFECT_ROLL_TO_RIGHT 	Roll window to the right.
        - wx.SHOW_EFFECT_ROLL_TO_TOP 	Roll window to the top.
        - wx.SHOW_EFFECT_ROLL_TO_BOTTOM 	Roll window to the bottom.
        - wx.SHOW_EFFECT_SLIDE_TO_LEFT 	Slide window to the left.
        - wx.SHOW_EFFECT_SLIDE_TO_RIGHT 	Slide window to the right.
        - wx.SHOW_EFFECT_SLIDE_TO_TOP 	Slide window to the top.
        - wx.SHOW_EFFECT_SLIDE_TO_BOTTOM 	Slide window to the bottom.
        - wx.SHOW_EFFECT_BLEND 	Fade in or out effect.
        - wx.SHOW_EFFECT_EXPAND 	Expanding or collapsing effect.
        - wx.SHOW_EFFECT_MAX

    >>> n = sppasSimplebook()
    >>> n.ShowNewPage(page)

    """

    def __init__(self, *args, **kw):
        super(sppasSimplebook, self).__init__(*args, **kw)
        try:
            s = wx.GetApp().settings
            self.SetBackgroundColour(s.bg_color)
            self.SetForegroundColour(s.fg_color)
            self.SetFont(s.text_font)
        except AttributeError:
            self.InheritAttributes()

    # -----------------------------------------------------------------------

    def SetBackgroundColour(self, colour):
        """Override."""
        wx.Simplebook.SetBackgroundColour(self, colour)
        for i in range(self.GetPageCount()):
            page = self.GetPage(i)
            page.SetBackgroundColour(colour)

    # -----------------------------------------------------------------------

    def SetForegroundColour(self, colour):
        """Override."""
        wx.Simplebook.SetForegroundColour(self, colour)
        for i in range(self.GetPageCount()):
            page = self.GetPage(i)
            page.SetForegroundColour(colour)

    # -----------------------------------------------------------------------

    def SetFont(self, font):
        """Override."""
        wx.Simplebook.SetFont(self, font)
        for i in range(self.GetPageCount()):
            page = self.GetPage(i)
            page.SetFont(font)
