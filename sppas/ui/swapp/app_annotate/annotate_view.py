"""
:filename: sppas.ui.swapp.app_annotate.annotate_view.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The view of Annotate: the tree of its page.

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

from whakerpy.htmlmaker import HTMLTree
from whakerpy.htmlmaker import EmptyNode
from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import TagNode

from sppas.core.config import sg
from sppas.ui import _

from ..swapp_base.swapp_view import swappBaseView
from ..swapp_core.swappsg import swapp_settings

from .annotate_record import swappAnnotateRecord
from .annotate_panels import swappActionAnnotatePanel
from .annotate_panels import swappAnnotationsPanel
from .annotate_panels import swappFilesAnnotatePanel
from .annotate_panels import swappLogAnnotatePanel
from .annotate_panels import swappReportsPanel

# ---------------------------------------------------------------------------

MSG_HEADER = f"SPPAS {sg.__release__} » " + _("Annotate")
MSG_VIEW_LEFT = _("Left")
MSG_VIEW_BOTH = _("Both")
MSG_VIEW_RIGHT = _("Right")
MSG_VIEW_LABEL = _("Panels to display")
MSG_UNDELETED = _("The report {:s} could not be deleted: {:s}")

BODY_SCRIPT = f"""
        import {{ AnnotateManager }} from '/{swapp_settings.js}sppas.js';

        const annotateManager = new AnnotateManager();
        annotateManager.handleAnnotateManagerOnLoad();
