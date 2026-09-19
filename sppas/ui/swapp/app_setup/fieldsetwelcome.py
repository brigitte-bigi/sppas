"""
:filename: sppas.ui.swapp.app_setup.fieldsetwelcome.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Create a "Welcome" fieldset node of the setup app.

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
import logging
from whakerpy.htmlmaker import HTMLNode

from sppas.core.config import sg
from sppas.core.config import cfg
from sppas.core.coreutils import info
from sppas.ui.swapp.swappcore.wexc import sppasHTMLIncompleteFieldset
from sppas.ui.swapp.nodes import sppasHTMLCheckboxNode

from ..swappcore.swappsg import swapp_settings

from .basefieldset import SetupBaseFieldset

# ---------------------------------------------------------------------------


MSG_WELCOME = info(551, "install")   # "Welcome & conditions"
LEGEND_WELCOME = info(552, "install")
MSG_WELCOME1 = info(554, "install")
MSG_WELCOME2 = info(555, "install")
MSG_WELCOME3 = info(556, "install")
MSG_ACCEPT_REF = info(558, "install")
MSG_ACCEPT_PROD = info(559, "install")

# ---------------------------------------------------------------------------


class SetupHomeFieldset(SetupBaseFieldset):
    """Welcome fieldset of the setup page.

    """

    def __init__(self, parent: str, uri: str = ""):
        """Create the fieldset node.

        :param parent: (str) The parent 'id' of the fieldset.

        """
        field_title = LEGEND_WELCOME + " " + str(sg.__version__)
        super(SetupHomeFieldset, self).__init__(parent, "home_field", field_title, uri=uri)

        self._msg = MSG_WELCOME
        self.__create_content()

    # -----------------------------------------------------------------------

    def __create_content(self):

        # --Welcome messages
        txt = HTMLNode(self.identifier, None, "p",
                       attributes={"class": "welcome-panel"},
                       value=MSG_WELCOME1 + MSG_WELCOME2)
        self.append_child(txt)

        # -- Logos
        logos = f"""
         <img class="flex-item small-logo" src="{swapp_settings.logos}LPL_horiz.jpg" alt="LPL">
         <img class="flex-item small-logo" src="{swapp_settings.logos}cnrs.png" alt="CNRS">
         <img class="flex-item small-logo" src="{swapp_settings.logos}logo_AMU_bleu.png" alt="AMU">
         <img class="flex-item small-logo" src="{swapp_settings.logos}GPLv3.png" alt="GPLv3">
         <div class="flex-item small-logo">
             <img alt="Download count" src="https://img.shields.io/sourceforge/dm/sppas.svg" >
             <img alt="SourceForge"
                  src="https://sourceforge.net/sflogo.php?type=17&amp;group_id=3319074">
         </div>
        """
        container = HTMLNode(self.identifier, "logos_container", "section",
                             attributes={"aria-label": "Organizations involved",
                                         "class": "panel logos-panel width_full",
                                         "id": "logos_container"},
                             value=logos)
        self.append_child(container)

        # -- Author
        auth = HTMLNode(self.identifier, None, "p", value=MSG_WELCOME3)
        self.append_child(auth)

        # -- Agreements
        # They are pre-checked at the log level of the author only -- 1, below
        # any standard level and out of reach of the Configuration page: an
        # engagement is taken by the user, never by the software, and this is
        # what makes the tests bearable for the one who writes them.
        AUTHOR_LOG_LEVEL = 1
        box = sppasHTMLCheckboxNode(self.identifier, "check_ref", MSG_ACCEPT_REF, self._uri)
        self.append_child(box)
        if cfg.log_level <= AUTHOR_LOG_LEVEL:
            box.check()
        box = sppasHTMLCheckboxNode(self.identifier, "check_prod", MSG_ACCEPT_PROD, self._uri)
        self.append_child(box)
        if cfg.log_level <= AUTHOR_LOG_LEVEL:
            box.check()

    # -----------------------------------------------------------------------

    @property
    def __checkbox_ref(self):
        return self.get_child("check_ref")

    @property
    def __checkbox_prod(self):
        return self.get_child("check_prod")

    # -----------------------------------------------------------------------

    def validate(self):
        """Raise an exception if the input are not checked.

        """
        if self.__checkbox_ref.is_checked() is False or self.__checkbox_prod.is_checked() is False:
            logging.error("Checkbox validation failed.")
            raise sppasHTMLIncompleteFieldset("Accept citation")

    # -----------------------------------------------------------------------

    def process_event(self, event_name: str) -> int:
        """Process a received event.

        :param event_name: (str) Identifier name of the posted data
        :return: (int) status 200 if event handled or 205 if unknown

        """
        if event_name == "check_ref_input":
            self.__checkbox_ref.check(not self.__checkbox_ref.is_checked())
            return 200

        elif event_name == "check_prod_input":
            self.__checkbox_prod.check(not self.__checkbox_prod.is_checked())
            return 200

        return 205
