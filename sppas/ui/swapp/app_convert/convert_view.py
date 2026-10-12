"""
:filename: sppas.ui.swapp.app_convert.convert_view.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The view of the Convert application.

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

from whakerpy.htmlmaker import EmptyNode
from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import HTMLTree
from whakerpy.htmlmaker import TagNode

from sppas.core.config import sg
from sppas.ui import _

from ..swapp_base.swapp_view import swappBaseView
from ..swapp_core.swappsg import swapp_settings
from ..nodes import swappProgressBar

from .convert_record import swappConvertRecord
from .convert_record import TASK_CONVERT
from .convert_record import MISSING_BATCH
from .convert_record import FIELD_REPORT
from .convert_panels import swappFormatsPanel
from .convert_panels import swappDestinationPanel
from .convert_panels import swappComparePanel
from .convert_panels import swappGeneralPanel
from .convert_panels import ID_FORM
from .convert_panels import swappResultsPanel

# ---------------------------------------------------------------------------

ID_SECTION = "convert_section"

MSG_HEADER = f"SPPAS {sg.__release__} » " + _("Convert")
MSG_TITLE = _("Conversion options")
MSG_INTRO = _("Convert writes annotated files into another format. Add the files to convert, "
              "choose the destination format, then convert. What the chosen format does not "
              "support is said beside the list of formats.")
MSG_MISSING = {MISSING_BATCH: _("No file is checked to be converted.")}

BODY_SCRIPT = f"""
        import {{ ConvertManager }} from '/{swapp_settings.js}sppas.js';
        import SwappFiles from '/{swapp_settings.js}swapp_files.js';
        const swappFiles = new SwappFiles();
        swappFiles.handleSwappFilesOnLoad();
        const convertManager = new ConvertManager(swappFiles);
        convertManager.handleConvertManagerOnLoad();
"""

# ---------------------------------------------------------------------------


class swappConvertView(swappBaseView):
    """View class responsible for populating the page of Convert.

    It builds the panel of the conversion, made of its five panels, from
    a record. It decides nothing: what it shows was decided before it was
    called.

    """

    def __init__(self, tree: HTMLTree, help_page: str):
        """Initialize and populate the Convert view structure.

        :param tree: (HTMLTree) An existing HTML tree to populate
        :param help_page: (str) Name of the page serving the document of the app
        :raises: TypeError: tree is not an instance of HTMLTree

        """
        if isinstance(tree, HTMLTree) is False:
            raise TypeError("swappConvertView: tree must be an instance of HTMLTree. "
                            "Got {} instead.".format(type(tree)))
        self.__section = None
        self.__info = ""
        # Set before the base view populates the nav with it.
        self.__help_page = help_page
        super(swappConvertView, self).__init__(tree, MSG_HEADER)

    # -----------------------------------------------------------------------

    def get_info(self) -> str:
        """Return what was said in the dialog of information, empty if nothing (str)."""
        return self.__info

    # -----------------------------------------------------------------------

    def get_section(self) -> TagNode:
        """Return the panel of the conversion, as it was last built.

        :return: (TagNode) None before it was built

        """
        return self.__section

    # -----------------------------------------------------------------------
    # Populate the tree
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

    def _populate_head_css(self, *args, **kwargs):
        """Override. Add the sheets of the table which compares the formats, and the one of Convert."""
        super()._populate_head_css(*args, **kwargs)
        self._htree.head.link("stylesheet", swapp_settings.wexa_statics + "css/extras/sortatable.css",
                              link_type="text/css")
        self._htree.head.link("stylesheet", swapp_settings.wexa_statics + "css/toggleselect.css",
                              link_type="text/css")
        self._htree.head.link("stylesheet", swapp_settings.css + "app_convert.css", link_type="text/css")

    # -----------------------------------------------------------------------

    def populate_body_script(self):
        """Override. Populate the script body section."""
        self._htree.body_script.add_attribute("type", "module")
        self._htree.body_script.set_value(BODY_SCRIPT)

    # -----------------------------------------------------------------------
    # Update the tree -- for baking the page
    # -----------------------------------------------------------------------

    def populate_introduction(self) -> None:
        """Append to the main content what the page is for, and in which order."""
        self._htree.body_main.append_child(HTMLNode(self._htree.body_main.identifier, None, "p", value=MSG_INTRO))

    # -----------------------------------------------------------------------

    def populate_tree_content(self, record: swappConvertRecord) -> None:
        """Append the panel of the conversion to the main content.

        :param record: (swappConvertRecord) What is to be shown
        :raises: TypeError: The given record is not a swappConvertRecord

        """
        if isinstance(record, swappConvertRecord) is False:
            raise TypeError("swappConvertView: record must be an instance of swappConvertRecord. "
                            "Got {} instead.".format(type(record)))

        self.append_alert_dialogs(self._htree.body_main)

        _shown = record.to_be_shown
        _conversion = record.conversion
        _section = TagNode(self._htree.body_main.identifier, ID_SECTION, "section",
                           attributes={"id": ID_SECTION, "class": "panel"})
        self._htree.body_main.append_child(_section)
        _section.append_child(HTMLNode(_section.identifier, None, "h3", value=MSG_TITLE))

        _section.append_child(swappComparePanel(_section.identifier, _shown.get("formats", list())))

        _flex = TagNode(_section.identifier, None, "div", attributes={"class": "flex-panel"})
        _section.append_child(_flex)
        _flex.append_child(swappFormatsPanel(_flex.identifier, _shown.get("formats", list()),
                                             _conversion.destination))
        _flex.append_child(swappDestinationPanel(_flex.identifier, _shown.get("formats", list()),
                                                 _conversion.destination))

        _section.append_child(swappGeneralPanel(_section.identifier, _conversion.override, _conversion.heuristic))

        # While the conversion runs, the page follows it: the progress, and the
        # name of the report it reads, which the form transmits.
        if _shown.get("converting", False) is True:
            _section.append_child(swappProgressBar(_section.identifier).get_node())
            _section.append_child(EmptyNode(_section.identifier, None, "input",
                                            attributes={"type": "hidden", "form": ID_FORM,
                                                        "name": FIELD_REPORT, "value": record.report}))

        if "results" in _shown:
            _section.append_child(swappResultsPanel(_section.identifier, _shown["results"]))

        self.__info = ""
        if record.task == TASK_CONVERT or _shown.get("ready", False) is True:
            self.__say_what_is_missing(_shown.get("missing", list()))

        self.__section = _section

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __say_what_is_missing(self, missing: list) -> None:
        """Say in the dialog of information what is missing for the conversion to run.

        :param missing: (list of str) What is missing, empty when nothing is

        """
        if len(missing) == 0:
            return

        _dialog = self._htree.body_main.get_child("info_dialog")
        _said = list()
        for _missing in missing:
            _dialog.append_child(HTMLNode(_dialog.identifier, None, "p", value=MSG_MISSING[_missing]))
            _said.append(MSG_MISSING[_missing])
        self.__info = " ".join(_said)

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    section = property(get_section, None)
    info = property(get_info, None)
