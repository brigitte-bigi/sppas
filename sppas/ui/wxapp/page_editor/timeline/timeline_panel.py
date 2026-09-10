# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.wxapp.page_editor.timeline.timeline_panel.py
:author:   Brigitte Bigi
:contact:  contact@sppas.org
:summary:  Main panel of the timeline view of files

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

import os
import wx

from sppas.core.config import paths  # only for the test
from sppas.core.coreutils import info
from sppas.core.coreutils import msg

from sppas.ui.wxapp.windows import sppasPanel
from sppas.ui.wxapp.windows import sppasScrolledPanel

from ..media import MediaEvents

from .rankfiles import sppasRankFilesDialog
from .timedatatype import TimelineType
from .smmpctrl_risepanel import SMMPCPanel
from .errorview_risepanel import ErrorViewPanel
from .trsview_risepanel import TrsViewPanel
from .audioview_risepanel import AudioViewPanel
from .videoview_risepanel import VideoViewPanel
from .timeevents import EVT_TIMELINE_VIEW, TimelineViewEvent

# ---------------------------------------------------------------------------
# List of displayed messages:


MSG_CLOSE = msg("Close", "ui")
MSG_UNKNOWN = msg("Unknown file format", "ui")

CLOSE_CONFIRM = info(9060, "ui")

# ----------------------------------------------------------------------------


