"""
:filename: sppas.ui.swapp.pages.trace_view.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: View of the "Traces" page.

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

from __future__ import annotations
import html

from whakerpy.htmlmaker import HTMLTree
from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import TagNode

from sppas.core.config import cfg
from sppas.core.config import sg
from sppas.ui import _
from sppas.ui.swapp.wappbase.wappview import swappBaseView
from sppas.ui.swapp.wappcore.wappsg import wapp_settings
from sppas.ui.swapp.wappcore.wapputils import sppasImagesAccess
from sppas.ui.swapp.main_trace_store import swappTraceStore

# ---------------------------------------------------------------------------


MSG_CLOSE = _("Close")
MSG_REFRESH = _("Refresh")
MSG_SAVE = _("Save")
MSG_CLEAR = _("Clear")
MSG_API_TITLE = _("What SPPAS did, and why")
MSG_UI_TITLE = _("How the interface is running")
MSG_TITLE = _("The journal of SPPAS")
MSG_VIEW_LEFT = _("Left")
MSG_VIEW_BOTH = _("Both")
MSG_VIEW_RIGHT = _("Right")
MSG_VIEW_LABEL = _("Panels to display")
# Same strings as the real 410 response (hstatusnode.py): the heartbeat
# can only detect the server is gone from client-side JavaScript, with no
# server left to bake the real page -- this reproduces its message.
MSG_SESSION_ENDED = _("Session ended")
MSG_CLOSE_TAB = _("You can close this tab. [...]")
# The long version of the message is in the "po" files.
MSG_PURPOSE = _("This page displays the messages of SPPAS.")
# Le code source « sppas » est à jour.
MSG_UP_TO_DATE = _("The « sppas » source code is up to date.")
# Une mise à jour du code source « sppas » est disponible. Lancez Setup pour l’installer.
MSG_UPDATE = _("An update of the « sppas » source code is available. Run Setup to install it.")

# The CSS class of a record, by Python logging level name.
LOG_LEVEL_CLASS = {
    "DEBUG": "log-debug",
    "INFO": "log-info",
    "WARNING": "log-warning",
    "ERROR": "log-error",
    "CRITICAL": "log-critical",
}

# ---------------------------------------------------------------------------

MSG_HEADER = f"SPPAS {sg.__release__} » " + _("Journal")

BODY_SCRIPT = f"""
        import {{ TraceManager }} from '/{wapp_settings.js}sppas.js';

        const traceManager = new TraceManager();
        traceManager.handleTraceManagerOnLoad();
