# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.wxapp.page_plugins.plugslist.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: List of available plugins.

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
import os
import time

from sppas.core.coreutils import sppasTypeError
from sppas.src.plugins import sppasPluginsManager
from sppas.src.wkps import sppasWorkspace, States

from sppas.ui import _

from ..events import sppasDataChangedEvent
from ..windows import Error, Information
from ..windows import sppasDialog
from ..windows import sppasScrolledPanel
from ..windows import sppasProgressDialog
from ..windows import sppasPanel
from ..windows import sppasMessageText, sppasTitleText
from ..windows import BitmapTextButton, TextButton
from ..panel_shared import sppasOptionsPanel
from ..views import AboutPlugin

# ---------------------------------------------------------------------------
# List of displayed messages:


MSG_CONFIG = _("Configure")
MSG_ABOUT = _("About")

# -----------------------------------------------------------------------


class sppasPluginsList(sppasScrolledPanel):
    """Create the list of panels with plugins.

    No data is given at the initialization.
    Use set_data() method instead.

    """

    def __init__(self, parent, name="page_plugins_list"):
        super(sppasPluginsList, self).__init__(
            parent=parent,
            style=wx.BORDER_NONE,
            name=name
        )

        # The workspace to work with
        self.__data = sppasWorkspace()

        # The manager for the plugins
        try:
            self._manager = sppasPluginsManager()
        except Exception as e:
            self._manager = None
            Error("Plugin manager initialization: {:s}".format(str(e)))

        self._create_content()
        self._setup_events()

        self.Layout()

    # ------------------------------------------------------------------------
    # Public methods to access the data
    # ------------------------------------------------------------------------

    def get_data(self):
        """Return the data currently displayed in the list of files.

        :returns: (sppasWorkspace) data of the files-viewer model.

        """
        return self.__data

    # ------------------------------------------------------------------------

    def set_data(self, data):
        """Assign new data to this page.

        :param data: (sppasWorkspace)

        """
        if isinstance(data, sppasWorkspace) is False:
            raise sppasTypeError("sppasWorkspace", type(data))
        self.__data = data

    # -----------------------------------------------------------------------
    # Actions to perform with plugins
    # -----------------------------------------------------------------------

    def get_plugins(self):
        """Return the list of plugin identifiers."""
        return list(self._manager.get_plugin_ids())

    # ------------------------------------------------------------------------

    def delete(self, plugin_id):
        """Ask for the plugin to be removed, remove of the list.

        :returns: plugin identifier of the plugin to be deleted.

        """
        # Destroy the panel and remove of the sizer
        panel_name = plugin_id + "_panel"
        panel = None
        for i, child in enumerate(self.GetChildren()):
            if child.GetName() == panel_name:
                panel = child
                self.GetSizer().Remove(i)
                break
        if panel is None:
            return
        panel.Destroy()

        # Delete of the manager
        self._manager.delete(plugin_id)

        # Re-organize the UI
        self.Layout()
        self.Refresh()

    # ------------------------------------------------------------------------

    def install(self, filename):
        """Import and install a plugin.

        :param filename: (str) ZIP file of the plugin content
        :return: (str) folder in which the plugin is installed

        """
        # fix a name for the plugin directory
        plugin_folder = os.path.splitext(os.path.basename(filename))[0]
        plugin_folder = plugin_folder.replace(' ', "_")

        # install the plugin and display it in the list
        plugin_id = self._manager.install(filename, plugin_folder)
        self._append(self._manager.get_plugin(plugin_id))

        # Update the UI
        self.Layout()
        self.Refresh()
        return plugin_folder

    # ------------------------------------------------------------------------

    def apply(self, plugin_id):
        """Apply the plugin on the data.

        :param plugin_id: (str)

        """
        # Get the list of checked FileName() instances
        checked = self.__data.get_filename_from_state(States().CHECKED)
        wx.LogMessage("Apply plugin {:s} on {:d} files."
                      "".format(plugin_id, len(checked)))
        if len(checked) == 0:
            Information("No file(s) selected to apply the plugin on!")
            return

        # Convert the list of FileName() instances into a list of filenames
        checked_fns = [f.get_id() for f in checked]
        start_time = time.time()

        # Apply the plugin
        dlg = sppasPluginConfigureDialog(self, self._manager.get_plugin(plugin_id))
        if dlg.ShowModal() == wx.ID_OK:
            progress = sppasProgressDialog()
            try:
                progress.Show(True)
                progress.set_new()
                self._manager.set_progress(progress)
                log_text = self._manager.run_plugin(plugin_id, checked_fns)
                progress.close()
                progress = None

                # Show the output message
                if len(log_text) > 0:
                    Information(log_text)

                # Add new data into the list
                added = 0
                for f in checked_fns:
                    a = self.__data.add_file(f, brothers=True, ctime=start_time)
                    if a is not None:
                        added += len(a)

                # Notify the data changed (if any)
                if added > 0:
                    wx.LogMessage("{:d} files added into the workspace"
                                  "".format(added))
                    evt = sppasDataChangedEvent(self.GetId())
                    evt.SetEventObject(self)
                    evt.SetWorkspace(self.__data)
                    wx.PostEvent(self.GetParent(), evt)

            except Exception as e:
                if progress is not None:
                    progress.close()
                Error(str(e))

        dlg.Destroy()

    # ------------------------------------------------------------------------
    # Create and manage the GUI
    # ------------------------------------------------------------------------

    def _create_content(self):
        """"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        if self._manager is not None:
            for plugin_id in self._manager.get_plugin_ids():
                plugin = self._manager.get_plugin(plugin_id)
                self._append(plugin)

        self.SetupScrolling(scroll_x=True, scroll_y=True)

    # -----------------------------------------------------------------------

    def _append(self, plugin):
        """Append a plugin into the panel.

        :param plugin (sppasPluginParam) The plugin to append

        """
        border = sppasPanel.fix_size(20)
        pp = sppasPluginDescription(self, plugin)
        self.GetSizer().Add(pp, 1, wx.EXPAND | wx.RIGHT | wx.LEFT | wx.BOTTOM, border)
        pp.Layout()
        pp.Refresh()
        self.SetSize(self.GetSize())

    # -----------------------------------------------------------------------
    # Events management
    # -----------------------------------------------------------------------

    def _setup_events(self):
        """Associate a handler function with the events.

        It means that when an event occurs then the process handler function
        will be called.

        """
        # Bind all events from our buttons (including 'exit')
        self.Bind(wx.EVT_BUTTON, self._process_event)

    # -----------------------------------------------------------------------

    def _process_event(self, event):
        """Process any kind of events.

        :param event: (wx.Event)

        """
        event_obj = event.GetEventObject()
        event_name = event_obj.GetName()

        for plugin_id in self._manager.get_plugin_ids():
            if event_name == plugin_id:
                self.apply(plugin_id)
                event.Skip()
                break

# ---------------------------------------------------------------------------


class sppasPluginDescription(sppasPanel):
    """Panel to describe the given plugin.

    """

    def __init__(self, parent, plugin):
        super(sppasPluginDescription, self).__init__(
            parent=parent,
            style=wx.BORDER_RAISED,
            name=plugin.get_key() + "_panel"
        )

        # The plugin to work with
        self.__plugin = plugin

        self._create_content()
        self._setup_events()

    # -----------------------------------------------------------------------

    def _create_content(self):
        """"""
        apply = self.__create_enable_btn()
        about = self.__create_about_text()
        descr = self.__create_description_sizer()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(apply, 0, wx.ALIGN_CENTRE | wx.LEFT, 8)
        sizer.Add(about, 0, wx.ALIGN_CENTRE | wx.RIGHT | wx.LEFT, 8)
        sizer.Add(descr, 1, wx.ALIGN_CENTRE_VERTICAL | wx.RIGHT, 8)

        self.SetSizer(sizer)

    # -----------------------------------------------------------------------

    def __create_enable_btn(self):
        w = sppasPanel.fix_size(128)
        h = sppasPanel.fix_size(48)

        btn_enable = BitmapTextButton(self, label=self.__plugin.get_key(), name=self.__plugin.get_key())
        btn_enable.SetImage(os.path.join(self.__plugin.get_directory(), self.__plugin.get_icon()))
        btn_enable.SetLabelPosition(wx.BOTTOM)
        btn_enable.SetSpacing(sppasPanel.fix_size(6))
        btn_enable.SetFocusWidth(0)
        btn_enable.SetBitmapColour(self.GetForegroundColour())
        btn_enable.SetMinSize(wx.Size(w, h))

        return btn_enable

    # -----------------------------------------------------------------------

    def __create_about_text(self):
        w = sppasPanel.fix_size(96)
        h = sppasPanel.fix_size(32)

        btn_about = TextButton(self, label=MSG_ABOUT + "...", name="about_plugin")
        btn_about.SetBorderWidth(0)
        btn_about.SetForegroundColour(wx.Colour(80, 100, 220))
        btn_about.SetMinSize(wx.Size(w, h))

        return btn_about

    # -----------------------------------------------------------------------

    def __create_description_sizer(self):
        p = sppasPanel(self, name="plugdescr_panel")
        s = wx.BoxSizer(wx.VERTICAL)
        tt = sppasTitleText(p, value=self.__plugin.get_name(), name="plugtext_title")
        tt.SetMinSize(wx.Size(-1, sppasPanel.fix_size(10)*2))
        td = sppasMessageText(p, self.__plugin.get_descr(), name="plugtext_message")
        s.Add(tt, 1, wx.EXPAND | wx.ALL, p.fix_size(4))
        s.Add(td, 3, wx.EXPAND | wx.ALL, p.fix_size(4))
        p.SetSizer(s)
        return p

    # -----------------------------------------------------------------------
    # Events management
    # -----------------------------------------------------------------------

    def _setup_events(self):
        """Associate a handler function with the events.

        It means that when an event occurs then the process handler function
        will be called.

        """
        # Bind all events from our buttons (including 'exit')
        self.Bind(wx.EVT_BUTTON, self._process_event)

    # -----------------------------------------------------------------------

    def _process_event(self, event):
        """Process any kind of events.

        :param event: (wx.Event)

        """
        event_obj = event.GetEventObject()
        event_name = event_obj.GetName()

        if event_name == "about_plugin":
            AboutPlugin(self, self.__plugin)

        event.Skip()

    # -----------------------------------------------------------------------

    def SetForegroundColour(self, colour):
        wx.Window.SetForegroundColour(self, colour)
        self.FindWindow("about_plugin").SetForegroundColour(colour)
        self.FindWindow("plugtext_message").SetForegroundColour(colour)
        # do not apply on the title nor the about button

    # -----------------------------------------------------------------------

    def SetBackgroundColour(self, colour):
        # Use a slightly different bg color in order to highlight the panel
        r, g, b = colour.Red(), colour.Green(), colour.Blue()
        delta = 10
        if (r + g + b) > 384:
            ccolour = wx.Colour(r, g, b).ChangeLightness(100 - delta)
        else:
            ccolour = wx.Colour(r, g, b).ChangeLightness(100 + delta)

        wx.Window.SetBackgroundColour(self, ccolour)
        for c in self.GetChildren():
            if c.GetName() == "plugdescr_panel":
                # this one is not highlighted, but it has to follow a change
                # of the color: giving it nothing was keeping the previous one
                c.SetBackgroundColour(colour)
            else:
                c.SetBackgroundColour(ccolour)
        self.FindWindow("plugtext_message").SetBackgroundColour(ccolour)

# ---------------------------------------------------------------------------


class sppasPluginConfigureDialog(sppasDialog):
    """Dialog to configure the given plugin.

    Returns either wx.ID_CANCEL or wx.ID_OK if ShowModal().

    """
    def __init__(self, parent, plugin):
        """Create a dialog to fix an annotation config.

        :param parent: (wx.Window)

        """
        super(sppasPluginConfigureDialog, self).__init__(
            parent=parent,
            title="plugin_configure",
            style=wx.DEFAULT_FRAME_STYLE | wx.DIALOG_NO_PARENT)

        self.plugin = plugin
        self.items = []
        self._options_key = []

        self.CreateHeader(MSG_CONFIG + " {:s}".format(plugin.get_name()),
                          "wizard-config")
        self._create_content()
        self._create_buttons()

        # Bind events
        self.Bind(wx.EVT_BUTTON, self._process_event)

        self.LayoutComponents()
        self.GetSizer().Fit(self)
        self.CenterOnParent()
        self.FadeIn()

    # -----------------------------------------------------------------------

    def _create_content(self):
        """Create the content of the dialog."""
        all_options = self.plugin.get_options()
        selected_options = []
        for option in all_options:
            if option.get_key() != "input" and option.get_value() != "input":
                self._options_key.append(option.get_key())
                selected_options.append(option)

        options_panel = sppasOptionsPanel(self, selected_options)
        options_panel.SetAutoLayout(True)
        self.items = options_panel.GetItems()
        self.SetContent(options_panel)

    # -----------------------------------------------------------------------

    def _create_buttons(self):
        self.CreateActions([wx.ID_CANCEL, wx.ID_OK])
        self.Bind(wx.EVT_BUTTON, self._process_event)
        self.SetAffirmativeId(wx.ID_OK)

    # -----------------------------------------------------------------------

    def _process_event(self, event):
        """Process any kind of events.

        :param event: (wx.Event)

        """
        event_obj = event.GetEventObject()
        event_id = event_obj.GetId()

        if event_id == wx.ID_CANCEL:
            self.SetReturnCode(wx.ID_CANCEL)
            self.Close()

        elif event_id == wx.ID_OK:
            # Set the list of "Option" instances to the plugin
            for i, item in enumerate(self.items):
                new_value = item.GetValue()
                key = self._options_key[i]
                option = self.plugin.get_option_from_key(key)
                option.set_value(str(new_value))
            # OK. Close the dialog and return wxID_OK
            self.EndModal(wx.ID_OK)
