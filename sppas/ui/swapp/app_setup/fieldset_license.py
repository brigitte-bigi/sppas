"""
:filename: sppas.ui.swapp.app_setup.fieldset_license.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Create a "License" fieldset node of the setup app.

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
from whakerpy.htmlmaker import HTMLHr

from sppas.core.config import cfg
from sppas.core.coreutils import info
from sppas.ui.swapp.swapp_core.swapp_exc import swappHTMLIncompleteFieldset
from sppas.ui.swapp.nodes import swappHTMLCheckboxNode

from .base_fieldset import swappSetupBaseFieldset

# ---------------------------------------------------------------------------


MSG_LICENSE = info(561, "install")   # "Welcome & conditions"
LEGEND_LICENSE = info(562, "install")
MSG_ACCEPT_LICENSE = info(568, "install")

LIC1 = info(563, "install")
LIC2 = info(564, "install")
LIC3 = info(565, "install")
LIC4 = info(566, "install")

# A short license text in case the file of the GPL can't be read.
LICENSE_AGPL = """

<h2>GNU Affero General Public License version 3 or later</h2>

<p><a href="https://www.gnu.org/licenses/agpl-3.0.html">
https://www.gnu.org/licenses/agpl-3.0.html</a></p>

<p>SPPAS is free software; you can redistribute it and/or
modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation; either version 3 of
the License, or (at your option) any later version.</p>

<p>SPPAS is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.</p>

<p>You should have received a copy of the GNU Affero General Public License
along with SPPAS; if not, write to the Free Software Foundation,
Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.</p>

"""

LICENSE_FDL = """

<h2>GNU Free Documentation License version 1.3</h2>

<p><a href="https://www.gnu.org/licenses/fdl-1.3.en.html">
https://www.gnu.org/licenses/fdl-1.3.en.html</a></p>

<p>Permission is granted to copy, distribute and/or modify this document
   under the terms of the GNU Free Documentation License, Version 1.3
   or any later version published by the Free Software Foundation;
   with no Invariant Sections, no Front-Cover Texts, and no Back-Cover Texts.
   A copy of the license is included in the section entitled "GNU
   Free Documentation License".</p>

"""

LICENSE_CC_BY_NC = """

<h2>Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)</h2>

<p><a href="https://creativecommons.org/licenses/by-nc/4.0/">
https://creativecommons.org/licenses/by-nc/4.0/</a></p>

<h3>You are free to:</h3>
<ul>
  <li><b>Share</b> — copy and redistribute the material in any medium or format</li>
  <li><b>Adapt</b> — remix, transform, and build upon the material</li>
</ul>
<p>The licensor cannot revoke these freedoms as long as you follow the license terms.</p>

<h3>Under the following terms:</h3>
<ul>
  <li><b>Attribution</b> — You must give appropriate credit, provide a link 
  to the license, and indicate if changes were made. You may do so in any 
  reasonable manner, but not in any way that suggests the licensor endorses 
  you or your use.</li>
  <li><b>NonCommercial</b> — You may not use the material for commercial purposes.</li>
</ul>
<p>No additional restrictions — You may not apply legal terms or technological 
measures that legally restrict others from doing anything the license permits.</p>

"""

# ---------------------------------------------------------------------------


class swappSetupLicenseFieldset(swappSetupBaseFieldset):
    """Terms and conditions fieldset of the setup page.

    A checkbox must be checked in order to validate the field.

    """

    def __init__(self, parent, uri: str = ""):
        super(swappSetupLicenseFieldset, self).__init__(parent, "license_field", LEGEND_LICENSE)
        self._msg = MSG_LICENSE

        # --- List of licenses
        lilist = HTMLNode(self.identifier, "licences_list", "ol", attributes={"class": "license-ol"})
        self.append_child(lilist)
        for limsg in (LIC1, LIC2, LIC3, LIC4):
            linode = HTMLNode(lilist.identifier, None, "li",
                              value=limsg)
            lilist.append_child(linode)

        # --- The licenses agreement
        # Pre-checked at the log level of the author only -- 1, below any
        # standard level and out of reach of the Configuration page: an
        # engagement is taken by the user, never by the software.
        AUTHOR_LOG_LEVEL = 1
        checkbox = swappHTMLCheckboxNode(self.identifier, "check_license", MSG_ACCEPT_LICENSE, uri=uri)
        if cfg.log_level <= AUTHOR_LOG_LEVEL:
            checkbox.check()
        self.append_child(checkbox)

        # ---  The full GNU AGPL license text or the short one
        self.append_child(HTMLHr(self.identifier))
        license_text = (LICENSE_AGPL, LICENSE_FDL, LICENSE_CC_BY_NC)
        text = HTMLNode(self.identifier, None, "article", value="<hr/>\n".join(license_text))
        self.append_child(text)

    # -----------------------------------------------------------------------

    @property
    def __checkbox(self):
        return self.get_child("check_license")

    # -----------------------------------------------------------------------

    def validate(self):
        """Raise an exception if the input is not checked.

        """
        if self.__checkbox.is_checked() is False:
            raise swappHTMLIncompleteFieldset("Accept License")

    # -----------------------------------------------------------------------

    def process_event(self, event_name):
        """Process a received event.

        :param event_name: (str) Identifier name of the posted data
        :return: (int) status 200 if event handled or 205 if unknown

        """
        if event_name == "check_license_input":
            self.__checkbox.check(not self.__checkbox.is_checked())
            return 200
        return 205
