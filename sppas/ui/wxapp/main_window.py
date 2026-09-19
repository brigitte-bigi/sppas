# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.wxapp.main_window.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The main window of the SPPAS wx Application.

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
import wx

from sppas.core.coreutils import msg
from sppas.src.wkps.wio import sppasWJSON
from sppas.ui.agnostic import sppasCommClient
from sppas.ui.agnostic import sppasCommKeys
from sppas.ui.agnostic import sppasCommServerError

from .events import sb
from .events import sppasDataChangedEvent

from .windows import sppasStaticLine
from .windows import BitmapTextButton
from .windows import ToggleButton
from .windows import sppasPanel
from .windows import sppasDialog
from .windows.book import sppasSimplebook
from .windows import YesNoQuestion
from .views import About
from .views import Settings
from .page_files import sppasFilesPanel
from .page_annotate import sppasAnnotatePanel
from .page_analyze import sppasAnalyzePanel
from .page_editor import sppasEditorPanel
from .page_convert import sppasConvertPanel
from .page_plugins import sppasPluginsPanel

# ---------------------------------------------------------------------------


MSG_CONFIRM = msg("Confirm exit?", "ui")
MSG_ACTION_EXIT = msg('Close', "ui")
MSG_ACTION_SETTINGS = msg('Settings', "ui")

MENU_BUTTONS = {
    "page_home": msg("Home", "ui"),
    "page_files": msg("Files", "ui"),
    "page_annotate": msg("Annotate", "ui"),
    "page_analyze": msg("Analyze", "ui"),
    "page_editor": msg("Edit", "ui"),
    "page_convert": msg("Convert", "ui"),
    "page_plugins": msg("Plugins", "ui")
}

MENU_COLOURS = {
    "page_home": wx.Colour(128, 128, 128, 196),
    "page_files": wx.Colour(228, 128, 128, 196),
    "page_annotate": wx.Colour(250, 120, 50, 196),
    "page_analyze": wx.Colour(200, 180, 120, 196),
    "page_editor": wx.Colour(240, 220, 205, 196),
    "page_convert": wx.Colour(220, 40, 80, 196),
    "page_plugins": wx.Colour(196, 128, 196, 196)
}

# -----------------------------------------------------------------------