"""

# ---------------------------------------------------------------------------


class swappAnnotateView(swappBaseView):
    """View class responsible for populating the page of Annotate.

    It builds the header and the nav of the page. It decides nothing: what
    it shows was decided before it was called.

    """

    def __init__(self, tree: HTMLTree, help_page: str):
        """Initialize and populate the Annotate view structure.

        :param tree: (HTMLTree) An existing HTML tree to populate
        :param help_page: (str) Name of the page serving the document of the app
        :raises: TypeError: tree is not an instance of HTMLTree

        """
        if isinstance(tree, HTMLTree) is False:
            raise TypeError("swappAnnotateView: tree must be an instance of HTMLTree. "
                            "Got {} instead.".format(type(tree)))
        # Set before the base view populates the nav with it.
        self.__help_page = help_page
        self.__files = None
        super(swappAnnotateView, self).__init__(tree, MSG_HEADER)

    # -----------------------------------------------------------------------
    # Populate the tree
    # -----------------------------------------------------------------------

    def _populate_head_css(self, *args, **kwargs):
        """Override. Add the sheet of the panel-view toggle, and the one of Annotate."""
        super()._populate_head_css(*args, **kwargs)
        self._htree.head.link("stylesheet", swapp_settings.wexa_statics + "css/togglegroup.css",
                              link_type="text/css")
        self._htree.head.link("stylesheet", swapp_settings.css + "app_annotate.css", link_type="text/css")

    # -----------------------------------------------------------------------

    def _populate_body_header(self):
        """Override. Populate the header area of the page."""
        self.append_responsive_menu_button(self._htree.body_header)

    # -----------------------------------------------------------------------

    def _populate_body_nav(self):
        """Override. Populate the nav area of the page."""
        _s = TagNode(self._htree.body_nav.identifier, None, "section")
        self.append_pin_button(_s)
        self.append_accessibility_buttons(_s)
        self._htree.body_nav.append_child(_s)
        self.append_home_link_button(self._htree.body_nav, self._home_target())
        self.append_help_link_button(self._htree.body_nav, self.__help_page)
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

    def populate_tree_content(self, record: swappAnnotateRecord) -> None:
        """Append the toggle of the panels, then the panel of the steps and the one of the reports.

        :param record: (swappAnnotateRecord) What is to be shown
        :raises: TypeError: The given record is not a swappAnnotateRecord

        """
        if isinstance(record, swappAnnotateRecord) is False:
            raise TypeError("swappAnnotateView: record must be an instance of swappAnnotateRecord. "
                            "Got {} instead.".format(type(record)))

        _shown = record.to_be_shown
        self.__files = None

        # The dialogs of the messages. Each report which could not be deleted
        # is said in the one of the errors, with the reason.
        self.append_alert_dialogs(self._htree.body_main)
        if "undeleted" in _shown:
            _dialog = self._htree.body_main.get_child("error_dialog")
            _undeleted = _shown["undeleted"]
            for _name in _undeleted:
                _dialog.append_child(HTMLNode(_dialog.identifier, None, "p",
                                              value=MSG_UNDELETED.format(_name, _undeleted[_name])))

        # The form of the performance: every field and every button of the
        # page is tied to it by its attribute "form", whichever panel is
        # written.
        _form = TagNode(self._htree.body_main.identifier, None, "form",
                        attributes={"id": "annotate_form", "method": "post"})
        self._htree.body_main.append_child(_form)
        # The names the written panel shows as fields.
        _fields = list()

        # The panel which was asked for takes the whole page: the annotations
        # of one type, the files, or the procedure outcome report. The six
        # steps are shown otherwise, beside the reports.
        if "annotations" in _shown:
            self._htree.body_main.append_child(swappAnnotationsPanel(self._htree.body_main.identifier,
                                                                     _shown.get("type", ""),
                                                                     _shown["annotations"],
                                                                     record.selected,
                                                                     record.annotation_langs,
                                                                     _shown.get("disabled", list())))
            for _annotation in _shown["annotations"]:
                _fields.append("annotate_ann_" + _annotation.get_key())
                _fields.append("annotate_lang_" + _annotation.get_key())
        elif record.task == "files":
            self.__files = swappFilesAnnotatePanel(self._htree.body_main.identifier)
            self._htree.body_main.append_child(self.__files)
        elif "report" in _shown:
            self._htree.body_main.append_child(swappLogAnnotatePanel(self._htree.body_main.identifier,
                                                                     record.report, _shown["report"]))
        else:
            self.__populate_steps(_shown, record)
            for _kind in record.extensions:
                _fields.append("annotate_ext_" + _kind)
            _fields.append("annotate_lang")
            _fields.append("annotate_merge")
            _fields.append("annotate_report")

        # What the record holds and the written panel does not show as a
        # field is carried in the form, hidden: the next request rebuilds
        # the record from all of it.
        _data = record.serialize()
        for _name in _data:
            if (_name in _fields) is False:
                _form.append_child(EmptyNode(_form.identifier, None, "input",
                                             attributes={"type": "hidden", "name": _name, "value": _data[_name]}))

    # -----------------------------------------------------------------------

    def get_files(self) -> TagNode | None:
        """Return the panel of the files, None when it was not written."""
        return self.__files

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __populate_steps(self, shown: dict, record: swappAnnotateRecord) -> None:
        """Append the toggle of the panels, then the six steps and the reports side by side.

        :param shown: (dict) What is to be shown
        :param record: (swappAnnotateRecord) What was decided

        """
        # Locally, the reports stand beside the six steps. Online there is no
        # list of reports: its panel is collapsed, and the six steps are alone.
        _local = "reports" in shown
        _view = "both"
        if _local is False:
            _view = "left"

        # The toggle choosing which panel(s) to display: a narrow window
        # makes two panels side by side hard to read. A native radiogroup:
        # keyboard operation and the checked-state announcement come from
        # the radio inputs themselves, not from JavaScript.
        _toggle = TagNode(self._htree.body_main.identifier, None, "section")
        _toggle.set_attribute("id", "annotate_toggle")
        _toggle.set_attribute("class", "toggle-group center")
        _toggle.set_attribute("role", "radiogroup")
        _toggle.set_attribute("aria-label", MSG_VIEW_LABEL)
        self._htree.body_main.append_child(_toggle)

        for value, msg in (("left", MSG_VIEW_LEFT),
                           ("both", MSG_VIEW_BOTH),
                           ("right", MSG_VIEW_RIGHT)):
            _label = TagNode(_toggle.identifier, None, "label")
            _label.set_attribute("class", "menuitem")
            _label.set_attribute("for", "annotate_view_" + value)
            _toggle.append_child(_label)
            _radio = HTMLNode(_label.identifier, None, "input")
            _radio.set_attribute("type", "radio")
            _radio.set_attribute("name", "annotate_panel_view")
            _radio.set_attribute("id", "annotate_view_" + value)
            _radio.set_attribute("value", value)
            if value == _view:
                _radio.set_attribute("checked", None)
            _label.append_child(_radio)
            _text = HTMLNode(_label.identifier, None, "span", value=msg)
            _label.append_child(_text)

        # The steps and the reports, in two side-by-side panels.
        _panels = TagNode(self._htree.body_main.identifier, None, "section")
        _panels.set_attribute("id", "annotate_panels")
        _panels.set_attribute("class", "flex-panel")
        self._htree.body_main.append_child(_panels)

        _panels.append_child(swappActionAnnotatePanel(_panels.identifier, shown.get("kinds", dict()),
                                                      record.extensions,
                                                      shown.get("languages", list()),
                                                      record.lang,
                                                      shown.get("types", list()),
                                                      shown.get("holding", list()),
                                                      shown.get("files", 0),
                                                      record.merge,
                                                      record.selected,
                                                      record.report,
                                                      _local))
        _panels.append_child(swappReportsPanel(_panels.identifier, shown.get("reports", list()), record.report,
                                               _local))


    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    files = property(get_files, None)