class sppasTimelinePanel(sppasPanel):
    """Panel to display opened files and their content in a time-line style.

    The event emitted by this view is TimelineViewEvent with:

        - action="close" and filename to ask for closing the panel
        - action="save" and filename to ask for saving the file of the panel
        - action="collapsed" with the filename and value=the object
        - action="expanded" with the filename and value=the object

        - tier_selected is received and emitted

    """

    def __init__(self, parent, name="timeline_panel"):
        super(sppasTimelinePanel, self).__init__(
            parent,
            id=wx.ID_ANY,
            pos=wx.DefaultPosition,
            size=wx.DefaultSize,
            style=wx.BORDER_SIMPLE | wx.NO_FULL_REPAINT_ON_RESIZE,
            name=name)

        # To get easy access to the opened files and their panel
        # (key=filename, value=wx.SizerItem)
        self._files = dict()
        self._sel_file = None
        self._options = dict()
        self._options["video_max_width"] = 512

        # Create a scrolled panel and a multi-media player control system
        self._create_content()
        self._setup_events()

        # Colors and font
        try:
            self.SetBackgroundColour(wx.GetApp().settings.bg_color)
            self.SetForegroundColour(wx.GetApp().settings.fg_color)
            self.SetFont(wx.GetApp().settings.text_font)
        except AttributeError:
            self.InheritAttributes()

    # -----------------------------------------------------------------------

    def _setup_events(self):
        """Associate a handler function with the events.

        It means that when an event occurs then the process handler function
        will be called.

        Note that events of `VideoViewPanel`s have to be bind when they are
        created.

        """
        # Set up the events of our objects
        self.Bind(wx.EVT_BUTTON, self._process_tool_event)
        self.smmpc.Bind(wx.EVT_BUTTON, self._process_tool_event)
        self.smmpc.Bind(wx.EVT_TOGGLEBUTTON, self._process_tool_event)
        self._scrolled_panel.Bind(EVT_TIMELINE_VIEW, self._process_time_event)
        self.FindWindow("smmpc_risepanel").Bind(MediaEvents.EVT_MEDIA_LOADED, self.__on_media_loaded)
        self.FindWindow("smmpc_risepanel").Bind(MediaEvents.EVT_MEDIA_NOT_LOADED, self.__on_media_not_loaded)
        self.FindWindow("smmpc_risepanel").Bind(MediaEvents.EVT_MEDIA_ACTION, self._process_media_event)

        # Capture keys
        self.Bind(wx.EVT_CHAR_HOOK, self._process_key_event)

    # -----------------------------------------------------------------------
    # Options about the players
    # -----------------------------------------------------------------------

    def set_video_max_width(self, max_width=512):
        """Set the video max width.

        :param max_width: (int) a value in range [64, 4096]

        """
        mw = int(max_width)
        if mw < 64:
            mw = 64
        if mw > 4096:
            mw = 4096
        self._options["video_max_width"] = mw

    # -----------------------------------------------------------------------
    # Manage the set of files
    # -----------------------------------------------------------------------

    def get_files(self):
        """Return the list of filenames this panel is displaying.

        The files are in the displayed order, which is the one of the sizer of
        the scrolled panel. It is the order the user is seeing, and the one
        _sort_files() is changing.

        :return: (list of str)

        """
        files = list()
        for child in self._sizer.GetChildren():
            files.append(child.GetWindow().get_filename())
        return files

    # -----------------------------------------------------------------------

    def is_trs(self, name):
        """Return True if name is a transcription file."""
        if name not in self._files:
            return False
        return self._files[name].is_trs()

    # -----------------------------------------------------------------------

    def is_audio(self, name):
        """Return True if name is an audio file."""
        if name not in self._files:
            return False
        return self._files[name].is_audio()

    # -----------------------------------------------------------------------

    def is_video(self, name):
        """Return True if name is a video file."""
        if name not in self._files:
            return False
        return self._files[name].is_video()

    # -----------------------------------------------------------------------

    def is_error(self, name):
        """Return True if name is matching a non-opened file."""
        if name not in self._files:
            return False
        return self._files[name].is_unknown()

    # -----------------------------------------------------------------------

    def is_expanded(self, name):
        """Return True if the panel displaying the file is expanded."""
        if name not in self._files:
            return False
        return self._files[name].IsExpanded()

    # -----------------------------------------------------------------------

    def is_modified(self, name=None):
        """Return True if the content of the file has changed.

        :param name: (str) Name of a file or none for all files.

        """
        if name is not None:
            page = self._files.get(name, None)
            if page is None:
                # There's no file with this name: nothing was changed.
                return False
            return page.is_modified()

        # All files
        for page in self._files.values():
            if page.is_modified() is True:
                return True

        return False

    # -----------------------------------------------------------------------
    # Manage one file at a time
    # -----------------------------------------------------------------------

    def append_file(self, name):
        """Append a file and create a rise panel to display its content.

        Do not refresh/layout the GUI.

        If the file is a media, its panel will emit action "media_loaded" in
        an event that we'll capture and re-send to the parent.
        If the file is a trs, we'll emit the action "tiers_added" in an event.

        :param name: (str)
        :raise: ValueError

        """
        if name in self._files:
            wx.LogError("Name {:s} is already in the list of files.".format(name))
            return False

        else:
            # Create the appropriate XxxxViewPanel
            panel = self._create_panel(name)
            self._sizer.Add(panel, 0, wx.EXPAND | wx.BOTTOM, sppasPanel.fix_size(2))
            self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self._on_collapse_changed, panel)
            self.Layout()
            self._files[name] = panel

            # For transcription, each panel is managing the content of a file but
            # the SMMPC needs to know the duration of the transcription.
            if panel.is_trs():
                panel.load()
                panel.show_tier_infos(not self.smmpc.is_tiers_annotations())
                self.smmpc.add_unsupported(name, panel.get_duration())
                self.notify(action="tiers_added", filename=name, value=panel.get_tier_list())

                # If no visible part was defined, do it now! or update it.
                self.update_visible_range()
                s, e = self.smmpc.get_visible_range()
                panel.set_visible_period(s, e)
                # we must layout under Windows...
                panel.Layout()

            # For media, the SMMPC is managing all files.
            # It's easier to manage media files this way particularly
            # because we need to play synchronously...
            elif panel.is_audio():
                self.smmpc.add_audio(name)

            elif panel.is_video():
                self.smmpc.add_video(name, player=panel.video_frame)


            return True

    # -----------------------------------------------------------------------

    def remove_file(self, name, force=False):
        """Remove a panel corresponding to the name of a file.

        Do not refresh/layout the GUI.

        :param name: (str)
        :param force: (bool) Force to remove, even if a file is modified
        :return: (bool) The file was removed or not

        """
        if force is True or self.is_modified(name) is False:
            if name == self._sel_file:
                self._sel_file = None

            # Remove of the object
            panel = self._files.get(name, None)
            if panel is None:
                wx.LogError("There's no file with name {:s}".format(name))
                return False

            # this file must be removed of the multimedia player control.
            self.smmpc.remove_media(name)

            # Detach the panel of the sizer of the scrolled panel, then ask
            # for its destruction. It can't be destroyed now: this method is
            # invoked while the event its own close button emitted is still
            # being processed.
            self._sizer.Detach(panel)
            panel.DestroyLater()

            # Delete of the list
            self._files.pop(name)
            return True

        return False

    # -----------------------------------------------------------------------

    def save_file(self, name):
        """Save a file.

        :param name: (str)
        :return: (bool) The file was saved or not

        """
        panel = self._files.get(name, None)
        saved = False
        if panel.is_modified() is True:
            try:
                saved = panel.save()
                if saved is True:
                    wx.LogMessage("File {:s} saved successfully.".format(name))
            except Exception as e:
                saved = False
                wx.LogError("Error while saving file {:s}: {:s}"
                            "".format(name, str(e)))

        return saved

    # -----------------------------------------------------------------------
    # Methods to operate on a TrsViewPanel()
    # -----------------------------------------------------------------------

    def get_tier_list(self, name):
        """Return the list of sppasTier() of the given file.

        :param name: (str) Name of a file
        :return: (list)

        """
        if name not in self._files:
            return list()

        if self._files[name].is_trs() is True:
            return self._files[name].get_tier_list()

        return list()

    # -----------------------------------------------------------------------

    def get_selected_filename(self):
        """Return the filename of the currently selected tier."""
        return self._sel_file

    # -----------------------------------------------------------------------

    def get_selected_tiername(self):
        """Return the name of the currently selected tier."""
        if self._sel_file is not None:
            panel = self._files[self._sel_file]
            return panel.get_selected_tiername()

        return None

    # -----------------------------------------------------------------------

    def get_selected_tier(self):
        """Return the currently selected tier or None."""
        if self._sel_file is not None:
            panel = self._files[self._sel_file]
            return panel.get_selected_tier()

        return None

    # -----------------------------------------------------------------------

    def set_selected_tiername(self, filename, tier_name, ann_idx):
        """Change selected tier and scroll to the selected ann to center it.

        :param filename: (str) Name of a file
        :param tier_name: (str) Name of a tier
        :param ann_idx: (int) Index of the selected annotation in the tier
        :return: (bool)

        """
        updated = self.__set_selection(filename, tier_name, ann_idx)
        if updated is True:
            panel = self._files[self._sel_file]
            s, e = panel.get_selected_localization()
            self.smmpc.set_selection_range(s, e)
            # ensure (s,e) is visible in the timeline
            self.update_visible_range(s, e)

    # -----------------------------------------------------------------------

    def __set_selection(self, filename, tier_name, ann_idx):
        """Change selected tier."""
        updated = False
        point = None
        for fn in self._files:
            panel = self._files[fn]
            if panel.is_trs() is True:
                if fn == filename:
                    self._sel_file = fn
                    panel.set_selected_tiername(tier_name)
                    panel.set_selected_ann(ann_idx)
                    point = panel.get_selected_point()
                    # Update the SMMPC: set the selection to the timeslider
                    s, e = panel.get_selected_localization()
                    self.smmpc.set_selection_range(s, e)
                    updated = True
                else:
                    panel.set_selected_tiername(None)

        if updated is True:
            self.update_video_players(filename, ann_idx, point)

        return updated

    # -----------------------------------------------------------------------

    def get_selected_annotation(self):
        """Return the index of the currently selected annotation.

        :return: (int) Index or -1 if nor found.

        """
        if self._sel_file is not None:
            panel = self._files[self._sel_file]
            return panel.get_selected_ann()
        return -1

    # -----------------------------------------------------------------------

    def show_tier_annotations(self, value):
        """Show annotations of a tier instead or the information.

        :param value: (bool) True to show the annotations, False for the information.

        """
        for fn in self._files:
            panel = self._files[fn]
            if panel.is_trs() is True:
                panel.show_tier_infos(not bool(value), tiername=None)

    # -----------------------------------------------------------------------
    # Methods to operate on an AudioViewPanel()
    # -----------------------------------------------------------------------

    def enable_audio_infos(self, value=True):
        """Enable or disable the view of the audio information."""
        for fn in self._files:
            panel = self._files[fn]
            if panel.is_audio() is True:
                panel.GetPane().show_infos(bool(value))

        self.Layout()

    # -----------------------------------------------------------------------

    def enable_audio_waveform(self, value=True):
        """Enable or disable the view of the audio waveform."""
        value = bool(value)
        for fn in self._files:
            panel = self._files[fn]
            if panel.is_audio() is True:
                panel.show_waveform(value)

        self.Layout()

    # -----------------------------------------------------------------------

    def enable_video_film(self, value=True):
        """Enable or disable the view of the video frames."""
        value = bool(value)
        for fn in self._files:
            panel = self._files[fn]
            if panel.is_video() is True:
                panel.GetPane().show_film(value)

        self.Layout()

    # -----------------------------------------------------------------------
    # Methods to operate on a VideoViewPanel()
    # -----------------------------------------------------------------------

    def enable_video_infos(self, value=True):
        """Enable or disable the view of the video information."""
        value = bool(value)
        for fn in self._files:
            panel = self._files[fn]
            if panel.is_video() is True:
                panel.GetPane().show_infos(value)

        self.Layout()

    # -----------------------------------------------------------------------
    # Methods to operate on any or all BaseViewPanel()
    # -----------------------------------------------------------------------

    def zoom_height(self, direction, panel=None):
        """Increase or decrease the height of all panels.

        :param direction: (int) Positive to increase
        :param panel: (wx.Panel) A panel to apply the zoom or None to apply to all

        """
        if direction == 0:
            return

        if panel is not None:
            if direction < 0:
                panel.ZoomDown()
            else:
                panel.ZoomUp()
        else:
            # Set the zoom level to each panel
            for fn in self._files:
                p = self._files[fn]
                if direction < 0:
                    p.ZoomDown()
                else:
                    p.ZoomUp()

        # Update scroll parent panel
        self.Layout()
        self.SendSizeEvent()

    # -----------------------------------------------------------------------
    # GUI creation
    # -----------------------------------------------------------------------

    def _create_content(self):
        """Create the main content. """
        smmpc = SMMPCPanel(self, name="smmpc_risepanel")
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self._on_collapse_smmpc_changed, smmpc)

        # The use of Create is required under Linux if the style includes ALWAYS_SHOW_SB.
        # scrolled = sppasScrolledPanel(self)
        # scrolled.Create(self, style=wx.BORDER_NONE | wx.ALWAYS_SHOW_SB | wx.VSCROLL,
        #                 name="scrolled_panel")
        if wx.Platform == "__WXMSW__":
            scrolled = sppasScrolledPanel(self, style=wx.BORDER_NONE | wx.ALWAYS_SHOW_SB | wx.VSCROLL, name="scrolled_panel")
        else:
            scrolled = sppasScrolledPanel(self, style=wx.BORDER_NONE, name="scrolled_panel")
        scrolled.SetupScrolling(scroll_x=False, scroll_y=True)
        sizer = wx.BoxSizer(wx.VERTICAL)
        scrolled.SetSizer(sizer)

        # Fix size&layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(smmpc, 0, wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT, border=sppasPanel.fix_size(2))
        main_sizer.Add(scrolled, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, border=sppasPanel.fix_size(2))
        self.SetSizer(main_sizer)

    # -----------------------------------------------------------------------

    @property
    def _scrolled_panel(self):
        return self.FindWindow("scrolled_panel")

    @property
    def _sizer(self):
        return self._scrolled_panel.GetSizer()

    @property
    def smmpc(self):
        """Return the SPPAS Multi Media Player Ctrl."""
        return self.FindWindow("smmpc_risepanel").GetPane()

    # -----------------------------------------------------------------------

    def _sort_files(self):
        """Ask the user to assign a rank to each file."""
        files = list()
        panels = list()
        colors = list()
        for child in self._sizer.GetChildren():
            panel = child.GetWindow()
            files.append(panel.get_filename())
            panels.append(panel)
            colors.append(panel.GetBackgroundColour())

        dlg = sppasRankFilesDialog(self, files, colors)
        resp = dlg.ShowModal()
        if resp == wx.ID_OK:
            sorted_files = dlg.get_files()
            if sorted_files != files:
                # Detach all panels
                for i in reversed(range(len(panels))):
                    self._sizer.Detach(i)
                # Add panels in the expected sorted list
                for filename in sorted_files:
                    old_idx = files.index(filename)
                    self._sizer.Add(panels[old_idx], 0, wx.EXPAND | wx.BOTTOM, sppasPanel.fix_size(2))
                self.Layout()
                self.notify(action="files_sorted", filename="", value=None)
        dlg.DestroyFadeOut()

    # -----------------------------------------------------------------------

    def select_next_prev_annot(self, sel_next=True):
        """Select the next or the previous annotation.

        :param sel_next: (bool) Select the next if True, the previous if False.
        :return: (int) Index of the newly selected annotation

        """
        if self._sel_file is None:
            return -1

        panel = self._files[self._sel_file]
        idx = panel.get_selected_ann()
        if sel_next is True:
            panel.set_selected_ann(idx + 1)
        else:
            panel.set_selected_ann(idx - 1)

        new_idx = panel.get_selected_ann()
        if new_idx != -1:
            self.notify(action="tier_selected", filename=self._sel_file, value=self.get_selected_tiername())
            # Only the selected annotation changed: the panel has to be drawn
            # again, but nothing was modified into the file.
            panel.Refresh()
            s, e = panel.get_selected_localization()
            self.smmpc.set_selection_range(s, e)
            self.update_visible_range(s, e)
        else:
            # restore
            panel.set_selected_ann(idx)
            new_idx = idx

        return new_idx

    # -----------------------------------------------------------------------
    # Events management
    # -----------------------------------------------------------------------

    def notify(self, action, filename, value=None):
        """Notify the parent of an event."""
        wx.LogDebug("{:s} notifies its parent {:s} of action {:s}."
                    "".format(self.GetName(), self.GetParent().GetName(), action))
        evt = TimelineViewEvent(action=action, filename=filename, value=value)
        evt.SetEventObject(self)
        wx.PostEvent(self.GetParent(), evt)

    # -----------------------------------------------------------------------

    def _process_time_event(self, event):
        """Process a time view event.

        A child emitted this event to inform an action occurred or to ask
        for an action.

        :param event: (wx.Event)

        """
        try:
            panel = event.GetEventObject()
            action = event.action
            value = event.value
            filename = panel.get_filename()
            if filename not in self._files:
                raise Exception("An unknown panel {:s} emitted an EVT_TIMELINE_VIEW."
                                "".format(filename))
        except Exception as e:
            wx.LogError("{:s} received an unexpected event".format(self.GetName()))
            wx.LogError(str(e))
            return
        wx.LogDebug("{:s} received an event action '{:s}' of file {:s} with value {:s}"
                    "".format(self.GetName(), action, filename, str(value)))

        if action == "zoom_up":
            # Zoom up the panel that emitted the event
            self.zoom_height(1, panel=panel)

        elif action == "zoom_down":
            # Zoom down the panel that emitted the event
            self.zoom_height(-1, panel=panel)

        elif isinstance(panel, TrsViewPanel):
            ann_idx = panel.get_selected_ann()
            if action == "tier_selected":
                # a new tier was selected, or a new annotation in this tier
                self.__set_selection(filename, value, ann_idx)

            elif action == "selected_point_update":
                if self._sel_file is not None:
                    selected_file_panel = self._files[self._sel_file]
                    selected_ann_idx = selected_file_panel.get_selected_ann()
                    self.update_video_players(self._sel_file, selected_ann_idx, event.value)

            elif action == "size":
                self.Layout()
                return

            else:
                if self._sel_file is not None:
                    selected_file_panel = self._files[self._sel_file]
                    selected_ann_idx = selected_file_panel.get_selected_ann()
                    selected_point = selected_file_panel.get_selected_point()
                    self.update_video_players(self._sel_file, selected_ann_idx, selected_point)

        elif isinstance(panel, VideoViewPanel):
            if self._sel_file is None:
                # Every action of a video player is about the annotation which
                # is selected into a transcription file, and there's none.
                return

            if action == "ann_update":
                # update the selected annotation panel
                selected_file_panel = self._files[self._sel_file]
                selected_file_panel.update_ann(event.value)

                # we need to synchronize tiers shown in players UI
                selected_point = selected_file_panel.get_selected_point()
                selected_tier = self.get_selected_tier()
                for filename in self._files:
                    p = self._files[filename]
                    if panel != p and p.is_video():
                        p.update_ann_in_video_frame(selected_tier, event.value, selected_point)

            elif action == "selected_point_update":
                # update the selected point of the selected annotation panel
                selected_file_panel = self._files[self._sel_file]
                selected_ann_idx = selected_file_panel.get_selected_ann()
                selected_file_panel.update_selected_point(event.value)
                # and update all the videoplayers (we could not update the one that emitted)
                self.update_video_players(self._sel_file, selected_ann_idx, event.value)

            elif action == "tier_selected":
                # Given event filename is the name of the video. The selected transcription
                # didn't change, so the selected tier is one of the current selected file.
                ann_idx = event.value
                filename = self._sel_file
                value = self.get_selected_tier().get_name()
                self.__set_selection(filename, value, ann_idx)
        else:
            wx.LogWarning("{:s} received an unknown event action '{:s}' of file {:s} with value {:s}"
                          "".format(self.GetName(), action, filename, str(value)))

        # send the event to the parent, including the filename
        self.notify(action, filename, value)

    # -----------------------------------------------------------------------

    def _process_tool_event(self, event):
        """Process a button event from the smmpc or the videoframe.

        :param event: (wx.Event)

        """
        btn = event.GetEventObject()
        btn_name = btn.GetName()

        if btn_name == "video_infos":
            self.enable_video_infos(btn.GetValue())

        elif btn_name == "video_film":
            self.enable_video_film(btn.GetValue())

        elif btn_name == "media_play_next_frame":
            self.smmpc.play_frame(1)

        elif btn_name == "media_play_prev_frame":
            self.smmpc.play_frame(-1)

        event.Skip()

    # -----------------------------------------------------------------------

    def _process_key_event(self, event):
        """Process a key event or skip it.

        See https://www.wxpython.org/Phoenix/docs/html/wx.KeyCode.enumeration.html#wx-keycode

        :param event: (wx.Event)

        """
        key_code = event.GetKeyCode()

        # The media keys of the keyboard are not combined with a modifier.
        # Posting event to the SMMPC is not recommended: it must ***NOT** skip it.
        if key_code in (wx.WXK_MEDIA_STOP, wx.WXK_MEDIA_PLAY_PAUSE):
            wx.PostEvent(self.smmpc, event)
            return

        if event.ShiftDown() is False:

            if event.AltDown() is True and event.ControlDown() is False:
                if key_code == wx.WXK_RIGHT:
                    self.select_next_prev_annot(sel_next=True)
                    return
                elif key_code == wx.WXK_LEFT:
                    self.select_next_prev_annot(sel_next=False)
                    return

            elif event.ControlDown() is True and event.AltDown() is False:
                # Posting event to the SMMPC is not recommended: it must ***NOT** skip it.
                if key_code == wx.WXK_LEFT:
                    wx.PostEvent(self.smmpc, event)
                    return
                elif key_code == wx.WXK_RIGHT:
                    wx.PostEvent(self.smmpc, event)
                    return
                elif key_code in (65, 73, 79):
                    # a, i, o
                    wx.PostEvent(self.smmpc, event)
                    return

        event.Skip()

    # -----------------------------------------------------------------------

    def _on_collapse_smmpc_changed(self, evt=None):
        self.Layout()
        self._scrolled_panel.ScrollChildIntoView(self.FindWindow("smmpc_risepanel"))
        if self.FindWindow("smmpc_risepanel").IsExpanded() is True:
            action = "expanded"
        else:
            action = "collapsed"
        self.notify(action, filename="", value=None)

    def _on_collapse_changed(self, evt=None):
        panel = evt.GetEventObject()
        self._collapse_changed(panel)

    # ----------------------------------------------------------------------

    def _collapse_changed(self, panel):
        # Update our layout - the sizer needs to get new sizes
        self.Layout()
        self._scrolled_panel.ScrollChildIntoView(panel)

        # Enable or disable the media into the SMMPC
        if panel.is_audio() is True or panel.is_video() is True:
            self.smmpc.enable(panel.get_filename(), value=panel.IsExpanded())

        # Notify parent: at least, it needs to layout
        if panel.IsExpanded() is True:
            action = "expanded"
        else:
            action = "collapsed"
        self.notify(action, filename=panel.get_filename(), value=panel.GetPane())

    # ----------------------------------------------------------------------

    def __on_media_loaded(self, event):
        filename = event.filename
        panel = self._files[filename]

        if self.smmpc.is_audio(filename):
            wx.LogMessage("Audio loaded successfully: {}".format(filename))
            panel.show_waveform(self.smmpc.is_audios_waveform())
            panel.set_audio_data(
                nchannels=self.smmpc.get_nchannels(filename),
                sampwidth=self.smmpc.get_sampwidth(filename),
                framerate=self.smmpc.get_framerate(filename),
                duration=self.smmpc.get_duration(filename),
                frames=self.smmpc.get_frames(filename)
            )
        elif self.smmpc.is_video(filename):
            wx.LogMessage("Video loaded successfully: {}".format(filename))
            panel.show_film(self.smmpc.is_video_film())
            panel.set_video_data(
                framerate=self.smmpc.get_framerate(filename),
                duration=self.smmpc.get_duration(filename),
                width=self.smmpc.get_video_width(filename),
                height=self.smmpc.get_video_height(filename)
            )
        panel.Expand()
        self._collapse_changed(panel)

        # If no visible part was defined, do it now! or update it.
        self.update_visible_range()

        s, e = self.smmpc.get_visible_range()
        if self.smmpc.is_audio(filename) or self.smmpc.is_video(filename):
            panel.set_visible_period(s, e)

    # ----------------------------------------------------------------------

    def __on_media_not_loaded(self, event):
        filename = event.filename
        wx.LogError("Failed to load media file {}".format(filename))
        panel = self._files[filename]
        panel.Collapse()
        self._collapse_changed(panel)

    # ----------------------------------------------------------------------

    def _process_media_event(self, event):
        """"""
        if event.action == "visible":
            s, e = event.value
            for fn in self._files:
                panel = self._files[fn]
                panel.set_visible_period(s, e)

        elif event.action == "tiers_annotations":
            self.show_tier_annotations(event.value)

        elif event.action == "audio_waveform":
            self.enable_audio_waveform(event.value)

        elif event.action == "video_film":
            self.enable_video_film(event.value)

        elif event.action == "sort_files":
            self._sort_files()

        elif event.action in ("play", "stop"):
            for filename in self._files:
                panel = self._files[filename]
                if panel.is_video():
                    panel.invalidate_selected_frames()

        elif event.action == "zoom_up":
            self.zoom_height(1)

        elif event.action == "zoom_down":
            self.zoom_height(-1)

    # ----------------------------------------------------------------------

    def update_visible_range(self, s=None, e=None):
        """Update the visible range to be sure that s or e is inside."""
        # no visible range was defined before
        duration = self.smmpc.get_duration()
        vd = self.smmpc.get_duration() / 10.

        current_visible = self.smmpc.get_visible_range()
        cs = current_visible[0]
        ce = current_visible[1]
        # no visible range was defined before... we'll do it now.
        if cs+ce == 0.:
            if s is None:
                # no start time was given
                if e is not None:
                    # but an end time was given
                    vs = max(0., e - vd)
                    ve = min(duration, e + vd)
                else:
                    # and no end time too
                    vs = 0.
                    ve = vd
            else:
                # a start time was given
                if e is None:
                    # but no end time.
                    vs = max(0., s - vd)
                    ve = min(duration, s + vd)
                # a end time was given too
                else:
                    vs = max(0., s - vd)
                    ve = min(duration, e + vd)
            self.smmpc.set_visible_range(vs, ve)
            for filename in self._files:
                panel = self._files[filename]
                panel.set_visible_period(vs, ve)

        else:
            # a visible range was defined before.
            if s is None and e is None:
                # visible range is centering the currently selected annotation
                self.smmpc.scroll_to_selection()
                ns, ne = self.smmpc.get_visible_range()
                for fn in self._files:
                    panel = self._files[fn]
                    panel.set_visible_period(ns, ne)
            else:
                # fix s and e if they are unknown
                if s is None or e is None:
                    self.smmpc.scroll_to_selection()
                    cs, ce = self.smmpc.get_visible_range()
                    if s is None:
                        s = cs
                    if e is None:
                        e = ce
                # check if s or e inside.
                cs, ce = self.smmpc.get_visible_range()
                if s >= ce or e <= cs:
                    # The expected (s,e) is after or before the visible period
                    self.smmpc.scroll_to_selection()
                    ns, ne = self.smmpc.get_visible_range()
                    for fn in self._files:
                        panel = self._files[fn]
                        panel.set_visible_period(ns, ne)
                elif cs <= s < e <= ce:
                    pass
                else:
                    cs_adjust = False
                    if s < cs:
                        cs_adjust = True
                        if e > ce:
                            # zoom out to make [s,e] fully visible
                            ce = e
                        else:
                            # scroll to make 's' visible
                            d = cs - s
                            ce = ce - d
                        cs = s
                    if e > ce:
                        if cs_adjust is False:
                            # scroll to make 'e' visible
                            d = e - ce
                            cs = cs + d
                        ce = e
                    # apply to the smmpc
                    self.smmpc.set_visible_range(cs, ce)
                    for fn in self._files:
                        panel = self._files[fn]
                        panel.set_visible_period(cs, ce)

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def _create_panel(self, name):
        """Create a view rise panel to display a file.

        :param name: (str) Name of the file to view
        :return: wx.Window

        """
        try:
            with TimelineType() as tt:
                if tt.guess_type(name) == tt.video:
                    panel = VideoViewPanel(self._scrolled_panel, filename=name)

                elif tt.guess_type(name) == tt.audio:
                    panel = AudioViewPanel(self._scrolled_panel, filename=name)

                elif tt.guess_type(name) == tt.trs:
                    panel = TrsViewPanel(self._scrolled_panel, filename=name)

                elif tt.guess_type(name) == tt.unknown:
                    raise IOError(MSG_UNKNOWN)

        except Exception as e:
            # traceback.print_exc()
            panel = ErrorViewPanel(self._scrolled_panel, filename=name)
            panel.set_error_message(str(e))

        return panel

    # -----------------------------------------------------------------------

    def update_ann(self, trs_filename, idx, what="select"):
        """Modify annotation into the scrolled panel and video players.

        """
        for filename in self._files:
            panel = self._files[filename]
            if panel.is_trs():
                self._scrolled_panel.ScrollChildIntoView(panel)
                if filename == trs_filename:
                    if what == "select":
                        panel.set_selected_ann(idx)
                    elif what == "update":
                        panel.update_ann(idx)
                    elif what == "delete":
                        panel.delete_ann(idx)
                    elif what == "create":
                        panel.create_ann(idx)
                    break

        if self._sel_file is not None:
            selected_file_panel = self._files[self._sel_file]
            selected_ann_idx = selected_file_panel.get_selected_ann()
            selected_point = selected_file_panel.get_selected_point()
            self.update_video_players(self._sel_file, selected_ann_idx, selected_point)

    # -----------------------------------------------------------------------

    def update_video_players(self, trs_filename, idx, selected_point):
        """Force the opened video players to update their content and refresh.

        Has to be invoked when an annotation was updated in the scrolled panel
        or in a player UI, or when selection changed in the scrolled panel.

        :param trs_filename: (string) the filename from which the selected
        tier comes from
        :param idx: (int) the selected annotation index
        :param selected_point: (sppasPoint)

        """
        trs_panel = self._files[trs_filename]
        tier = trs_panel.get_selected_tier()

        for filename in self._files:
            panel = self._files[filename]
            if panel.is_video():
                panel.update_ann_in_video_frame(tier, idx, selected_point)


