"""
:filename: sppas.ui.swapp.pages.feedback_view.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: View of the "Feedback" page.

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

from sppas.core.config import sg
from sppas.core.coreutils import sppasLogFile
from sppas.ui import _
from sppas.ui.swapp.swapp_base.swapp_view import swappBaseView
from sppas.ui.swapp.swapp_core.swappsg import swapp_settings

# ---------------------------------------------------------------------------


# The long versions of these messages are in the "po" files.
MSG_PURPOSE = _("This page allows you to send an e-mail to the author.")
MSG_NOTICE = _("The feedback is anonymous.")
MSG_HOWTO = _("Click the button below: the message is copied.")
MSG_TO = _("To: ")
MSG_SUBJECT = _("Subject: ")
MSG_DESCRIBE = _("Write the message here")
MSG_MESSAGE = _("Message:")
MSG_INCLUDED = _("Technical information included in the message")
MSG_REPORT = _("What to include")
MSG_MINIMAL = _("Minimal system information")
MSG_FULL = _("Full trace report")
MSG_SEND = _("Send by e-mail")
MSG_COPIED = _("The message is copied. Paste it in the e-mail and send it.")
MSG_EMPTY = _("Write a message before sending.")
MSG_NO_CLIPBOARD = _("The message can not be copied. Select and copy it manually.")

# ---------------------------------------------------------------------------

MSG_HEADER = f"SPPAS {sg.__release__} » " + _("Feedback")

BODY_SCRIPT = f"""
        import {{ FeedbackManager }} from '/{swapp_settings.js}sppas.js';

        const feedbackManager = new FeedbackManager();
        feedbackManager.handleFeedbackManagerOnLoad();

