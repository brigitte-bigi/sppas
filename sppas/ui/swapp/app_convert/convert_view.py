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

from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import HTMLTree
from whakerpy.htmlmaker import TagNode

from sppas.core.config import sg
from sppas.ui import _

from ..swapp_base.swapp_view import swappBaseView
from ..swapp_core.swappsg import swapp_settings

from .convert_record import swappConvertRecord
from .convert_record import TASK_CONVERT
from .convert_record import MISSING_BATCH
from .convert_panels import swappFormatsPanel
from .convert_panels import swappDestinationPanel
from .convert_panels import swappComparePanel
from .convert_panels import swappGeneralPanel
from .convert_panels import swappResultsPanel

# ---------------------------------------------------------------------------

ID_SECTION = "convert_section"

MSG_HEADER = f"SPPAS {sg.__release__} » " + _("Convert")
MSG_TITLE = _("Conversion options")
MSG_MISSING = {MISSING_BATCH: _("No file is checked to be converted.")}

BODY_SCRIPT = f"""
        import {{ ConvertManager }} from '/{swapp_settings.js}sppas.js';
        import SwappFiles from '/{swapp_settings.js}swapp_files.js';
        const convertManager = new ConvertManager();
        convertManager.handleConvertManagerOnLoad();
        const swappFiles = new SwappFiles();
        swappFiles.handleSwappFilesOnLoad();
"""

# ---------------------------------------------------------------------------


class swappConvertView(swappBaseView):
    """View class responsible for populating the page of Convert.

    It builds the panel of the conversion, made of its five panels, from
    a record. It decides nothing: what it shows was decided before it was
    called.

    """

    def __init__(self, tree: HTMLTree):
        """Initialize and populate the Convert view structure.

        :param tree: (HTMLTree) An existing HTML tree to populate
        :raises: TypeError: tree is not an instance of HTMLTree

        """
        if isinstance(tree, HTMLTree) is False:
            raise TypeError("swappConvertView: tree must be an instance of HTMLTree. "
                            "Got {} instead.".format(type(tree)))
        self.__section = None
        super(swappConvertView, self).__init__(tree, MSG_HEADER)

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
        self.append_trace_link_button(self._htree.body_nav)

    # -----------------------------------------------------------------------

    def populate_body_script(self):
        """Override. Populate the script body section."""
        self._htree.body_script.add_attribute("type", "module")
        self._htree.body_script.set_value(BODY_SCRIPT)

    # -----------------------------------------------------------------------
    # Update the tree -- for baking the page
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
        _section = TagNode(self._htree.body_main.identifier, ID_SECTION, "div",
                           attributes={"id": ID_SECTION, "class": "panel"})
        self._htree.body_main.append_child(_section)
        _section.append_child(HTMLNode(_section.identifier, None, "h3", value=MSG_TITLE))

        _flex = TagNode(_section.identifier, None, "div", attributes={"class": "flex-panel"})
        _section.append_child(_flex)
        _flex.append_child(swappFormatsPanel(_flex.identifier, _shown.get("formats", list()),
                                             _conversion.destination))
        _flex.append_child(swappDestinationPanel(_flex.identifier, _conversion.destination,
                                                 _shown.get("properties", list()),
                                                 _shown.get("held", dict())))

        _section.append_child(swappComparePanel(_section.identifier, _shown.get("formats", list()),
                                                _shown.get("properties", list())))
        _section.append_child(swappGeneralPanel(_section.identifier, record.serialize(),
                                                _conversion.override, _conversion.heuristic))

        if "results" in _shown:
            _section.append_child(swappResultsPanel(_section.identifier, _shown["results"]))

        if record.task == TASK_CONVERT:
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
        for _missing in missing:
            _dialog.append_child(HTMLNode(_dialog.identifier, None, "p", value=MSG_MISSING[_missing]))
        _dialog.set_attribute("class", "info")

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    section = property(get_section, None)
