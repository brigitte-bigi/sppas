"""
:filename: sppas.ui.swapp.app_convert.convert_provision.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The access of Convert to the provision of files.

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

from sppas.core.coreutils import sppasTypeError

from ..services.files import swappFilesManager

# ---------------------------------------------------------------------------


class swappModelProvision:
    """Call the provision of files on files: the batch, and what comes back.

    It is given the manager of that service, which the response holds, and it
    is the only class of this application which calls it on files. It reads
    the batch, says what it takes and gives back while the batch is
    converted, gives back what was produced, and says when it has finished.

    """

    def __init__(self, manager: swappFilesManager):
        """Create the access to the provision of files.

        :param manager: (swappFilesManager) What the response holds of that service
        :raises: sppasTypeError: The given manager is not a swappFilesManager

        """
        if isinstance(manager, swappFilesManager) is False:
            raise sppasTypeError(manager, "swappFilesManager")

        self.__manager = manager

    # -----------------------------------------------------------------------

    def batch(self):
        """Return the workspace holding the files to be treated.

        :return: (sppasWorkspace) Can hold no file at all

        """
        return self.__manager.files_for_app()

    # -----------------------------------------------------------------------

    def lock(self, filenames: list) -> int:
        """Say the files are taken, to be converted.

        :param filenames: (list of str) Names of the files, with their path
        :return: (int) Number of locked files

        """
        return self.__manager.lock(filenames)

    # -----------------------------------------------------------------------

    def release(self, filenames: list) -> int:
        """Say the files are given back.

        :param filenames: (list of str) Names of the files, with their path
        :return: (int) Number of released files

        """
        return self.__manager.release(filenames)

    # -----------------------------------------------------------------------

    def produced(self, workspace) -> dict:
        """Give back the workspace which was handed, holding what was produced.

        :param workspace: (sppasWorkspace) The batch, with the files written in it
        :return: (dict) Names of the produced files, with their path, by root

        """
        return self.__manager.produced(workspace)

    # -----------------------------------------------------------------------

    def finished(self) -> None:
        """Say the batch has been treated."""
        self.__manager.consumes({"task": "finished"})