class sppasMainWindow(sppasDialog):
    """Create the main frame of SPPAS.

    This class:

        - does not inherit of wx.TopLevelWindow because we need EVT_CLOSE
        - does not inherit of wx.Frame because we don't need neither a
        status bar, nor a toolbar, nor a menu.

    Styles:

        - wx.CAPTION: Puts a caption on the dialog box
        - wx.RESIZE_BORDER: Display a resizable frame around the window
        - wx.CLOSE_BOX: Displays a close box on the frame
        - wx.MAXIMIZE_BOX: Displays a maximize box on the dialog
        - wx.MINIMIZE_BOX: Displays a minimize box on the dialog
        - wx.DIALOG_NO_PARENT: Create an orphan dialog

    """

    def __init__(self):
        super(sppasMainWindow, self).__init__(
            parent=None,
            title=wx.GetApp().GetAppDisplayName(),
            style=wx.WANTS_CHARS | wx.TAB_TRAVERSAL | wx.CAPTION |
                  wx.RESIZE_BORDER | wx.CLOSE_BOX | wx.MAXIMIZE_BOX |
                  wx.MINIMIZE_BOX | wx.DIALOG_NO_PARENT,
            name="sppas_main_dlg")
        # Members
        self._init_infos()

        # The other UI answered the last time a workspace was sent to it.
        self.__wkp_listener = True

        # Fix this frame content
        self._pages = list()
        self._create_content()
        self._setup_events()
        self.UpdateUI()

        # Announce the workspace this interface starts with: the other UI
        # is only told of the changes, so a workspace nobody changed yet
        # would never be reported -- and the other UI would show none.
        page = self.FindWindow("page_files")
        if page is not None:
            self._send_workspace(page.get_data())

        # Fix this frame properties
        self.Enable()
        self.Show(False)
        self.SetFocus()
        self.Raise()

    # -----------------------------------------------------------------------

    def Show(self, show=True):
        """Override to fade the window in."""
        if show is True:
            self.FadeIn()
        sppasDialog.Show(self, show)

    # ------------------------------------------------------------------------
    # Private methods to create the GUI and initialize members
    # ------------------------------------------------------------------------

    def _init_infos(self):
        """Overridden. Initialize the main frame.

        Set the title, the icon and the properties of the frame.

        :return: Delta value to fade in the window

        """
        sppasDialog._init_infos(self)

        # Fix some frame properties
        min_width = sppasPanel.fix_size(620)
        self.SetMinSize(wx.Size(min_width, 480))
        self.SetSize(wx.GetApp().settings.frame_size)
        self.SetName("frm_main")
        self.SetPosition(wx.GetApp().settings.frame_pos)

    # -----------------------------------------------------------------------

    def _create_content(self):
        """Create the content of the frame.

        Content is made of a menu, an area for panels and action buttons.

        """
        # The content of this main frame is organized in a book
        book = self._create_book()
        self.SetContent(book)

        # add a customized menu (instead of an header+toolbar)
        menus = sppasMenuPanel(self, self._pages)
        menus.enable(self._pages[0])
        self.SetHeader(menus)

        # add some action buttons
        actions = sppasActionsPanel(self)
        self.SetActions(actions)

        # organize the content and lays out.
        self.LayoutComponents()

    # -----------------------------------------------------------------------

    def _create_book(self):
        """Create the simple book to manage the several pages of the frame.

        Names of the pages are: page_welcome, page_files, page_annotate,
        page_analyze, page_convert, and page_plugins.

        """
        book = sppasSimplebook(
            parent=self,
            style=wx.BORDER_NONE | wx.TAB_TRAVERSAL | wx.WANTS_CHARS,
            name="content"
        )
        book.SetEffectsTimeouts(150, 200)

        # 1st page: a panel with a welcome message -- Removed in SPPAS 5.0

        # 2nd: file browser
        page = sppasFilesPanel(book)
        book.AddPage(page, text="")
        self._pages.append(page.GetName())

        # 3rd: annotate automatically selected files
        page = sppasAnnotatePanel(book)
        book.AddPage(page, text="")
        self._pages.append(page.GetName())

        # 4th: analyze checked files
        page = sppasAnalyzePanel(book) 
        book.AddPage(page, text="")
        self._pages.append(page.GetName())

        # 5th: edit checked files
        page = sppasEditorPanel(book) 
        book.AddPage(page, text="")
        self._pages.append(page.GetName())

        # 6th: convert checked files
        page = sppasConvertPanel(book) 
        book.AddPage(page, text="")
        self._pages.append(page.GetName())

        # 7th: plugins
        page = sppasPluginsPanel(book)
        book.AddPage(page, text="")
        self._pages.append(page.GetName())

        return book

    # -----------------------------------------------------------------------
    # Events management
    # -----------------------------------------------------------------------

    def _setup_events(self):
        """Associate a handler function with the events.

        It means that when an event occurs then the process handler function
        will be called.

        """
        # Bind close event from the close dialog 'x' on the frame
        self.Bind(wx.EVT_CLOSE, self.on_exit)

        # Bind all events from our buttons (including 'exit')
        self.Bind(wx.EVT_BUTTON, self._process_event)
        self.Bind(wx.EVT_TOGGLEBUTTON, self._process_event)

        # The data have changed.
        # This event was sent by any of the children
        self.FindWindow("content").Bind(sb.EVT_DATA_CHANGED, self._process_data_changed)

        # A message was received on the socket, posted by the communication
        # server of the application.
        self.Bind(sb.EVT_COMM_MESSAGE, self._process_comm_message)

        # Capture keys
        self.Bind(wx.EVT_CHAR_HOOK, self._process_key_event)

    # -----------------------------------------------------------------------

    def _process_event(self, event):
        """Process any kind of events.

        :param event: (wx.Event)

        """
        event_obj = event.GetEventObject()
        event_name = event_obj.GetName()

        if event_name == "exit":
            self.exit(interactive=True)

        elif event_name == "about":
            About(self)

        elif event_name == "settings":
            self.on_settings()

        elif event_name in self._pages:
            self.show_page(event_name)

    # -----------------------------------------------------------------------

    def _process_data_changed(self, event):
        """Process a change of data.

        Set the data of the event to the other panels.

        :param event: (wx.Event) An event with a sppasWorkspace()

        """
        # The object the event comes from
        emitted = event.GetEventObject()
        try:
            wkp = event.GetWorkspace()
            logging.debug("Main window received evt_data_changed.")
        except AttributeError:
            wx.LogError("Workspace wasn't sent in the event emitted by {:s}"
                        "".format(emitted.GetName()))
            return

        # Set the data to appropriate children panels
        book = self.FindWindow('content')
        for i in range(book.GetPageCount()):
            page = book.GetPage(i)
            if emitted != page and page.GetName() in self._pages:
                page.set_data(wkp)

        # Send the workspace to the other UI -- except when the change is
        # the one it just sent: this window is then the emitter.
        if emitted != self:
            self._send_workspace(wkp)

    # -----------------------------------------------------------------------

    def _send_workspace(self, wkp, name=None):
        """Send the workspace to the communication server of the other UI.

        The serialized workspace carries an internal identifier of its own
        (a uuid, see sppasWorkspace), unrelated to its display name: the
        name is fetched from the workspaces panel and sent alongside.

        Nothing is sent to a socket nobody listens to. The call waits for an
        answer, and this window waits with it: one silence is enough to learn
        that no one is there, and every click would pay for it again. The
        sending starts over when the other UI talks by itself.

        :param wkp: (sppasWorkspace)
        :param name: (str) Name to send instead of the one of the panel.
            An empty name says this interface has no workspace anymore.

        """
        if self.__wkp_listener is False:
            return

        wjson = sppasWJSON()
        wjson.set(wkp)
        wkp_name = name
        if wkp_name is None:
            wkpslist = self.FindWindow("wkpslist")
            wkp_name = ""
            if wkpslist is not None:
                wkp_name = wkpslist.get_wkp_name()
        settings = wx.GetApp().settings
        client = sppasCommClient(settings.shost, settings.sport)
        value = {"name": wkp_name, "workspace": wjson.serialize()}
        request = client.format_request(sppasCommKeys.WKP_CHANGED, value)
        try:
            client.request(request)
            logging.debug("Workspace sent to the communication server.")
        except sppasCommServerError:
            self.__wkp_listener = False
            logging.info("No communication server to send the workspace to. "
                         "The workspace is not sent again until the other "
                         "user interface talks.")

    # -----------------------------------------------------------------------

    def _process_comm_message(self, event):
        """Process a message received from the other UI.

        A WKP_CHANGED message carries the serialized dict of a workspace:
        parse it and re-emit EVT_DATA_CHANGED, with this window as the
        emitter so that the workspace is not sent back to its sender.

        :param event: (sppasCommMessageEvent)

        """
        # The other UI is there: what it sends is also what proves it listens.
        self.__wkp_listener = True

        key = event.GetKey()
        if key == sppasCommKeys.WKP_CHANGED:
            wjson = sppasWJSON()
            wjson.parse(event.GetValue())
            evt = sppasDataChangedEvent(self.GetId())
            evt.SetEventObject(self)
            evt.SetWorkspace(wjson)
            wx.PostEvent(self.FindWindow("content"), evt)

        elif key == sppasCommKeys.SHOW_PAGE:
            self.request_page(event.GetValue())

        elif key == sppasCommKeys.EXIT_REQUEST:
            # The web interface asks whether this one accepts to close.
            # Its request was acknowledged long before the reader made up
            # their mind: the answer travels as a message of its own.
            granted = self.exit(interactive=True)
            sppasMainWindow.answer_exit(granted)

        elif key == sppasCommKeys.BYE:
            # The web server announces its own shutdown: this interface
            # does not survive it either. Work in progress is asked about
            # first, exactly as when the reader closes this interface: an
            # exit decided elsewhere is not a reason to lose it.
            logging.info("The web server closed. Closing this interface too.")
            self.exit(interactive=True)

        else:
            logging.warning("Unexpected message received: key={:s}."
                            "".format(sppasCommKeys.name_of(key)))

    # -----------------------------------------------------------------------

    def _process_key_event(self, event):
        """Process a key event.

        :param event: (wx.Event)

        """
        key_code = event.GetKeyCode()

        if key_code == wx.WXK_F4 and event.AltDown() and wx.Platform == "__WXMSW__":
            # ALT+F4 on Windows to exit with confirmation
            self.exit(interactive=False)
            return

        elif key_code == 81 and event.ControlDown() and wx.Platform != "__WXMSW__":
            # CMD+q on MacOS / Ctrl+q on Linux/Windows to force exit
            event.Skip()
            self.exit(interactive=False)
            return

        elif key_code == 87 and event.ControlDown():
            # CMD+w on MacOS / Ctrl+w on Linux/Windows to exit with confirmation
            self.on_exit(event)
            return

        elif event.AltDown():

            if key_code == 70 and event.AltDown():
                # Alt+f
                self.FindWindow("header").enable("page_files")
                self.show_page("page_files")
                return

            elif key_code == wx.WXK_UP:
                self.show_next_page(direction=-1)
                return

            elif key_code == wx.WXK_DOWN:
                self.show_next_page(direction=1)
                return

            # elif key_code == wx.WXK_UP:
            #     page_name = self._pages[0]
            #     self.FindWindow("header").enable(page_name)
            #     self.show_page(page_name)
            #
            # elif key_code == wx.WXK_DOWN:
            #     page_name = self._pages[-1]
            #     self.FindWindow("header").enable(page_name)
            #     self.show_page(page_name)

        # Keeps on going the event to the current page of the book.
        # wx.LogDebug('Key event skipped by the main window.')
        event.Skip()

    # -----------------------------------------------------------------------
    # Callbacks to events
    # -----------------------------------------------------------------------

    def on_exit(self, event):
        """Makes sure the user was intending to exit the application.

        :param event: (wx.Event) Un-used.

        """
        response = YesNoQuestion(MSG_CONFIRM)
        if response == wx.ID_YES:
            logging.info("Bye bye... Hope to see you soon!")
            self.exit(interactive=True)
        else:
            logging.info("Welcome back...")

    # -----------------------------------------------------------------------

    def on_settings(self):
        """Open settings dialog and apply changes."""
        response = Settings(self)
        if response == wx.ID_CANCEL:
            return

        self.UpdateUI()

    # -----------------------------------------------------------------------
    # Public methods
    # -----------------------------------------------------------------------

    def exit(self, interactive=False) -> bool:
        """Destroy the frame, terminating the application.

        :param interactive: (bool) Ask user to confirm if modified files.
        :return: (bool) False if the reader cancelled, True if it is closing

        """
        # Close files in editor & analyze pages
        book = self.FindWindow("content")
        for page_name in ("page_editor", "page_analyze"):
            nb = book.FindWindow(page_name).close_files(interactive)
            if nb == -1:
                # The user cancelled. Can occur only if 'interactive' is True.
                return False

        # The other UI shows the workspace this one reports: a window which
        # is closing has none to report. Its silence would only say that it
        # is gone, not that no workspace is left.
        page = self.FindWindow("page_files")
        if page is not None:
            self._send_workspace(page.get_data(), name="")

        # Remember some properties of this window
        wx.GetApp().settings.set("frame_size", self.GetSize())
        wx.GetApp().settings.set("frame_pos", self.GetPosition())

        # Destroy after decreasing transparency of the frame
        self.DestroyFadeOut()
        return True

        # Under Windows, for an unknown reason (?!), the wxapp.OnExit() **WAS**
        # not invoked if exit() is called directly after clicking the Exit button.
        # if wx.Platform == "__WXMSW__":
        #     wx.GetApp().OnExit()

    # -----------------------------------------------------------------------

    @staticmethod
    def answer_exit(granted: bool) -> None:
        """Tell the web interface whether the exit was accepted.

        Nothing of this window is used: it is gone when the exit was
        accepted, and the answer is still owed.

        :param granted: (bool) True when this interface is closing

        """
        key = sppasCommKeys.EXIT_NO
        if granted is True:
            key = sppasCommKeys.EXIT_OK

        settings = wx.GetApp().settings
        client = sppasCommClient(settings.shost, settings.sport)
        try:
            client.request(client.format_request(key, {"source": "wxapp"}))
            logging.info("The answer to the exit request was sent: {:s}"
                         "".format(sppasCommKeys.name_of(key)))
        except sppasCommServerError:
            logging.info("The answer to the exit request was not sent: no "
                         "communication server.")

    # -----------------------------------------------------------------------

    def show_next_page(self, direction=1):
        """Show a page of the content panel, the next one.

        :param direction: (int) Positive=Next; Negative=RIGHT

        """
        book = self.FindWindow("content")
        c = book.GetSelection()
        if direction > 0:
            nextc = (c+1) % len(self._pages)
        elif direction < 0:
            nextc = (c-1) % len(self._pages)
        else:
            return
        next_page_name = self._pages[nextc]
        self.FindWindow("header").enable(next_page_name)
        self.show_page(next_page_name)

    # -----------------------------------------------------------------------

    def request_page(self, page_name):
        """Show a page and ask for the attention of the user.

        This is what the other UI asks for: the page is shown, the menu
        follows, and the window asks to be seen. Raising a window is a
        request the window manager is free to refuse -- Windows flashes
        the taskbar button instead -- hence the call for attention.

        :param page_name: (str) one of 'page_files', 'page_annotate', ...

        """
        if page_name not in self._pages:
            logging.error("Unknown page to show: {:s}".format(str(page_name)))
            return

        self.FindWindow("header").enable(page_name)
        self.show_page(page_name)

        if self.IsIconized() is True:
            self.Iconize(False)
        self.Raise()
        self.RequestUserAttention()

    # -----------------------------------------------------------------------

    def show_page(self, page_name):
        """Show a page of the content panel.

        If the page can't be found, the default home page is shown.

        :param page_name: (str) one of 'page_home', 'page_files', ...

        """
        book = self.FindWindow("content")

        # Find the page number to switch on
        w = book.FindWindow(page_name)
        if w is None:
            w = book.FindWindow(self._pages[0])
        p = book.FindPage(w)
        if p == wx.NOT_FOUND:
            p = 0

        # current page number
        c = book.FindPage(book.GetCurrentPage())

        # assign the effect
        if c < p:
            book.SetEffects(showEffect=wx.SHOW_EFFECT_SLIDE_TO_LEFT,
                            hideEffect=wx.SHOW_EFFECT_SLIDE_TO_LEFT)
        elif c > p:
            book.SetEffects(showEffect=wx.SHOW_EFFECT_SLIDE_TO_RIGHT,
                            hideEffect=wx.SHOW_EFFECT_SLIDE_TO_RIGHT)
        else:
            book.SetEffects(showEffect=wx.SHOW_EFFECT_NONE,
                            hideEffect=wx.SHOW_EFFECT_NONE)

        # then change to the page
        book.ChangeSelection(p)
        w.SetFocus()
        self.Layout()
        self.Refresh()