"""

# ---------------------------------------------------------------------------


class swappFeedbackView(swappBaseView):
    """View class responsible for populating the *feedback.html* page.

    This class represents the **View** component of the "Feedback" page.
    It receives an existing :class:`HTMLTree` instance and fills it with a
    form allowing the user to prepare a feedback message: a free text and
    the technical information, both visible before anything is sent.

    The message never leaves the application by itself: the send action is
    handled by the JS FeedbackManager, in the browser.

    """

    def __init__(self, tree: HTMLTree):
        """Initialize and populate the "Feedback" view structure.

        :param tree: (HTMLTree) An existing HTML tree to populate with
                     the page-specific content.
        :raises: TypeError: tree is not an instance of HTMLTree

        """
        if isinstance(tree, HTMLTree) is False:
            raise TypeError("swappFeedbackView: tree must be an instance of HTMLTree. Got {}".format(type(tree)))
        super().__init__(tree, MSG_HEADER)

    # -----------------------------------------------------------------------
    # Populate the tree
    # -----------------------------------------------------------------------

    def _populate_head_css(self):
        """Override. Populate the `<head>` section of the HTML tree for CSS links.

        No page-specific stylesheet: the page relies on the shared one only.

        """
        pass

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

        self.append_home_link_button(self._htree.body_nav, self._home_target())
        self.append_trace_link_button(self._htree.body_nav)

    # -----------------------------------------------------------------------

    def populate_body_script(self):
        """Override. Populate the script body section.

        """
        self._htree.body_script.add_attribute("type", "module")
        self._htree.body_script.set_value(BODY_SCRIPT)

    # -----------------------------------------------------------------------
    # Update the tree -- for baking the page
    # -----------------------------------------------------------------------

    def populate_tree_content(self, trace_text: str):
        """Populate the tree content with the feedback form.

        :param trace_text: (str) The serialized content of the trace store,
                           proposed as the full report of the message.

        """
        # The purpose of the page
        _purpose = HTMLNode(self._htree.body_main.identifier, None, "p", value=MSG_PURPOSE)
        self._htree.body_main.append_child(_purpose)

        # The anonymity notice: the user must know what is sent.
        _notice = HTMLNode(self._htree.body_main.identifier, None, "p", value=MSG_NOTICE)
        self._htree.body_main.append_child(_notice)

        # Recipient and subject, fixed
        _to = sg.__contact__
        _subject = sg.__name__ + " " + sg.__version__ + " - Feedback..."
        _p = TagNode(self._htree.body_main.identifier, None, "p")
        self._htree.body_main.append_child(_p)
        _s = HTMLNode(_p.identifier, None, "strong", value=MSG_TO)
        _p.append_child(_s)
        _s = HTMLNode(_p.identifier, None, "span", value=_to)
        _p.append_child(_s)
        _b = TagNode(_p.identifier, None, "br")
        _p.append_child(_b)
        _s = HTMLNode(_p.identifier, None, "strong", value=MSG_SUBJECT)
        _p.append_child(_s)
        _s = HTMLNode(_p.identifier, None, "span", value=_subject)
        _p.append_child(_s)

        # The message of the user
        _label = HTMLNode(self._htree.body_main.identifier, None, "label", value=MSG_MESSAGE)
        _label.set_attribute("for", "feedback_message")
        self._htree.body_main.append_child(_label)
        _text = HTMLNode(self._htree.body_main.identifier, None, "textarea")
        _text.set_attribute("id", "feedback_message")
        _text.set_attribute("name", "feedback_message")
        _text.set_attribute("rows", "8")
        _text.set_attribute("class", "width_full")
        _text.set_attribute("placeholder", MSG_DESCRIBE)
        self._htree.body_main.append_child(_text)

        # The choice of the technical information to include: minimal
        # system information, or the full report of the trace store.
        # There is no "nothing" choice, on purpose.
        # A group of radio buttons is a fieldset with its legend, and each
        # button is written beside its label, not inside it: wexa.css hides
        # a control put inside a label, which is how it dresses one as a
        # button.
        _choice = TagNode(self._htree.body_main.identifier, None, "fieldset")
        _choice.set_attribute("id", "feedback_choice")
        self._htree.body_main.append_child(_choice)

        _legend = HTMLNode(_choice.identifier, None, "legend", value=MSG_REPORT)
        _choice.append_child(_legend)

        for value, message in (("minimal", MSG_MINIMAL), ("full", MSG_FULL)):
            ident = "feedback_report_" + value
            _radio = HTMLNode(_choice.identifier, ident, "input")
            _radio.set_attribute("id", ident)
            _radio.set_attribute("type", "radio")
            _radio.set_attribute("name", "feedback_report")
            _radio.set_attribute("value", value)
            if value == "minimal":
                _radio.set_attribute("checked", None)
            _choice.append_child(_radio)

            _label = HTMLNode(_choice.identifier, None, "label", value=message)
            _label.set_attribute("for", ident)
            _choice.append_child(_label)

        # The technical information, visible in an accordion: the user
        # sees exactly what will be sent. One block for each choice, the
        # JS FeedbackManager shows the selected one.
        _details = TagNode(self._htree.body_main.identifier, None, "details")
        self._htree.body_main.append_child(_details)
        _summary = HTMLNode(_details.identifier, None, "summary", value=MSG_INCLUDED)
        _details.append_child(_summary)
        _info = HTMLNode(_details.identifier, None, "pre", value=sppasLogFile.get_header())
        _info.set_attribute("id", "feedback_sysinfo")
        _details.append_child(_info)
        _report = HTMLNode(_details.identifier, None, "pre", value=html.escape(trace_text))
        _report.set_attribute("id", "feedback_fullreport")
        _report.set_attribute("class", "hidden")
        _details.append_child(_report)

        # The procedure to follow, replaced by the status of the send action.
        # The area is announced to screen readers when its content changes.
        _status = HTMLNode(self._htree.body_main.identifier, None, "p", value=MSG_HOWTO)
        _status.set_attribute("id", "feedback_status")
        _status.set_attribute("class", "status-message")
        _status.set_attribute("aria-live", "polite")
        self._htree.body_main.append_child(_status)

        # The single send button, handled by the JS FeedbackManager
        _button = HTMLNode(self._htree.body_main.identifier, None, "button", value=MSG_SEND)
        _button.set_attribute("id", "feedback_send_button")
        _button.set_attribute("type", "button")
        _button.set_attribute("class", "action-button")
        _button.set_attribute("data-to", _to)
        _button.set_attribute("data-subject", _subject)
        _button.set_attribute("data-msg-copied", MSG_COPIED)
        _button.set_attribute("data-msg-empty", MSG_EMPTY)
        _button.set_attribute("data-msg-error", MSG_NO_CLIPBOARD)
        self._htree.body_main.append_child(_button)
