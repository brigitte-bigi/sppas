"""
:filename: sppas.ui.wxapp.page_editor.timeline.trsvista.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  Timeline view of a transcription

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

import os
import wx
import wx.lib.newevent

from sppas.core.config import paths
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasTranscription

from sppas.ui.wxapp.windows.panels import sppasPanel
from sppas.ui.wxapp.windows.panels import sppasScrolledPanel
from sppas.ui.wxapp.windows.popup import PopupCheckBox

from ..datactrls.layerctrl import sppasTierWindow
from ..datactrls.layerctrl import EVT_TIER

# ---------------------------------------------------------------------------


TrsEvent, EVT_TRS = wx.lib.newevent.NewEvent()
TrsCommandEvent, EVT_TRS_COMMAND = wx.lib.newevent.NewCommandEvent()


# Height of a tier with the default zoom level (100%)
# and the default font size (10).
TIER_HEIGHT = 20

# ---------------------------------------------------------------------------


class TranscriptionVista(sppasPanel):
    """Display a transcription in a timeline view.

    Only one tier must be selected at a time and only one annotation can be
    selected in the selected tier.

    Event emitted by this class is TRS_EVENT with:

        - action="tier_selected", value=name of the tier to be selected

    Do not bind TRS_EVENT event from the TierWindow:
    tier_selected, ann_update, ann_create, selected_point_update

    """

    def __init__(self, parent, name="trsvista_panel"):
        super(TranscriptionVista, self).__init__(parent, name=name)
        # The sppasTranscription() to be represented
        self.__trs = None

        # Create the view content
        self._zoom = 100
        self._create_content()

        # Associate a popup to display the filename
        self._check_popup = PopupCheckBox(self.GetTopLevelParent(), choices=list())
        self._check_popup.Bind(wx.EVT_MOUSE_EVENTS, self._check_popup_mouse_event)
        self._check_popup.Bind(wx.EVT_CHECKBOX, self._checked_popup_mouse_event)

        # A menu is shown on right-click to check the tiers to be displayed
        self.Bind(wx.EVT_CONTEXT_MENU, self._on_context_menu)

        # Events related to the embedded transcription
        self.Bind(EVT_TIER, self.__process_tier_event)

    # -----------------------------------------------------------------------

    def __process_tier_event(self, event):
        """Process an event from the embedded tier.

        This is a solution to convert the EVT_TIER received from a
        sppasTierWindow into an EVT_TRS.

        :param event: (wx.Event)

        """
        self.notify(action=event.action, value=event.value)

    # -----------------------------------------------------------------------

    def SetFont(self, font):
        """Override to keep the tier height proportional."""
        wx.Panel.SetFont(self, font)
        for tier_ctrl in self.GetChildren():
            tier_ctrl.SetFont(font)
            tier_ctrl.SetMinSize(wx.Size(-1, self.get_font_height() * 2))
        self.Layout()

    # -----------------------------------------------------------------------

    def set_transcription(self, transcription):
        """Fix the transcription object if it wasn't done when init.

        """
        if self.__trs is not None:
            raise Exception("A sppasTranscription is already defined.")

        if isinstance(transcription, sppasTranscription):
            self.__trs = transcription
            for tier in self.__trs:
                self._add_tier_to_panel(tier)

            self.SetMinSize(wx.Size(-1, len(self.__trs) * self.get_font_height() * 2))

    # -----------------------------------------------------------------------

    def write_transcription(self, parser):
        """Write the transcription object with the given parser.

        :param parser: (sppasRW)

        """
        parser.write(self.__trs)

    # -----------------------------------------------------------------------

    def get_duration(self):
        """Return the duration of the transcription."""
        if self.__trs is not None:
            max_point = self.__trs.get_max_loc()
            if max_point is not None:
                midpoint = max_point.get_midpoint()
                radius = max_point.get_radius()
                if radius is None:
                    return midpoint
                else:
                    return midpoint + radius

        return 0.

    # -----------------------------------------------------------------------

    def set_visible_period(self, start, end):
        """Period to display (in seconds)."""
        for child in self.GetChildren():
            changed = child.set_visible_period(start, end)
            if changed and child.IsShown():
                child.Refresh()

    # -----------------------------------------------------------------------

    def set_selection_period(self, start, end):
        raise NotImplementedError

    # -----------------------------------------------------------------------

    def get_selected_tiername(self):
        for child in self.GetChildren():
            if child.is_selected() is True:
                return child.get_tiername()
        return None

    # -----------------------------------------------------------------------

    def get_selected_tier(self):
        for child in self.GetChildren():
            if child.is_selected() is True:
                return child.get_tier()
        return None

    # -----------------------------------------------------------------------

    def set_selected_tiername(self, tier_name=None):
        """Set the selected tier.

        :param tier_name: (str)

        """
        if self.__trs is None:
            return

        if tier_name is not None:
            if tier_name not in [t.get_name() for t in self.__trs]:
                wx.LogError("Tier {:s} can't be selected: it is not in the "
                            "transcription.".format(tier_name))
                return

        for child in self.GetChildren():
            if child.is_selected() is True:
                child.set_selected(False)
                child.Refresh()
            if child.get_tiername() == tier_name:
                child.set_selected(True)
                child.Refresh()

    # -----------------------------------------------------------------------

    def get_tier_list(self):
        """Return the list of tiers."""
        if self.__trs is not None:
            return self.__trs.get_tier_list()
        return list()

    # -----------------------------------------------------------------------

    def get_selected_localization(self):
        """Return begin and end time value (float) rounded to milliseconds."""
        for child in self.GetChildren():
            if child.is_selected() is True:
                return child.get_selected_localization()

        return 0., 0.

    # -----------------------------------------------------------------------

    def get_selected_ann(self):
        """Return the index of the currently selected annotation or -1."""
        for child in self.GetChildren():
            if child.is_selected() is True:
                return child.get_selected_ann()

        return -1

    # -----------------------------------------------------------------------

    def set_selected_ann(self, idx):
        """An annotation was selected.

        Changing the selected annotation could also invalidate the
        selected point.

        """
        for child in self.GetChildren():
            if child.is_selected() is True:
                child.set_selected_ann(idx)

    # -----------------------------------------------------------------------

    def update_ann(self, idx):
        """An annotation was modified."""
        for child in self.GetChildren():
            if child.is_selected() is True:
                # Update the selected tier: no need to update the others.
                child.update_ann(idx)

    # -----------------------------------------------------------------------

    def update_selected_point(self, point):
        """The selected point was modified elsewhere.

        Changing the selected point could also change the selected
        annotation.

        """
        for child in self.GetChildren():
            if child.is_selected() is True:
                # Update the selected tier: no need to update the others.
                child.set_selected_point(point)

    # -----------------------------------------------------------------------

    def delete_ann(self, idx):
        """An annotation was deleted.

        If the idx was the selected ann, there's no remaining selected
        annotation after delete.

        """
        for child in self.GetChildren():
            if child.is_selected() is True:
                child.delete_ann(idx)

    # -----------------------------------------------------------------------

    def create_ann(self, idx):
        """An annotation was created. """
        for child in self.GetChildren():
            if child.is_selected() is True:
                child.create_ann(idx)

    # -----------------------------------------------------------------------

    def get_selected_point(self):
        """Return a copy of the currently selected point or None."""
        for child in self.GetChildren():
            if child.is_selected() is True:
                return child.get_selected_point()
        return None

    # -----------------------------------------------------------------------
    # Construct the GUI
    # -----------------------------------------------------------------------

    def show_tier_infos(self, value, tiername=None):
        """Show information about a tier instead or the annotations.

        :param value: (bool) True to show the information, False for the annotations.
        :param tiername: (str) Name of a tier or None for all tiers

        """
        if self.__trs is None:
            return
        for child in self.GetChildren():
            if tiername is None or tiername == child.get_tiername():
                child.show_infos(value)
                child.Refresh()

    # -----------------------------------------------------------------------

    def get_tier_height(self) -> int:
        """Return the height required to draw the film."""
        try:
            h = int(float(sppasPanel.fix_size(TIER_HEIGHT)) * float(self._zoom) / 100.)
        except AttributeError:
            h = int(float(TIER_HEIGHT) * float(self._zoom) / 100.)
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
        value = int(value)
        if value < 25:
            value = 25
        if value > 400:
            value = 400

        self._zoom = value
        tier_height = self.get_tier_height()
        min_height = tier_height
        for child in self.GetChildren():
            child.SetMinSize(wx.Size(width=-1, height=tier_height))
        self.SetMinSize(wx.Size(-1, max(min_height, tier_height)))

    # ------------------------------------------------------------------------

    def update_with_checked_tier(self):
        # Get the name of the checked tiers in the popup check box
        checked_tier_idx = self._check_popup.checkbox.GetSelection()
        wx.LogDebug("Checked choices: {}".format(checked_tier_idx))
        tier_height = self.get_tier_height()

        # Show/Hide tiers
        nb = 0
        for i, child in enumerate(self.GetChildren()):
            child.SetMinSize(wx.Size(width=-1, height=tier_height))
            if i in checked_tier_idx and self._check_popup.checkbox.IsItemEnabled(i):
                nb += 1
                child.Show()
            else:
                child.Hide()
        # Resize
        self.SetMinSize(wx.Size(-1, max(nb * tier_height, tier_height)))
        self.notify(action="size")

    # -----------------------------------------------------------------------
    # Construct the UI
    # -----------------------------------------------------------------------

    def _create_content(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

    # -----------------------------------------------------------------------

    def _add_tier_to_panel(self, tier):
        fg = self.GetForegroundColour()
        tier.set_meta("private_fg_color_r", str(fg.GetRed()))
        tier.set_meta("private_fg_color_g", str(fg.GetGreen()))
        tier.set_meta("private_fg_color_b", str(fg.GetBlue()))
        bg = self.GetBackgroundColour()
        tier.set_meta("private_bg_color_r", str(bg.GetRed()))
        tier.set_meta("private_bg_color_g", str(bg.GetGreen()))
        tier.set_meta("private_bg_color_b", str(bg.GetBlue()))

        tier_ctrl = sppasTierWindow(self, tier=tier)
        tier_ctrl.SetMinSize(wx.Size(-1, self.get_tier_height()))
        tier_ctrl.Bind(wx.EVT_COMMAND_LEFT_CLICK, self._process_tier_selected)
        i = self._check_popup.checkbox.Append(tier.get_name())
        self._check_popup.checkbox.SetSelection(i)

        self.GetSizer().Add(tier_ctrl, 0, wx.EXPAND, 0)

    # -----------------------------------------------------------------------
    # Events
    # -----------------------------------------------------------------------

    def notify(self, action, value=None):
        """Send a EVT_TRS event to the listener (if any)."""
        evt = TrsEvent(action=action, value=value)
        evt.SetEventObject(self)
        wx.PostEvent(self.GetParent(), evt)

    # -----------------------------------------------------------------------

    def _process_tier_selected(self, event):
        """Process a click on a tier or an annotation of a tier.

        :param event: (wx.Event)

        """
        # Which tier was clicked?
        tierctrl_click = event.GetEventObject()

        # Do not accept that a tier decides by its own to deselect
        if tierctrl_click.is_selected() is False:
            tierctrl_click.set_selected(True)

        # Update selection: disable any other selected tier. It has to be done
        # whether the clicked tier was already selected or not, otherwise two
        # of them are selected at the same time.
        for child in self.GetChildren():
            if child is not tierctrl_click and child.is_selected() is True:
                child.set_selected(False)
                child.Refresh()

        self.notify(action="tier_selected", value=tierctrl_click.get_tiername())

    # -----------------------------------------------------------------------

    def _on_context_menu(self, event):
        """Show menu to check the tiers to be displayed.

        """
        mx, my = wx.GetMousePosition()
        # we need to put the mouse inside the popup
        cx = mx - sppasPanel.fix_size(10)

        # The parent of the popup is the top-level window so does it's position
        w, h = self._check_popup.checkbox.DoGetBestSize()
        self._check_popup.SetPosition(wx.Point(cx, my - (h // 2)))
        self._check_popup.SetSize(wx.Size(sppasPanel.fix_size(150), h))

        # Show the popup window
        self._check_popup.Layout()
        self._check_popup.Show()
        self._check_popup.SetFocus()
        self._check_popup.Raise()

    # ------------------------------------------------------------------------

    def _check_popup_mouse_event(self, event):
        """Mouse action on the menu to check the tiers to be displayed.

        """
        if event.Leaving():
            # Mouse went out, don't show the menu anymore
            self._check_popup.Hide()
            self.update_with_checked_tier()

    # ------------------------------------------------------------------------

    def _checked_popup_mouse_event(self, event):
        """Mouse action on the menu to check the tiers to be displayed.

        """
        self.update_with_checked_tier()

# ---------------------------------------------------------------------------


class TestPanel(sppasScrolledPanel):

    def __init__(self, parent):
        super(TestPanel, self).__init__(parent, name="TrsVista Panel")

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        f1 = os.path.join(paths.samples, "annotation-results", "samples-fra", "F_F_B003-P9-palign.xra")
        trs1 = sppasTrsRW(f1).read()
        p1 = TranscriptionVista(self, name="p1")
        p1.SetPosition(wx.Point(10, 10))
        p1.SetSize(wx.Size(600, 80))
        p1.set_transcription(trs1)
        sizer.Add(p1, 0, wx.EXPAND)

        f2 = os.path.join(paths.samples, "annotation-results", "samples-fra", "F_F_B003-P8-palign.xra")
        trs2 = sppasTrsRW(f2).read()
        p2 = TranscriptionVista(self, name="p2")
        p2.SetPosition(wx.Point(10, 10))
        p2.set_zoom(200)
        p2.set_transcription(trs2)
        sizer.Add(p2, 0, wx.EXPAND)

        self.SetSizer(sizer)