"""

# ---------------------------------------------------------------------------


class TraceView(swappBaseView):
    """View class responsible for populating the *journal.html* page.

    This class represents the **View** component of the "Traces" page.
    It receives an existing :class:`HTMLTree` instance and fills it with
    the content of the shared trace store: the useful trace/info messages
    of all the SPPAS components. It replaces the former wx log window.

    The Save and Clear actions are sent with a native form POST. The only
    JavaScript of the page is the heartbeat of the TraceManager: the
    server knows the single tab displaying the traces is open.

    """

    def __init__(self, tree: HTMLTree):
        """Initialize and populate the "Traces" view structure.

        :param tree: (HTMLTree) An existing HTML tree to populate with
                     the page-specific content.
        :raises: TypeError: tree is not an instance of HTMLTree

        """
        if isinstance(tree, HTMLTree) is False:
            raise TypeError("TraceView: tree must be an instance of HTMLTree. Got {}".format(type(tree)))
        super().__init__(tree, MSG_HEADER)

    # -----------------------------------------------------------------------
    # Populate the tree
    # -----------------------------------------------------------------------

    def _home_target(self) -> str:
        """Override. The Journal lives in its own persistent, named tab.

        Going "home" must not turn it into the Dashboard: it switches to
        the Dashboard's own named tab instead.

        """
        return "sppas_dashboard"

    # -----------------------------------------------------------------------

    def _populate_head_css(self):
        """Override. Populate the `<head>` section of the HTML tree for CSS links.

        The panel-view toggle needs Whakerexa's segmented control.

        """
        self._htree.head.link("stylesheet", wapp_settings.wexa_statics + "css/togglegroup.css",
                              link_type="text/css")

    # -----------------------------------------------------------------------

    def _populate_body_header(self):
        """Override. Populate the header area of the page.

        """
        self.append_responsive_menu_button(self._htree.body_header)

    # -----------------------------------------------------------------------

    def _populate_body_nav(self):
        """Override. Populate the nav area of the page.

        """
        _s = TagNode(self._htree.body_nav.identifier, None, "section")
        self.append_pin_button(_s)
        self.append_accessibility_buttons(_s)
        self._htree.body_nav.append_child(_s)

        # The Journal has its own tab: its Dashboard button switches to the
        # tab of the Dashboard -- see _home_target() -- instead of turning
        # this one into it.
        self.append_home_link_button(self._htree.body_nav, self._home_target())
        self.append_help_link_button(self._htree.body_nav)
        self.__append_close_button(self._htree.body_nav, self._home_target())

    # -----------------------------------------------------------------------

    @staticmethod
    def __append_close_button(parent: HTMLNode, home_target: str) -> HTMLNode:
        """Create and append the button closing the tab of the Journal.

        The tab of the Dashboard is brought forward before this one closes,
        so that closing the Journal lands the user where the Journal was
        opened from. A browser only lets a script close what a script
        opened: the button works in the tab opened by the Dashboard, and
        does nothing in a tab the user opened by hand.

        :param parent: (HTMLNode) the parent HTML node to append the button in
        :param home_target: (str) Window name of the tab of the Dashboard
        :return: (HTMLNode) the close button node

        """
        go_home = ("window.open(window.Wexa.accessibility.setUrlWithParameters("
                   f"'{wapp_settings.default_page()}'), '{home_target}');")
        _button = HTMLNode(parent.identifier, None, "button",
                           value="<span>" + MSG_CLOSE + "</span>")
        _button.add_attribute("data-icon", "cancel")
        _button.add_attribute("id", "close-tab_button")
        _button.add_attribute("aria-label", MSG_CLOSE)
        _button.add_attribute("aria-keyshortcuts", "w")
        _button.add_attribute("title", MSG_CLOSE + " (w)")
        _button.add_attribute("type", "button")
        _button.add_attribute("class", "menuitem")
        _button.add_attribute("onclick", go_home + " window.close()")
        parent.append_child(_button)
        return _button

    # -----------------------------------------------------------------------

    def populate_body_script(self):
        """Override. Populate the script body section.

        """
        self._htree.body_script.add_attribute("type", "module")
        self._htree.body_script.set_value(BODY_SCRIPT)

    # -----------------------------------------------------------------------
    # Update the tree -- for baking the page
    # -----------------------------------------------------------------------

    @staticmethod
    def _colorize(records: list) -> str:
        """Return the records as one HTML-ready string, one colored line each.

        Each line is wrapped in a <span> carrying the CSS class of its
        logging level. Built as a single string, not as child nodes: a
        <pre> with several child nodes is mis-indented by WhakerPy, which
        breaks the preformatted layout -- a single value is not affected.

        :param records: (list) Records, as returned by swappTraceStore.
        :return: (str) One <span> per record, joined with newlines.

        """
        lines = list()
        for record in records:
            css_class = LOG_LEVEL_CLASS.get(record["levelname"], "log-info")
            line_text = html.escape(swappTraceStore.format_record(record))
            lines.append(f'<span class="{css_class}">{line_text}</span>')
        return "\n".join(lines) + "\n"

    # -----------------------------------------------------------------------

    def populate_tree_content(self, header_text: str, api_records: list,
                              ui_records: list, status_text: str = ""):
        """Populate the tree content with the given trace.

        The records are displayed in two side-by-side panels: the messages
        of the API on the left, the logs of the interfaces on the right.
        Each line is colored according to the logging level of its record.

        :param header_text: (str) The header of the trace store.
        :param api_records: (list) The records of the API origin.
        :param ui_records: (list) The records of the UI origin.
        :param status_text: (str) The status of the last action, if any.

        """
        # Read by the heartbeat when it detects the server is gone: no
        # server is left to bake the real "session ended" page then.
        self._htree.body_main.set_attribute("data-msg-session-ended", MSG_SESSION_ENDED)
        self._htree.body_main.set_attribute("data-msg-close-tab", MSG_CLOSE_TAB)

        # The title of the page: it says more than the short name "Journal".
        _title = HTMLNode(self._htree.body_main.identifier, None, "h2", value=MSG_TITLE)
        self._htree.body_main.append_child(_title)

        # The purpose of the page
        _purpose = HTMLNode(self._htree.body_main.identifier, None, "p", value=MSG_PURPOSE)
        self._htree.body_main.append_child(_purpose)

        # The actions, sent to the server with a native form POST.
        # No 'action' attribute: the browser then posts to the URL of the page
        # itself, query string included, so the accessibility parameters of
        # Whakerexa -- which are propagated on links only -- are preserved.
        _form = TagNode(self._htree.body_main.identifier, None, "form")
        _form.set_attribute("id", "trace_actions")
        _form.set_attribute("method", "post")
        self._htree.body_main.append_child(_form)

        # Refresh sends no event: the page is simply baked again.
        _refresh = HTMLNode(_form.identifier, None, "button", value=MSG_REFRESH)
        _refresh.set_attribute("type", "submit")
        _form.append_child(_refresh)

        _save = HTMLNode(_form.identifier, None, "button", value=MSG_SAVE)
        _save.set_attribute("type", "submit")
        _save.set_attribute("name", "event_bake")
        _save.set_attribute("value", "handle_trace_save")
        _form.append_child(_save)

        _clear = HTMLNode(_form.identifier, None, "button", value=MSG_CLEAR)
        _clear.set_attribute("type", "submit")
        _clear.set_attribute("name", "event_bake")
        _clear.set_attribute("value", "handle_trace_clear")
        _form.append_child(_clear)

        # The status of the last action -- an inline message, never a dialog.
        if len(status_text) > 0:
            _status = HTMLNode(self._htree.body_main.identifier, None, "p",
                               value=html.escape(status_text))
            _status.set_attribute("class", "status-message")
            _status.set_attribute("role", "status")
            self._htree.body_main.append_child(_status)

        # The update state of the source code, as displayed by the About
        # page. It is colored with the levels of the journal: a warning if
        # a newer version exists, an information if the code is up to date.
        if cfg.update_info.get('update') is True:
            _update = HTMLNode(self._htree.body_main.identifier, None, "p", value=MSG_UPDATE)
            _update.set_attribute("class", "status-message log-warning")
        else:
            _update = HTMLNode(self._htree.body_main.identifier, None, "p", value=MSG_UP_TO_DATE)
            _update.set_attribute("class", "status-message log-info")
        self._htree.body_main.append_child(_update)

        # The header of the store, once, above the two panels.
        # The values are escaped: they are plain text and could contain
        # characters interpreted as HTML.
        _header = HTMLNode(self._htree.body_main.identifier, None, "pre",
                           value=html.escape(header_text))
        _header.set_attribute("id", "trace_header")
        self._htree.body_main.append_child(_header)

        # The toggle choosing which panel(s) to display: a narrow window
        # makes two half-width panels hard to read. A native radiogroup:
        # keyboard operation and the checked-state announcement come from
        # the radio inputs themselves, not from JavaScript.
        _toggle = TagNode(self._htree.body_main.identifier, None, "section")
        _toggle.set_attribute("class", "toggle-group center")
        _toggle.set_attribute("role", "radiogroup")
        _toggle.set_attribute("aria-label", MSG_VIEW_LABEL)
        self._htree.body_main.append_child(_toggle)

        for value, msg, checked in (("left", MSG_VIEW_LEFT, False),
                                    ("both", MSG_VIEW_BOTH, True),
                                    ("right", MSG_VIEW_RIGHT, False)):
            _label = TagNode(_toggle.identifier, None, "label")
            _label.set_attribute("class", "menuitem")
            _label.set_attribute("for", "trace_view_" + value)
            _toggle.append_child(_label)
            _radio = HTMLNode(_label.identifier, None, "input")
            _radio.set_attribute("type", "radio")
            _radio.set_attribute("name", "trace_panel_view")
            _radio.set_attribute("id", "trace_view_" + value)
            _radio.set_attribute("value", value)
            if checked is True:
                _radio.set_attribute("checked", None)
            _label.append_child(_radio)
            _text = HTMLNode(_label.identifier, None, "span", value=msg)
            _label.append_child(_text)

        # The records, in two side-by-side panels: one for each origin.
        _panels = TagNode(self._htree.body_main.identifier, None, "section")
        _panels.set_attribute("id", "trace_panels")
        _panels.set_attribute("class", "flex-panel")
        self._htree.body_main.append_child(_panels)

        _api = TagNode(_panels.identifier, None, "section")
        _api.set_attribute("id", "trace_api_panel")
        _api.set_attribute("class", "width_50")
        _panels.append_child(_api)
        _title = HTMLNode(_api.identifier, None, "h3", value=MSG_API_TITLE)
        _api.append_child(_title)
        _content = HTMLNode(_api.identifier, None, "pre",
                            value=self._colorize(api_records))
        _content.set_attribute("id", "trace_api_content")
        _api.append_child(_content)

        _ui = TagNode(_panels.identifier, None, "section")
        _ui.set_attribute("id", "trace_ui_panel")
        _ui.set_attribute("class", "width_50")
        _panels.append_child(_ui)
        _title = HTMLNode(_ui.identifier, None, "h3", value=MSG_UI_TITLE)
        _ui.append_child(_title)
        _content = HTMLNode(_ui.identifier, None, "pre",
                            value=self._colorize(ui_records))
        _content.set_attribute("id", "trace_ui_content")
        _ui.append_child(_content)
