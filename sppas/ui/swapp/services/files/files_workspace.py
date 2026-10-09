"""
:filename: sppas.ui.swapp.services.files.files_workspace.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The files known to a workspace, and their states.

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
from sppas.src.wkps import States

from ...swapp_core.swappsg import swapp_wkps
from ...swapp_core.swappsg import notify_wkp_changed

# ---------------------------------------------------------------------------

# What an app is allowed to do to the copy it worked on, and the only states
# which are reported on the workspace of the machine.
REPORTED_STATES = (States().CHECKED, States().UNUSED)

# ---------------------------------------------------------------------------


class swappWorkspaceFiles:
    """Convenient class to access the files of a workspace and their states.

    Every operation is one or two calls to a workspace: a file is checked to be
    treated, locked while it is being treated, and checked again when it is
    given back. The two other states are neither read nor written. The only
    rule held here is that a produced file is known and checked.

    """

    def __init__(self, workspace: sppasWorkspace | None = None, name: str = ""):
        """Create the access to the files of a workspace.

        :param workspace: (sppasWorkspace) Workspace to work on, None to get a new one
        :param name: (str) The name it is managed under, which is what a person is told
        :raises: sppasTypeError: The given workspace is not a sppasWorkspace
        :raises: sppasTypeError: The given name is not a string

        """
        if workspace is None:
            workspace = sppasWorkspace()
        if isinstance(workspace, sppasWorkspace) is False:
            raise sppasTypeError(workspace, "sppasWorkspace")
        if isinstance(name, str) is False:
            raise sppasTypeError(name, "str")

        self.__wkp = workspace
        self.__name = name.strip()

    # -----------------------------------------------------------------------

    @staticmethod
    def make_workspace(filenames: list | None = None) -> sppasWorkspace:
        """Return a workspace knowing the given files, and set to be treated.

        :param filenames: (list of str) Names of the files, with their path
        :raises: sppasTypeError: The given names are not a list
        :raises: OSError: A given name cannot be read
        :return: (sppasWorkspace) With no file in it if no name was given

        """
        _made = swappWorkspaceFiles(sppasWorkspace())
        if filenames is not None:
            _made.make_known(filenames)
            _made.check(filenames)

        return _made.__wkp

    # -----------------------------------------------------------------------

    @staticmethod
    def validate_filenames(filenames: list | tuple) -> list:
        """Return the given names if they are a list of names.

        A single name given instead of a list would be walked letter by
        letter, so it is refused.

        :param filenames: (list of str) Names to be validated
        :raises: sppasTypeError: The given names are not a list nor a tuple
        :return: (list of str) The given names

        """
        if isinstance(filenames, (list, tuple)) is False:
            raise sppasTypeError(filenames, "list")

        return filenames

    # -----------------------------------------------------------------------

    def set_workspace(self, workspace: sppasWorkspace) -> None:
        """Set the workspace the files are known to.

        It is the one a request carried, or the one an app holds: this class
        works on what it is given, and holds none of its own.

        :param workspace: (sppasWorkspace) Workspace to work on
        :raises: sppasTypeError: The given workspace is not a sppasWorkspace

        """
        if isinstance(workspace, sppasWorkspace) is False:
            raise sppasTypeError(workspace, "sppasWorkspace")

        self.__wkp = workspace

    # -----------------------------------------------------------------------

    def remove(self, filenames: list) -> int:
        """Remove files of the workspace.

        Removing a file which is not known does nothing.

        :param filenames: (list of str) Names of the files, with their path
        :raises: sppasTypeError: The given names are not a list
        :return: (int) Number of removed files, roots and paths

        """
        swappWorkspaceFiles.validate_filenames(filenames)

        _nb_removed = 0
        for _filename in filenames:
            _nb_removed += len(self.__wkp.remove_file(_filename))

        return _nb_removed

    # -----------------------------------------------------------------------

    def workspace(self) -> sppasWorkspace:
        """Return the workspace the files are known to.

        It is given to what carries a request from one to the next, and never
        to an app: what an app receives is made for it.

        :return: (sppasWorkspace)

        """
        return self.__wkp

    # -----------------------------------------------------------------------

    def name(self) -> str:
        """Return the name of the workspace.

        It is the one the workspaces are managed under, and it is given when
        this class is created: what a workspace carries of its own is an
        identifier, which says nothing to a person.

        :return: (str) Empty when none was given

        """
        return self.__name

    # -----------------------------------------------------------------------

    def exists(self) -> bool:
        """Return whether a workspace holds files to be treated.

        A workspace with no file in it is one to be filled, and not one to
        be used.

        :return: (bool)

        """
        return self.__wkp.is_empty() is False

    # -----------------------------------------------------------------------

    def is_known(self, filename: str) -> bool:
        """Return True if the given name is a file of the workspace.

        :param filename: (str) Name of a file, with its path
        :return: (bool)

        """
        return self.__wkp.get_object(filename) is not None

    # -----------------------------------------------------------------------

    @staticmethod
    def known_files(workspace: sppasWorkspace) -> list:
        """Return every file of the given workspace, whatever its state.

        A workspace gives its files by state, and the three levels are walked
        to get them all.

        :param workspace: (sppasWorkspace) Workspace to be read
        :raises: sppasTypeError: The given workspace is not a sppasWorkspace
        :return: (list of FileName) Can be empty

        """
        if isinstance(workspace, sppasWorkspace) is False:
            raise sppasTypeError(workspace, "sppasWorkspace")

        _files = list()
        for _path in workspace.get_paths():
            for _root in _path:
                for _one in _root:
                    _files.append(_one)

        return _files

    # -----------------------------------------------------------------------

    def make_known(self, filenames: list) -> int:
        """Add files to the workspace.

        A file which is already known is not added twice, and a file which is
        not on the disk is known as a missing one.

        :param filenames: (list of str) Names of the files, with their path
        :raises: sppasTypeError: The given names are not a list
        :raises: OSError: A given name cannot be read
        :return: (int) Number of added files, roots and paths

        """
        swappWorkspaceFiles.validate_filenames(filenames)

        _nb_added = 0
        for _filename in filenames:
            _added = self.__wkp.add_file(_filename)
            if _added is not None:
                _nb_added += len(_added)

        return _nb_added

    # -----------------------------------------------------------------------

    def check(self, filenames: list) -> int:
        """Set the given files to be treated.

        :param filenames: (list of str) Names of the files, with their path
        :raises: sppasTypeError: The given names are not a list
        :return: (int) Number of files whose state was changed

        """
        return self.__set_state(filenames, States().CHECKED)

    # -----------------------------------------------------------------------

    def lock(self, filenames: list) -> int:
        """Set the given files as being treated.

        A locked file is no longer a checked one, so it is in nothing which is
        given to an app.

        The state is set on the workspace which is held as well, and at once:
        a lock is of use to whoever does not hold it, and one which stayed in
        the copy would be seen by nobody -- the other interface could take a
        file an app is treating. It is the one state which does not wait for
        the copy to be given back.

        :param filenames: (list of str) Names of the files, with their path
        :raises: sppasTypeError: The given names are not a list
        :return: (int) Number of files whose state was changed

        """
        _nb_changed = self.__set_state(filenames, States().LOCKED)
        self.__report_state(filenames, States().LOCKED)

        return _nb_changed

    # -----------------------------------------------------------------------

    def release(self, filenames: list) -> int:
        """Set the given files to be treated again.

        Releasing a file which is not locked does nothing.

        The workspace which is held is told at once, as it was told of the
        lock: a file which is free again is free for whoever asks.

        :param filenames: (list of str) Names of the files, with their path
        :raises: sppasTypeError: The given names are not a list
        :return: (int) Number of files whose state was changed

        """
        _nb_changed = self.__set_state(filenames, States().CHECKED)
        self.__report_state(filenames, States().CHECKED)

        return _nb_changed

    # -----------------------------------------------------------------------

    def checked_files(self) -> list:
        """Return the files to be treated.

        :return: (list of FileName) Can be empty

        """
        return self.__wkp.get_filename_from_state(States().CHECKED)

    # -----------------------------------------------------------------------

    def locked_files(self) -> list:
        """Return the files which are being treated.

        :return: (list of FileName) Can be empty

        """
        return self.__wkp.get_filename_from_state(States().LOCKED)

    # -----------------------------------------------------------------------

    def write_produced(self, filenames: list) -> int:
        """Add produced files to the workspace, and set them to be treated.

        The state of the other files is left as it is.

        :param filenames: (list of str) Names of the files, with their path
        :raises: sppasTypeError: The given names are not a list
        :raises: OSError: A given name cannot be read
        :return: (int) Number of added files, roots and paths

        """
        _nb_added = self.make_known(filenames)
        self.check(filenames)

        return _nb_added

    # -----------------------------------------------------------------------

    def roots_of(self, filenames: list) -> dict:
        """Return the given files, grouped by the root they stand under.

        The grouping is the work of the workspace, and it is read where it is
        written: a name the workspace does not know is left out, and no group
        is made here.

        :param filenames: (list of str) Names of the files, with their path
        :raises: sppasTypeError: The given names are not a list
        :return: (dict) The given names, by root, empty when none of them is known

        """
        swappWorkspaceFiles.validate_filenames(filenames)

        _grouped = dict()
        for _path in self.__wkp.get_paths():
            for _root in _path:
                for _one in _root:
                    if _one.get_id() in filenames:
                        _of_root = _grouped.get(_root.get_id(), list())
                        _of_root.append(_one.get_id())
                        _grouped[_root.get_id()] = _of_root

        return _grouped

    # -----------------------------------------------------------------------

    # -----------------------------------------------------------------------

    def give_back(self) -> int:
        """Report on the workspace of the machine what an app was allowed to do.

        An app adds files, checks them and unchecks them, and those changes
        are the only ones reported: a file it removed, and a state this domain
        does not set, are left where they were made. A file which is locked is
        not reported either -- an app which has finished holds nothing any
        more, which is T12.

        Nothing is reported when the machine holds no workspace to report on:
        what one request carries is then the whole of it, and it is given back
        to nobody. Whoever holds the workspace is told once, and only when
        something was reported. PF13

        :raises: OSError: A file of the copy cannot be read
        :return: (int) Number of reported files

        """
        _held = swapp_wkps.data
        if isinstance(_held, sppasWorkspace) is False:
            return 0
        if _held.is_empty() is True:
            return 0

        _nb_reported = 0
        for _one in swappWorkspaceFiles.known_files(self.__wkp):
            if _one.get_state() in REPORTED_STATES:
                if swappWorkspaceFiles.__report(_held, _one) is True:
                    _nb_reported += 1

        if _nb_reported > 0:
            notify_wkp_changed()

        return _nb_reported

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __report_state(self, filenames: list, state: int) -> int:
        """Set a state on the workspace which is held, and tell it changed.

        Only a file that workspace knows already is set: a file it does not
        know is a file of a copy, and a state is no reason to add it there.

        :param filenames: (list of str) Names of the files, with their path
        :param state: (States) State to be set
        :return: (int) Number of files whose state was changed

        """
        _held = swapp_wkps.data
        if isinstance(_held, sppasWorkspace) is False:
            return 0
        if _held is self.__wkp:
            return 0

        _nb_changed = 0
        for _filename in filenames:
            _object = _held.get_object(_filename)
            if _object is not None:
                if len(_held.set_object_state(state, _object)) > 0:
                    _nb_changed += 1

        if _nb_changed > 0:
            notify_wkp_changed()

        return _nb_changed

    # -----------------------------------------------------------------------

    @staticmethod
    def __report(held: sppasWorkspace, one) -> bool:
        """Report one file of the copy on the given workspace.

        :param held: (sppasWorkspace) Workspace of the machine
        :param one: (FileName) File of the copy, checked or unchecked
        :raises: OSError: The file cannot be read
        :return: (bool) True when it was added or when its state was set

        """
        _reported = False
        _object = held.get_object(one.get_id())
        if _object is None:
            if held.add_file(one.get_id()) is not None:
                _object = held.get_object(one.get_id())
                _reported = True

        if _object is None:
            return _reported

        if _object.get_state() != one.get_state():
            if len(held.set_object_state(one.get_state(), _object)) > 0:
                _reported = True

        return _reported

    # -----------------------------------------------------------------------

    def __set_state(self, filenames: list, state: int) -> int:
        """Set a state to the given files of the workspace.

        A name which is not known to the workspace is ignored.

        :param filenames: (list of str) Names of the files, with their path
        :param state: (States) State to be set
        :raises: sppasTypeError: The given names are not a list
        :return: (int) Number of files whose state was changed

        """
        swappWorkspaceFiles.validate_filenames(filenames)

        _nb_changed = 0
        for _filename in filenames:
            _file_object = self.__wkp.get_object(_filename)
            if _file_object is not None:
                _modified = self.__wkp.set_object_state(state, _file_object)
                if len(_modified) > 0:
                    _nb_changed += 1

        return _nb_changed
