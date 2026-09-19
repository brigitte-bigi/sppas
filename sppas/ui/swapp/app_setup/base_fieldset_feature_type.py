"""
:filename: sppas.ui.swapp.app_setup.base_fieldset_feature_type.py
:author: Brigitte Bigi
:contributor: Florian Lopitaux
:contact: contact@sppas.org
:summary: Create a base class for a "Feature" type fieldset node of the setup app.

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
import sys
from whakerpy.htmlmaker import HTMLNode

from sppas.core import cfg
from sppas.core.coreutils import msg
from sppas.core.coreutils import info
from sppas.core.preinstall import Installer

from sppas.ui.swapp.nodes import swappHTMLCheckboxNode

from .base_fieldset import swappSetupBaseFieldset

# ---------------------------------------------------------------------------


MSG_FEAT = msg("Feature", "install")
MSG_DESCR = msg("Description", "install")
MSG_FEATURES = msg("Features", "install")
LEGEND_FEATURES = msg("Check the SPPAS optional features", "install")
INFO_FEATURES = info(504, "install")

# ---------------------------------------------------------------------------


class swappSetupFeatureTypeFieldset(swappSetupBaseFieldset):
    """List of features fieldset of the setup page.

    """

    def __init__(self,
                 parent_id: str,
                 fieldset_id: str,
                 installer: Installer,
                 feature_type: str,
                 legend: str = LEGEND_FEATURES,
                 uri: str = ""
                 ):
        super(swappSetupFeatureTypeFieldset, self).__init__(parent_id, fieldset_id, legend, uri)

        self._installer = installer
        self.__feature_type = feature_type
        self._checkables = dict()

        # A default message to shortly describe the fieldset
        self._msg = MSG_FEATURES

        # Create the content of the fieldset
        self._create_content()

    # -----------------------------------------------------------------------

    def process_event(self, event_name: str) -> dict:
        """Process a received event.

        :param event_name: (str) Identifier name of the posted data
        :return: (dict[str, bool] or None) dict if event handled or None if unknown

        """
        check_name = event_name.replace("_input", "")
        checkbox_to_change = None

        for checkable in self._checkables.values():
            if checkable.identifier == check_name:
                checkbox_to_change = dict()
                checkable.check(not checkable.is_checked())

                # update all checkbox that depends on this checkable
                # it can happen when two features are "linked" (enabling one implied
                # to enable/disable another one)
                for feature_id in self._installer.features_ids(self.__feature_type):
                    current_checkable = self._checkables[feature_id]

                    if current_checkable.is_checked() != self._installer.enable(feature_id):
                        current_checkable.check(self._installer.enable(feature_id))

                        key_name = f"feature_{feature_id}_input"
                        checkbox_to_change[key_name] = checkable.is_checked()

        return checkbox_to_change

    # -----------------------------------------------------------------------
    # Private: construct the nodes
    # -----------------------------------------------------------------------

    def _create_content(self):
        """Create and fill-in the fieldset.

        """
        # Put the list of features of the given type in a table.
        table = HTMLNode(self.identifier, None, "table")
        table.set_attribute("class", "features-table")
        self.append_child(table)

        # Create the features installation message, as table caption.
        txt = HTMLNode(table.identifier, None, "caption", value=INFO_FEATURES)
        txt.add_attribute("class", "features-caption")
        table.append_child(txt)

        tbody = HTMLNode(table.identifier, None, "tbody")
        table.append_child(tbody)

        # Fill-in the lines of the table
        if self._installer is not None:
            self._fill_in_tbody(tbody)

    # -----------------------------------------------------------------------

    def _fill_in_tbody(self, tbody_node: HTMLNode):
        """Fill-in the table with two columns: checkbox and brief+description.

        :param tbody_node: (HTMLNode) HTML node to fill in the table body

        """
        for fid in self._installer.features_ids(self.__feature_type):
            tr = HTMLNode(tbody_node.identifier, None, "tr")
            tbody_node.append_child(tr)
            self._fill_in_tr(tr, fid)

    # -----------------------------------------------------------------------

    def _fill_in_tr(self, tr_node: HTMLNode, fid: str):
        """Fill-in the table with two columns: checkbox and brief+description.

        :param tr_node: (HTMLNode) HTML node to fill in the table row

        """
        td1 = HTMLNode(tr_node.identifier, None, "td",
                       attributes={"class": "checkable_col"})
        tr_node.append_child(td1)
        checkable = swappHTMLCheckboxNode(td1.identifier, "feature_" + fid, fid, self._uri)

        # -------------------------------
        # This should not be here because the view should not decide anything!
        disabled = (
                (fid == "sppas" and cfg.update_info.get('update') is False)
                or (fid == "mactools" and sys.platform != "darwin")
                or (fid == "wintools" and sys.platform.startswith("win") is False)
        )
        if disabled is True:
            checkable.add_input_attribute("disabled", None)
        else:
            checkable.check(self._installer.enable(fid))
        # -------------------------------
        td1.append_child(checkable)
        self._checkables[fid] = checkable

        td2 = HTMLNode(tr_node.identifier, None, "td")
        tr_node.append_child(td2)
        brief = HTMLNode(td2.identifier, None, "p", attributes={"class": "p-brief"},
                         value=self._installer.brief(fid))
        descr = HTMLNode(td2.identifier, None, "p", attributes={"class": "p-descr"},
                         value=self._installer.description(fid))
        td2.append_child(brief)
        td2.append_child(descr)
