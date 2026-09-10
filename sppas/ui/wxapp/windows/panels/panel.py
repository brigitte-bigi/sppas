"""
:filename: sppas.ui.wxapp.windows.panels.panel.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: A panel is a window on which controls are placed.

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

Panels of SPPAS allow to propagate properly fonts and colors defined in the
settings.

"""

import wx
import wx.lib.scrolledpanel as sc

# ---------------------------------------------------------------------------


class sppasPanel(wx.Panel):
    """A panel with colors and fonts defined in the settings.

    Possible constructors:

        - sppasPanel(parent, id=ID_ANY, pos=DefaultPosition, size=DefaultSize,
              style=TAB_TRAVERSAL, name=PanelNameStr)

    """

    def __init__(self, parent, id=-1,
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=0, name="sppas_panel"):
        # always turn on tab traversal
        style |= wx.TAB_TRAVERSAL

        # and turn off the border, but only if none was asked: a child class
        # can ask for one, and it was the platform default until now
        if style & wx.BORDER_MASK == 0:
            style |= wx.BORDER_NONE

        super(sppasPanel, self).__init__(parent, id, pos, size, style, name)

        try:
            s = wx.GetApp().settings
            self.SetBackgroundColour(s.bg_color)
            self.SetForegroundColour(s.fg_color)
            self.SetFont(s.text_font)
        except AttributeError:
            self.InheritAttributes()

        self.SetAutoLayout(True)

    # -----------------------------------------------------------------------

    def ShouldInheritColours(self):
        try:
            wx.GetApp().settings
            return False
        except AttributeError:
            return True

    # -----------------------------------------------------------------------

    def InheritsBackgroundColour(self):
        try:
            wx.GetApp().settings
            return False
        except AttributeError:
            return True

    # -----------------------------------------------------------------------

    def InheritsForegroundColour(self):
        try:
            wx.GetApp().settings
            return False
        except AttributeError:
            return True

    # -----------------------------------------------------------------------

    def SetBackgroundColour(self, colour):
        """Override."""
        wx.Panel.SetBackgroundColour(self, colour)
        for c in self.GetChildren():
            c.SetBackgroundColour(colour)

    # -----------------------------------------------------------------------

    def SetForegroundColour(self, colour):
        """Override."""
        wx.Panel.SetForegroundColour(self, colour)
        for c in self.GetChildren():
            c.SetForegroundColour(colour)

    # -----------------------------------------------------------------------

    def SetFont(self, font):
        """Override."""
        wx.Panel.SetFont(self, font)
        for c in self.GetChildren():
            c.SetFont(font)
        self.Layout()

    # -----------------------------------------------------------------------

    @staticmethod
    def fix_size(value):
        """Return a proportional size value.

        :param value: (int)
        :returns: (int)

        """
        try:
            obj_size = int(float(value) * wx.GetApp().settings.size_coeff)
        except AttributeError:
            obj_size = int(value)
        return obj_size

    # -----------------------------------------------------------------------

    def get_font_height(self):
        """Return the height of the in-use font."""
        try:
            font = wx.GetApp().settings.text_font
        except AttributeError:
            font = self.GetFont()
        return int(float(font.GetPixelSize()[1]))

    # -----------------------------------------------------------------------

    def get_font_width(self):
        """Return the width of the in-use font."""
        try:
            font = wx.GetApp().settings.text_font
        except AttributeError:
            font = self.GetFont()
        return int(float(font.GetPixelSize()[0]))

# ---------------------------------------------------------------------------


class sppasTransparentPanel(sppasPanel):
    """Create a panel with a transparent background.

    """

    def __init__(self, parent, id=wx.ID_ANY,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=0,
                 name="transparent_panel"):
        # always turn on transparency
        style |= wx.TRANSPARENT_WINDOW

        super(sppasTransparentPanel, self).__init__(parent, id, pos, size, style, name)

        # Bind the events related to our window
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)

    # -----------------------------------------------------------------------

    def SetBackgroundColour(self, colour):
        return

    # -----------------------------------------------------------------------

    def OnEraseBackground(self, evt):
        """Trap the erase event to be transparent even under windows.

        :param evt: wx.EVT_ERASE_BACKGROUND

        """
        pass

# ---------------------------------------------------------------------------
# Panel to test
# ---------------------------------------------------------------------------


class TestPanel(sc.ScrolledPanel):

    def __init__(self, parent):
        super(TestPanel, self).__init__(
            parent,
            style=wx.BORDER_NONE | wx.WANTS_CHARS | wx.HSCROLL | wx.VSCROLL,
            name="Test Panels")

        p1 = sppasPanel(self)
        self.MakePanelContent(p1)

        p2 = sppasTransparentPanel(self)
        self.MakePanelContent(p2)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(p1, 0, wx.EXPAND)
        sizer.Add(p2, 0, wx.EXPAND)

        self.SetSizerAndFit(sizer)
        self.Layout()
        self.SetupScrolling(scroll_x=True, scroll_y=True)
        self.SetAutoLayout(True)
        self.Refresh()

        self.Bind(wx.EVT_SIZE, self.OnSize)

    def MakePanelContent(self, pane):
        """Just make a few controls to put on the collapsible pane."""
        nameLbl = wx.StaticText(pane, -1, "Name:")
        name = wx.TextCtrl(pane, -1, "")

        addrLbl = wx.StaticText(pane, -1, "Address:")
        addr1 = wx.TextCtrl(pane, -1, "")
        addr2 = wx.TextCtrl(pane, -1, "")

        cstLbl = wx.StaticText(pane, -1, "City, State, Zip:")
        city = wx.TextCtrl(pane, -1, "", size=(150, -1))
        state = wx.TextCtrl(pane, -1, "", size=(50, -1))
        zip = wx.TextCtrl(pane, -1, "", size=(70, -1))

        addrSizer = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        addrSizer.AddGrowableCol(1)
        addrSizer.Add(nameLbl, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        addrSizer.Add(name, 0, wx.EXPAND)
        addrSizer.Add(addrLbl, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        addrSizer.Add(addr1, 0, wx.EXPAND)
        addrSizer.Add((5, 5))
        addrSizer.Add(addr2, 0, wx.EXPAND)

        addrSizer.Add(cstLbl, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)

        cstSizer = wx.BoxSizer(wx.HORIZONTAL)
        cstSizer.Add(city, 1)
        cstSizer.Add(state, 0, wx.LEFT | wx.RIGHT, 5)
        cstSizer.Add(zip)
        addrSizer.Add(cstSizer, 0, wx.EXPAND)

        border = wx.BoxSizer()
        border.Add(addrSizer, 1, wx.EXPAND | wx.ALL, 5)
        pane.SetSizer(border)
        pane.Layout()

    def OnSize(self, evt):
        self.Layout()
