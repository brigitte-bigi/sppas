"""
:filename: sppas.ui.swapp.app_convert.convert_remediation.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The transformations of the annotations of a file.

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


class swappModelRemediation:
    """Transform annotations in memory, as the answers of the options ask.

    It is given a content and gives back a content: no file, no path, no
    batch. A remediation produces a new content, which is verified again
    against what the destination holds, and a remediation is applied at most
    once for one file.

    """

    def remediate(self, content, properties: dict, answers: dict) -> tuple:
        """Return a content the destination holds, or why it cannot.

        :param content: (sppasTranscription) The content of one file
        :param properties: (dict) True or False for every property of the destination
        :param answers: (dict) The answer standing for each option, by option
        :raises: NotImplementedError
        :return: (tuple) The contents to be written, and the cause of a refusal or None

        """
        raise NotImplementedError

    # -----------------------------------------------------------------------

    def what_was_transformed(self) -> list:
        """Return the remediations which changed the last content.

        :raises: NotImplementedError
        :return: (list of str) Empty when none did

        """
        raise NotImplementedError