# ----------------------------------------------------------------------------
# Panel for tests
# ----------------------------------------------------------------------------


class TestPanel(wx.Panel):
    TEST_FILES = (
        os.path.join(paths.samples, "samples-fra", "F_F_B003_P8.wav"),
        os.path.join(paths.samples, "faces", "video_sample.mp4"),
        os.path.join(paths.basedir, "demo", "demo.mp4"),
        os.path.join(paths.samples, "annotation-results", "samples-fra", "F_F_B003-P8-palign.xra"),
        # os.path.join(paths.samples, "annotation-results", "samples-fra", "F_F_B003-P9-palign.xra"),
        os.path.join(paths.samples, "toto.xxx")
    )

    def __init__(self, parent):
        super(TestPanel, self).__init__(
            parent,
            size=(1200, 768),
            name="Timeline Panel")

        p = sppasTimelinePanel(self)
        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(p, 1, wx.EXPAND)
        self.SetSizer(s)

        for filename in TestPanel.TEST_FILES:
            p.append_file(filename)

        # the size won't be correct when collapsed. we need a layout.
        self.Bind(EVT_TIMELINE_VIEW, self._process_action)

    # -----------------------------------------------------------------------

    def _process_action(self, event):
        """Process an action event from one of the trs panels.

        :param event: (wx.Event)

        """
        panel = event.GetEventObject()
        filename = event.filename
        action = event.action
        value = event.value

        if action == "save":
            panel.save_file(filename)

        elif action == "close":
            closed = panel.remove_file(filename)
            self.Layout()

        elif action == "tiers_added":
            wx.LogDebug("Test Panel of Timeline received event 'tiers_added'")

        elif action == "tier_selected":
            wx.LogDebug("Test Panel of Timeline received event 'tier_selected'")

        elif action in ("collapsed", "expanded"):
            self.Layout()

        else:
            event.Skip()
