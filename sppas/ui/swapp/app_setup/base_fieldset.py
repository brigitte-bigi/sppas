"""
:filename: sppas.ui.swapp.app_setup.base_fieldset.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: A base class to create a fieldset node of the setup app.

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

    Copyright (C) 2011-2025  Brigitte Bigi, CNRS
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

# -----------------------------------------------------------------------


class swappSetupBaseFieldset(HTMLNode):
    """A base class for any fieldset of the setup page.

    """

    def __init__(self, parent, identifier, legend=None, uri=""):
        super(swappSetupBaseFieldset, self).__init__(parent, identifier, "fieldset")
        if identifier is not None:
            self.set_attribute("id", identifier)
        self.set_attribute("class", "wizard-fieldset")
        if legend is not None:
            legend = HTMLNode(self.identifier, "field_legend", "legend", value="{:s}".format(legend))
            self.append_child(legend)
        # A short version of the legend
        self._msg = ""
        # The page uri of the fieldset
        self._uri = uri

    # -----------------------------------------------------------------------

    def get_msg(self):
        """Return the title message of the fieldset (str)."""
        return self._msg

    # -----------------------------------------------------------------------

    def validate(self):
        """Raise an exception if the fieldset is not fulfilled or return None.

        :raises: IncompleteFieldset

        """
        return None

    # -----------------------------------------------------------------------

    def process_event(self, event):
        """Process a received event.

        :param event: The received event.
        :return: (int) Status value (default: 205)

        """
        return 205
