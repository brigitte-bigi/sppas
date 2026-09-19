"""
:filename: sppas.ui.swapp.app_setup.fieldset_install.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Create an "Install" fieldset node of the setup app.

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
from whakerpy.htmlmaker import EmptyNode
from whakerpy.htmlmaker import HTMLHr

from sppas.core.coreutils import msg
from sppas.core.coreutils import info

from ..nodes import swappProgressBar

from .base_fieldset import swappSetupBaseFieldset

# ---------------------------------------------------------------------------


MSG_COMPLETED = msg("Installation", "install")
MSG_ENABLED = msg("enabled", "install")
MSG_DISABLED = msg("disabled", "install")
LEGEND_COMPLETED = info(573, "install")
INFO_INSTALL_FINISHED = info(560, "install")
INFO_SEE_LOGS = info(512, "install")

# ---------------------------------------------------------------------------


class swappSetupInstallFieldset(swappSetupBaseFieldset):
    """Completed fieldset of the setup page.

    """

    def __init__(self, parent):
        super(swappSetupInstallFieldset, self).__init__(parent, "install_field", LEGEND_COMPLETED)
        self._msg = MSG_COMPLETED
        self.__progress = None

    # -----------------------------------------------------------------------

    def create_progress(self):
        """Create the node to show progress.

        :return: (sppasBaseProgress)

        """
        self.__progress = swappProgressBar(self.identifier)
        self.__progress.set_header("")
        self.__progress.set_text("")
        self.append_child(self.__progress.get_node())
        return self.__progress

    # -----------------------------------------------------------------------

    def get_progress(self):
        """Return the progress node."""
        return self.__progress

    # -----------------------------------------------------------------------

    def completed(self, errors, installer):
        """Append the completed messages to the node.

        :param errors: (list of str) List of installation errors or warnings
        :param installer: (sppasInstallerDeps)

        """
        if self.__progress is not None:
            self.remove_child(self.__progress.ID)
        self.__progress = None

        txt = HTMLNode(self.identifier, None, "p",
                       value=INFO_INSTALL_FINISHED + "<br>" + INFO_SEE_LOGS)
        self.append_child(txt)

        # Show the errors
        if len(errors) > 0:
            self.append_child(HTMLHr(self.identifier))
            pre = HTMLNode(self.identifier, None, "code")
            self.append_child(pre)
            for line in errors:
                msg = self.format_to_html(line)
                txt = HTMLNode(pre.identifier, None, "p", value=msg)
                pre.append_child(txt)

        self.append_child(EmptyNode(self.identifier, None, "hr"))

        # Show the list of features, and their status
        if installer is not None:
            for feat_type in ("deps", "lang", "annot", "spin"):
                ul = HTMLNode(self.identifier, None, "ul")
                self.append_child(ul)
                for fid in installer.features_ids(feat_type):
                    text = MSG_ENABLED if installer.enable(fid) is True else MSG_DISABLED
                    li = HTMLNode(ul.identifier, None, "li", value=fid + ": " + text)
                    ul.append_child(li)
                self.append_child(EmptyNode(self.identifier, None, "br"))

    # -----------------------------------------------------------------------

    def format_to_html(self, msg):
        """Format a message with HTML tags.

        :param msg: (str)
        :return: (str)

        """
        msg = msg.replace("\t", "    ")
        msg = msg.replace("\\t", "    ")
        msg = msg.replace("\r", " ")
        msg = msg.replace("\n", " <br/>")
        msg = msg.replace("\\n", " <br/>")
        msg = msg.replace("\\'", "&apos;")
        msg = msg.replace('\\"', "&quot;")

        return msg
