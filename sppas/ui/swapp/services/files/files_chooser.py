"""
:filename: sppas.ui.swapp.services.files.files_chooser.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The files a person chooses on the machine SPPAS runs on.

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

import logging
import os

from sppas.ui.agnostic.filechooser.filechooser_mixin import FileChooserMixin

# ---------------------------------------------------------------------------

MSG_CHOOSE = "Choose the files to be treated"
MSG_NO_CHOOSER = "The file chooser could not be opened on this machine."

# ---------------------------------------------------------------------------


class swappFileChooser:
    """Convenient class to ask a person for files of the machine.

    It is the way in of the files which stand already where SPPAS reads
    them: the browser gives a content and never a path, so the path is asked
    for where the files are, which is the machine the server runs on. It is
    the only class of this service which opens a dialog, and it opens none
    of its own: what it asks is what SPPAS asks everywhere else.

    """

    def __init__(self, chooser=None):
        """Create the access to the file chooser of SPPAS.

        :param chooser: (FileChooserMixin) What asks the person, None for the one of SPPAS

        """
        if chooser is None:
            chooser = FileChooserMixin()

        self.__chooser = chooser
        self.__why_nothing = ""

    # -----------------------------------------------------------------------

    def ask_for_files(self) -> list:
        """Return the files a person chose, with their path.

        The dialog is asked as the test page of swapp asks it, and no type is
        offered to it: what SPPAS reads is answered by the acceptance, and a
        dialog which judged it would judge it twice.

        Nothing is raised: a person who chooses nothing, and a machine which
        cannot open a dialog, both give no file -- and a caller which asked
        has nothing to correct in either case.

        :return: (list of str) Empty when no file was chosen

        """
        self.__why_nothing = ""
        try:
            _chosen = self.__chooser.ask_file(
                mode="openfile",
                title=MSG_CHOOSE,
                multiple=True,
                filetypes=None,
                defaultextension=None)
        except Exception as e:
            logging.error("No file could be asked for: {}".format(e))
            self.__why_nothing = MSG_NO_CHOOSER
            return list()

        _files = swappFileChooser.validate_chosen(_chosen)
        if len(_files) == 0 and len(str(_chosen)) > 0:
            logging.error("No file was obtained. What was answered instead: "
                          "{}".format(_chosen))
            self.__why_nothing = MSG_NO_CHOOSER

        return _files

    # -----------------------------------------------------------------------

    def why_nothing(self) -> str:
        """Return why no file came back, when it is not because none was chosen.

        A person who closed the dialog chose nothing, and there is nothing to
        say of it. A dialog which could not open is another thing, and she
        would otherwise read the same silence in both cases.

        :return: (str) Empty when nothing is to be said

        """
        return self.__why_nothing

    # -----------------------------------------------------------------------

    @staticmethod
    def validate_chosen(chosen) -> list:
        """Return the chosen files, as a list of names.

        One name, a list of them, or an error said in a sentence: the three
        are what a dialog gives back, and only the files which stand on the
        disk are kept -- a sentence saying what went wrong is not the name of
        a file, and it would be taken for one.

        :param chosen: (str|list) What the dialog gave back
        :return: (list of str) Empty when nothing was chosen

        """
        if chosen is None:
            return list()
        if isinstance(chosen, str) is True:
            chosen = [chosen]
        if isinstance(chosen, (list, tuple)) is False:
            return list()

        _files = list()
        for _one in chosen:
            if isinstance(_one, str) is False:
                continue
            if os.path.isfile(_one.strip()) is True:
                _files.append(_one.strip())

        return _files
