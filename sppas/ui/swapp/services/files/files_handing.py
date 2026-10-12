"""
:filename: sppas.ui.swapp.services.files.files_handing.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: What is given to an app, and what comes back from it.

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
from sppas.src.wkps import sppasWorkspace

from .files_workspace import swappWorkspaceFiles

# ---------------------------------------------------------------------------


class swappAppExchange:
    """Give an app the files it has to treat, and read what it gives back.

    What is given to an app is created for it: the workspace and the files in
    it are new objects, so what an app does with them reaches nothing else.

    """

    def __init__(self, workspace_files: swappWorkspaceFiles):
        """Create the exchange with the apps.

        :param workspace_files: (swappWorkspaceFiles) Access to the files of a workspace
        :raises: sppasTypeError: The given access is not a swappWorkspaceFiles

        """
        if isinstance(workspace_files, swappWorkspaceFiles) is False:
            raise sppasTypeError(workspace_files, "swappWorkspaceFiles")

        self.__files = workspace_files

    # -----------------------------------------------------------------------

    def for_app(self) -> sppasWorkspace:
        """Return a workspace with the files to be treated in it.

        The files are the checked ones, and no other. They are added to a new
        workspace, so no object of the given one is shared.

        :return: (sppasWorkspace) Can hold no file at all

        """
        _filenames = list()
        for _one in self.__files.checked_files():
            _filenames.append(_one.get_id())

        return swappWorkspaceFiles.make_workspace(_filenames)

    # -----------------------------------------------------------------------

    def back_from_app(self, workspace: sppasWorkspace) -> list:
        """Return the names of the files an app added to what it was given.

        A file of the given workspace which is unknown to the workspace the
        files come from is a file the app produced. What the app changed
        otherwise is left out.

        The cause an app states for a file it made nothing of is not read
        here: it is a sentence the app writes, and shows itself beside the
        file it concerns. B16

        :param workspace: (sppasWorkspace) Workspace an app gives back
        :raises: sppasTypeError: The given workspace is not a sppasWorkspace
        :return: (list of str) Names of the added files, with their path

        """
        _added = list()
        for _one in swappWorkspaceFiles.known_files(workspace):
            if self.__files.is_known(_one.get_id()) is False:
                _added.append(_one.get_id())

        return _added