# ---------------------------------------------------------------------------


class sppasMenuPanel(sppasPanel):
    """Create a custom menu panel with several action buttons.

    """

    def __init__(self, parent, pages):
        super(sppasMenuPanel, self).__init__(
            parent=parent,
            style=wx.WANTS_CHARS | wx.TAB_TRAVERSAL | wx.NO_BORDER,
            name="header")

        self.SetMinSize(wx.Size(-1, wx.GetApp().settings.header_height))
        self._pages = pages

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        bord = sppasPanel.fix_size(6)

        sizer.AddStretchSpacer(1)
        
        for button_name in pages:
            btn_label = MENU_BUTTONS.get(button_name, "")
            btn = self._create_button(btn_label, button_name)
            colour = MENU_COLOURS.get(button_name, wx.Colour(128, 128, 128, 128))
            btn.SetFocusColour(colour)
            # btn.SetBitmapColour(colour)
            sizer.Add(btn, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=bord)

        sizer.AddStretchSpacer(1)

        self.SetSizer(sizer)

    # ------------------------------------------------------------------------

    def enable(self, btn_name):
        """Enable a given button name.

        :param btn_name: (str) Name of the page to enable the toggle button.

        """
        # Disable all the buttons
        for name in self._pages:
            self.FindWindow(name).SetValue(False)
        # Enable the expected one
        self.FindWindow(btn_name).SetValue(True)

    # -----------------------------------------------------------------------

    def _create_button(self, text, icon):
        btn = ToggleButton(self, label=text, name=icon)

        # Get the font height for the header
        h = self.get_font_height()

        btn.SetLabelPosition(wx.RIGHT)
        btn.SetFocusStyle(wx.PENSTYLE_SOLID)
        btn.SetFocusWidth(h//4)
        btn.SetSpacing(sppasPanel.fix_size(h//2))
        btn.SetMinSize(wx.Size(h*10, h*3))
        btn.Bind(sb.EVT_BUTTON_PRESSED, self.__on_tg_btn_event)
        btn.Bind(sb.EVT_WINDOW_FOCUSED, self._on_btn_focused)

        return btn

    # ------------------------------------------------------------------------
    # Callback to events
    # ------------------------------------------------------------------------

    def __on_tg_btn_event(self, event):
        obj = event.GetEventObject()
        name = obj.GetName()
        if name in self._pages:
            self.enable(name)

        event.Skip()

    # -----------------------------------------------------------------------

    def _on_btn_focused(self, event):
        win = event.GetEventObject()
        is_focused = event.GetFocused()
        if is_focused is True:
            win.SetFont(win.GetFont().MakeLarger())
            win.SetBitmapColour(wx.WHITE)
        else:
            win.SetBitmapColour(win.GetForegroundColour())
            win.SetFont(win.GetFont().MakeSmaller())

# ---------------------------------------------------------------------------


class sppasActionsPanel(sppasPanel):
    """Create my own panel with some action buttons.

    """
    def __init__(self, parent):

        super(sppasActionsPanel, self).__init__(
            parent=parent,
            style=wx.WANTS_CHARS | wx.TAB_TRAVERSAL | wx.NO_BORDER,
            name="actions")

        settings = wx.GetApp().settings

        # Create the action panel and sizer
        self.SetMinSize(wx.Size(-1, settings.action_height))
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        exit_btn = self._create_button(MSG_ACTION_EXIT, "exit")
        settings_btn = self._create_button(MSG_ACTION_SETTINGS, "settings")

        sizer.Add(settings_btn, 1, wx.ALL | wx.EXPAND, 0)
        sizer.Add(self.VertLine(), 0, wx.ALL | wx.EXPAND, 0)
        sizer.Add(exit_btn, 4, wx.ALL | wx.EXPAND, 0)

        self.SetSizer(sizer)

    # -----------------------------------------------------------------------

    def _create_button(self, text, icon):
        btn = BitmapTextButton(self, label=text, name=icon)

        # Get the font height for the header
        h = self.get_font_height()

        btn.SetLabelPosition(wx.RIGHT)
        btn.SetFocusStyle(wx.PENSTYLE_SOLID)
        btn.SetFocusWidth(1)
        btn.SetFocusColour(wx.Colour(128, 128, 128, 128))
        # btn.SetSpacing(sppasPanel.fix_size(h//2))
        btn.SetMinSize(wx.Size(h*10, h*2))
        btn.Bind(sb.EVT_WINDOW_SELECTED, self._on_btn_selected)
        btn.Bind(sb.EVT_WINDOW_FOCUSED, self._on_btn_focused)

        return btn

    # -----------------------------------------------------------------------

    def _on_btn_selected(self, event):
        win = event.GetEventObject()

    # -----------------------------------------------------------------------

    def _on_btn_focused(self, event):
        win = event.GetEventObject()
        is_focused = event.GetFocused()
        if is_focused is True:
            win.SetFont(win.GetFont().MakeLarger())
        else:
            win.SetFont(win.GetFont().MakeSmaller())

    # ------------------------------------------------------------------------

    def VertLine(self):
        """Return a vertical static line."""
        line = sppasStaticLine(self, orient=wx.LI_VERTICAL)
        line.SetMinSize(wx.Size(1, -1))
        line.SetSize(wx.Size(1, -1))
        line.SetPenStyle(wx.PENSTYLE_SOLID)
        line.SetDepth(1)
        return line
