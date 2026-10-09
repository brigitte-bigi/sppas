"""
:filename: sppas.ui.swapp.services.files.files_provision.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The provision of files to an app, and their return.

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

from .files_acceptance import swappDepositAcceptance
from .files_chooser import swappFileChooser
from .files_delivery import swappResultDelivery
from .files_feeding import swappDataFiles
from .files_handing import swappAppExchange
from .files_place import swappFilePlace
from .files_workspace import swappWorkspaceFiles

# ---------------------------------------------------------------------------

MSG_NO_PLACE = "No place can be given now."
MSG_CONTENT = "This file is not one SPPAS reads."
MSG_SIZE = "This file is beyond the size which is accepted."
MSG_VOLUME = "This file is beyond the volume which is accepted."

# ---------------------------------------------------------------------------


class swappFileProvision:
    """Give an app the files it has to treat, and give back what it produced.

    It puts the tasks of a request in order and calls what does them: judging
    a name is the acceptance's, writing a copy is the place's, and what says
    which comes first is here. It is the only object of this service an app
    ever reaches, through the manager which holds it.

    """

    def __init__(self, workspace: swappWorkspaceFiles | None = None,
                 place: swappFilePlace | None = None,
                 chooser: swappFileChooser | None = None,
                 reachable: bool = True):
        """Create the provision of files.

        :param workspace: (swappWorkspaceFiles) The files of the workspace, None for a new one
        :param place: (swappFilePlace) The places of the deposit API, None for a new one where files are brought
        :param chooser: (swappFileChooser) What asks the person for files, None for a new one
        :param reachable: (bool) True when the person designates files which stand already
        :raises: sppasTypeError: One of the given objects is of a wrong type

        """
        if isinstance(reachable, bool) is False:
            raise sppasTypeError(reachable, "bool")
        if workspace is None:
            workspace = swappWorkspaceFiles()
        if isinstance(workspace, swappWorkspaceFiles) is False:
            raise sppasTypeError(workspace, "swappWorkspaceFiles")
        if chooser is None:
            chooser = swappFileChooser()
        if isinstance(chooser, swappFileChooser) is False:
            raise sppasTypeError(chooser, "swappFileChooser")

        self.__workspace = workspace
        self.__chooser = chooser
        self.__reachable = reachable
        self.__handing = swappAppExchange(workspace)

        # Nothing of the deposit API is built where the files stand already.
        self.__place = None
        self.__acceptance = None
        self.__delivery = None
        if reachable is False:
            if place is None:
                place = swappFilePlace()
            if isinstance(place, swappFilePlace) is False:
                raise sppasTypeError(place, "swappFilePlace")
            self.__place = place
            self.__acceptance = swappDepositAcceptance(place)
            self.__delivery = swappResultDelivery(place)

    # -----------------------------------------------------------------------

    def what_is_accepted(self) -> dict:
        """Return what may be sent, before anything is sent.

        :return: (dict) It depends on no file and on no deposit

        """
        return self.__acceptance.what_is_accepted()

    # -----------------------------------------------------------------------

    def feed(self, feeding: swappDataFiles, name: str, size: int) -> tuple:
        """Take a file into what is to be sent, and say why it is refused.

        The name, the size and the volume are judged on what is known of the
        file before anything travels.

        :param feeding: (swappDataFiles) The files fed so far
        :param name: (str) Name of the file, without any path
        :param size: (int) Size of the file, in bytes
        :raises: sppasTypeError: The given files are not a swappDataFiles
        :return: (tuple) Whether it is taken in, and why it is not

        """
        if isinstance(feeding, swappDataFiles) is False:
            raise sppasTypeError(feeding, "swappDataFiles")

        _accepted, _reason = self.__acceptance.accepts(name, feeding)
        if _accepted is False:
            return (False, _reason)
        if self.__acceptance.accepts_size(size) is False:
            return (False, MSG_SIZE)
        if self.__acceptance.accepts_volume(feeding.volume() + size) is False:
            return (False, MSG_VOLUME)

        feeding.feed(name, size)

        return (True, "")

    # -----------------------------------------------------------------------

    def take_back(self, feeding: swappDataFiles, name: str) -> int:
        """Take a file back out of what is to be sent.

        :param feeding: (swappDataFiles) The files fed so far
        :param name: (str) Name of the file to take back out
        :raises: sppasTypeError: The given files are not a swappDataFiles
        :return: (int) Volume of what is to be sent, in bytes

        """
        if isinstance(feeding, swappDataFiles) is False:
            raise sppasTypeError(feeding, "swappDataFiles")

        return feeding.take_back(name)

    # -----------------------------------------------------------------------

    def send(self, feeding: swappDataFiles, contents: dict) -> dict:
        """Write the files in a place, and make them known and checked.

        A place is asked for, the type of every file is read on its bytes,
        and what is refused is said with its reason. Nothing is written when
        no place is given.

        The contents travel in as many requests as there are files, so only
        the files whose bytes came with this one are written, and the place
        the deposit stands in is asked for once: the one the deposit already
        holds is kept, a second place being a second deposit.

        :param feeding: (swappDataFiles) The files fed so far
        :param contents: (dict) The bytes of the files which came, by name
        :raises: sppasTypeError: The given files are not a swappDataFiles
        :raises: OSError: The place cannot be written
        :return: (dict) The reason of every refused file, by name

        """
        if isinstance(feeding, swappDataFiles) is False:
            raise sppasTypeError(feeding, "swappDataFiles")

        _refused = dict()
        _place = feeding.place
        if len(_place) == 0:
            _place = self.__place.ask_for_a_place()
        if len(_place) == 0:
            _refused[""] = MSG_NO_PLACE
            return _refused

        feeding.place = _place
        _written = list()
        for _one in feeding.files:
            if _one.name not in contents:
                continue
            _content = contents[_one.name]
            if self.__acceptance.accepts_content(_content) is False:
                _refused[_one.name] = MSG_CONTENT
            elif self.__place.put(_place, _one.name, _content) is False:
                _refused[_one.name] = self.__place.why_not(_place, _one.name, _content)
            else:
                _written.append(self.__place.path_of(_place, _one.name))

        self.__workspace.make_known(_written)
        self.__workspace.check(_written)

        return _refused

    # -----------------------------------------------------------------------

    def ask_for_files(self) -> list:
        """Ask the person for files of the machine, and make them known.

        It is the way in of the files which stand already where SPPAS reads
        them: a path is asked for where they are, and the files join the
        workspace as they stand. A person who chooses nothing adds nothing.

        :raises: OSError: A chosen name cannot be read
        :return: (list of str) The files which were chosen, with their path

        """
        _chosen = self.__chooser.ask_for_files()
        if len(_chosen) > 0:
            self.make_known(_chosen)

        return _chosen

    # -----------------------------------------------------------------------

    def why_no_file(self) -> str:
        """Return why no file was obtained, when there is something to say.

        :return: (str) Empty when the person simply chose none

        """
        return self.__chooser.why_nothing()

    # -----------------------------------------------------------------------

    def make_known(self, filenames: list) -> int:
        """Make files of the machine known to the workspace, and check them.

        It is the way in of the files which stand already where SPPAS reads
        them: nothing is copied, and nothing is asked of the deposit API.

        :param filenames: (list of str) Names of the files, with their path
        :raises: sppasTypeError: The given names are not a list
        :raises: OSError: A given name cannot be read
        :return: (int) Number of added files, roots and paths

        """
        _nb_added = self.__workspace.make_known(filenames)
        self.__workspace.check(filenames)

        return _nb_added

    # -----------------------------------------------------------------------

    def take_out(self, filenames: list) -> int:
        """Take files out of the workspace.

        :param filenames: (list of str) Names of the files, with their path
        :return: (int) Number of removed files, roots and paths

        """
        return self.__workspace.remove(filenames)

    # -----------------------------------------------------------------------

    def works_on(self, workspace) -> None:
        """Set the workspace the files are known to.

        :param workspace: (sppasWorkspace) Workspace a request carried

        """
        self.__workspace.set_workspace(workspace)

    # -----------------------------------------------------------------------

    def workspace_name(self) -> str:
        """Return the name of the workspace the files are known to.

        :return: (str)

        """
        return self.__workspace.name()

    # -----------------------------------------------------------------------

    def has_workspace(self) -> bool:
        """Return whether a workspace holds the files to be treated.

        Nothing of this service reads it to tell the three cases apart: a
        workspace exists in all of them, one being composed when none is
        given, and the case is said by the app when it is entered.

        :return: (bool) False when it holds no file

        """
        return self.__workspace.exists()

    # -----------------------------------------------------------------------

    def workspace(self):
        """Return the workspace the files are known to.

        It is what a request carries back, so that the next one finds what
        the person designated. It is the workspace itself and not a copy of
        it: what an app receives is another thing, and handing is what makes
        it.

        :return: (sppasWorkspace)

        """
        return self.__workspace.workspace()

    # -----------------------------------------------------------------------

    def files_for_app(self):
        """Return a workspace with the files to be treated in it.

        A file which is still locked is held by nobody: the app which took it
        never said it had finished, and it is released before anything is
        handed. It is what makes an app stopping halfway harmless, and a
        release is why the state does not have to be watched.

        :return: (sppasWorkspace) Can hold no file at all

        """
        _still_locked = list()
        for _one in self.__workspace.locked_files():
            _still_locked.append(_one.get_id())
        if len(_still_locked) > 0:
            self.__workspace.release(_still_locked)

        return self.__handing.for_app()

    # -----------------------------------------------------------------------

    def lock(self, filenames: list) -> int:
        """Set as being treated the files an app takes.

        :param filenames: (list of str) Names of the files, with their path
        :raises: sppasTypeError: The given names are not a list
        :return: (int) Number of locked files

        """
        return self.__workspace.lock(filenames)

    # -----------------------------------------------------------------------

    def release(self, filenames: list) -> int:
        """Set to be treated again the files an app gives back.

        :param filenames: (list of str) Names of the files, with their path
        :raises: sppasTypeError: The given names are not a list
        :return: (int) Number of released files

        """
        return self.__workspace.release(filenames)

    # -----------------------------------------------------------------------

    def produced(self, workspace) -> dict:
        """Write what an app produced into the workspace, and check it.

        What is given back is grouped by the root the files stand under, which
        is what lets a person see which files were grouped together and what
        they produced. The grouping is the workspace's own work.

        What an app made nothing of, and the cause it states for it, is not
        read here: a deposit brings it with it, and it waits with the rest of
        the deposit.

        :param workspace: (sppasWorkspace) Workspace an app gives back
        :raises: sppasTypeError: The given workspace is not a sppasWorkspace
        :raises: OSError: A produced file cannot be read
        :return: (dict) Names of the produced files, with their path, by root

        """
        _produced = self.__handing.back_from_app(workspace)
        self.__workspace.write_produced(_produced)

        return self.__workspace.roots_of(_produced)

    # -----------------------------------------------------------------------

    def finished(self, filenames: list | None = None) -> int:
        """Release the files an app still holds, and give the copy back.

        The app has finished, so it holds nothing any more and what it
        produced is in the copy: it is the moment the copy is reported on the
        workspace of the machine, and the only one. Where the files had to be
        brought there is no such workspace and nothing is reported: what the
        request carries is the whole of it. PF13

        :param filenames: (list of str) Names the app still holds, None for every locked file
        :raises: OSError: A file of the copy cannot be read
        :return: (int) Number of released files

        """
        if filenames is None:
            filenames = list()
            for _one in self.__workspace.locked_files():
                filenames.append(_one.get_id())

        _nb_released = self.__workspace.release(filenames)
        if self.__reachable is True:
            self.__workspace.give_back()

        return _nb_released

    # -----------------------------------------------------------------------

    def address_of(self, place: str, name: str) -> str:
        """Return the address a produced file is reached at.

        :param place: (str) Place the file stands in
        :param name: (str) Name of the file
        :return: (str) Empty when the file is reached at no address

        """
        return self.__delivery.address_of(place, name)

    # -----------------------------------------------------------------------

    def serve(self, address: str) -> bytes:
        """Return the bytes an address names.

        :param address: (str) Address to be served
        :return: (bytes) Empty when there is nothing to give

        """
        return self.__delivery.serve(address)
