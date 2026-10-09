"""
:filename: sppas.ui.swapp.services.files.files_view.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The two containers an app places in its page.

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

import html

from whakerpy.htmlmaker import EmptyNode
from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import TagNode

from sppas.core.coreutils import sppasTypeError

from .files_record import swappFilesRecord
from .files_record import TASK_DESIGNATE
from .files_record import TASK_READY
from .files_record import TASK_SEND
from .files_record import TASK_TAKE_BACK

# ---------------------------------------------------------------------------

ID_DEPOSIT_CONTAINER = "files_deposit"
ID_DELIVERY_CONTAINER = "files_delivery"

MSG_ADD_FILES = "Add files"
MSG_IN_USE = "The files to be treated"
MSG_WORKSPACE = "Workspace:"
MSG_NO_FILE = "No file was obtained."
MSG_SELECT_FILES = "Select files"
MSG_OR_DROP = ", or drag and drop files here."
MSG_TAKE_BACK = "Take back"
MSG_SEND = "Send"
MSG_DONE = "Done"
MSG_REFUSED = "Refused"
MSG_ACCEPTED = "Accepted"

MSG_PRODUCED = "What was produced"
MSG_NOTHING_YET = "Nothing has come back yet."
MSG_FINISHED = "The app has finished."
MSG_NOT_FINISHED = "The app has not finished."

# ---------------------------------------------------------------------------


class swappFilesBaseView:
    """Convenient class to build a container an app places in its page.

    The container is a node built under the identifier of the node an app
    chose: it is that app which appends it, and a node built under another
    parent is refused by the framework.

    """

    def __init__(self, parent: str):
        """Create the container, with nothing in it.

        :param parent: (str) Identifier of the node an app appends it to
        :raises: sppasTypeError: The given parent is not a string

        """
        if isinstance(parent, str) is False:
            raise sppasTypeError(parent, "str")

        self._node = TagNode(parent, self._identifier(), self._tag(),
                             attributes={"id": self._identifier()})

    # -----------------------------------------------------------------------

    @staticmethod
    def _tag() -> str:
        """Return the tag of the container (str)."""
        return "section"

    # -----------------------------------------------------------------------

    @staticmethod
    def _identifier() -> str:
        """Return the identifier of the container (str)."""
        return ID_DEPOSIT_CONTAINER

    # -----------------------------------------------------------------------

    def get_node(self) -> TagNode:
        """Return the container, to be appended by an app.

        :return: (TagNode)

        """
        return self._node

    # -----------------------------------------------------------------------

    def serialize(self) -> str:
        """Return the container and its content, in HTML.

        :return: (str)

        """
        return self._node.serialize()

    # -----------------------------------------------------------------------

    def populate_tree_content(self, record: swappFilesRecord) -> None:
        """Build the content of the container. To be overridden.

        :param record: (swappFilesRecord) What is to be shown
        :raises: sppasTypeError: The given record is not a swappFilesRecord

        """
        raise NotImplementedError

    # -----------------------------------------------------------------------
    # Protected
    # -----------------------------------------------------------------------

    def _append_form(self, parent: TagNode) -> TagNode:
        """Append the form which sends what the person did.

        :param parent: (TagNode) The node the form is appended to
        :return: (TagNode) The form

        """
        _form = TagNode(parent.identifier, None, "form",
                        attributes={"method": "post"})
        parent.append_child(_form)

        return _form

    # -----------------------------------------------------------------------

    def _append_record(self, form: TagNode, record: swappFilesRecord) -> None:
        """Append what the next request brings back, as hidden fields.

        A tree which omits it breaks the request which follows: the record
        would be rebuilt empty, and the person would see her list vanish
        without having touched it.

        :param form: (TagNode) The form the fields are appended to
        :param record: (swappFilesRecord) What is to be carried back

        """
        _carried = record.serialize()
        for _name in _carried:
            _value = html.escape(str(_carried[_name]), quote=True)
            _field = EmptyNode(form.identifier, None, "input",
                               attributes={"type": "hidden", "name": _name,
                                           "value": _value})
            form.append_child(_field)

    # -----------------------------------------------------------------------

    def _validate_record(self, record) -> None:
        """Empty the container, and raise if the given record is not one.

        The container is emptied because a view is populated once per
        request and its node lives longer than one: what was built for the
        request before is not what is shown now.

        :param record: (swappFilesRecord) Record to be validated
        :raises: sppasTypeError: The given record is not a swappFilesRecord

        """
        if isinstance(record, swappFilesRecord) is False:
            raise sppasTypeError(record, "swappFilesRecord")

        self._node.clear_children()

    # -----------------------------------------------------------------------

    node = property(get_node, None)

# ---------------------------------------------------------------------------


class swappDepositView(swappFilesBaseView):
    """Show what a person feeds, and what sends it.

    Nothing is counted, judged or refused here: a file is marked refused when
    the record says so, and the control which sends is left out when the
    record says there is no place.

    """

    def populate_tree_content(self, record: swappFilesRecord) -> None:
        """Build the container: the files designated, and what validates them.

        Where the files stand already, what the person designates is a path,
        nothing is deposited and no bound is shown. Where they have to be
        brought, what she designates is a name and a size, and what is
        accepted is said.

        :param record: (swappFilesRecord) What is to be shown
        :raises: sppasTypeError: The given record is not a swappFilesRecord

        """
        self._validate_record(record)
        if record.reachable is True:
            if record.has_workspace is True:
                self.__populate_in_use(record)
            else:
                self.__populate_in_place(record)
            return

        _shown = record.to_be_shown

        _form = self._append_form(self._node)
        self._append_record(_form, record)

        _fieldset = TagNode(_form.identifier, None, "fieldset",
                            attributes={"class": "dropzone"})
        _form.append_child(_fieldset)
        _legend = HTMLNode(_fieldset.identifier, None, "legend", value=MSG_ADD_FILES)
        _fieldset.append_child(_legend)

        _p = HTMLNode(_fieldset.identifier, None, "p")
        _fieldset.append_child(_p)
        _label = HTMLNode(_p.identifier, None, "label", value=MSG_SELECT_FILES,
                          attributes={"for": "files_input"})
        _p.append_child(_label)
        _input = EmptyNode(_p.identifier, "files_input", "input",
                           attributes={"id": "files_input", "type": "file",
                                       "multiple": "multiple"})
        _p.append_child(_input)
        _p.append_child(HTMLNode(_p.identifier, None, "span", value=MSG_OR_DROP))

        _ul = TagNode(_fieldset.identifier, None, "ul",
                      attributes={"class": "wrap-panel dropzone-list"})
        _fieldset.append_child(_ul)
        _refused = _shown.get("refused", dict())
        _listed = list()
        for _name, _size in record.fed:
            self.__append_fed_file(_ul, _name, _size, _refused)
            _listed.append(_name)

        for _name in _refused:
            if len(_name) > 0 and _name not in _listed:
                self.__append_fed_file(_ul, _name, 0, _refused)

        if "accepted" in _shown:
            _fieldset.append_child(HTMLNode(_fieldset.identifier, None, "p",
                                            value=_shown["accepted"]))

        if "no_place" in _shown:
            return

        _p = HTMLNode(_form.identifier, None, "p")
        _form.append_child(_p)
        _button = HTMLNode(_p.identifier, None, "button", value=MSG_SEND,
                           attributes={"type": "submit", "name": TASK_SEND,
                                       "value": "", "class": "cta-button"})
        _p.append_child(_button)

    # -----------------------------------------------------------------------

    def __populate_in_use(self, record: swappFilesRecord) -> None:
        """Build the container of a workspace which is there to be used.

        There is nothing to do but say its name: the workspace holds the
        files, and an app asking for files is given them.

        :param record: (swappFilesRecord) What is to be shown

        """
        _title = HTMLNode(self._node.identifier, None, "h3", value=MSG_IN_USE)
        self._node.append_child(_title)

        _said = MSG_WORKSPACE + " " + record.to_be_shown.get("workspace_name", "")
        self._node.append_child(HTMLNode(self._node.identifier, None, "p",
                                         value=_said))

    # -----------------------------------------------------------------------

    def __populate_in_place(self, record: swappFilesRecord) -> None:
        """Build the container of the files which stand already.

        No bound of any kind is shown and no file carries a mark of validity:
        nothing is deposited here, so nothing is refused for a size or for a
        volume.

        :param record: (swappFilesRecord) What is to be shown

        """
        _form = self._append_form(self._node)
        self._append_record(_form, record)

        _fieldset = TagNode(_form.identifier, None, "fieldset",
                            attributes={"class": "dropzone"})
        _form.append_child(_fieldset)
        _legend = HTMLNode(_fieldset.identifier, None, "legend", value=MSG_ADD_FILES)
        _fieldset.append_child(_legend)

        if "failed" in record.to_be_shown:
            _fieldset.append_child(HTMLNode(_fieldset.identifier, None, "p",
                                            value=record.to_be_shown["failed"]))

        _p = HTMLNode(_fieldset.identifier, None, "p")
        _fieldset.append_child(_p)
        _browse = HTMLNode(_p.identifier, "files_browse", "button", value=MSG_SELECT_FILES,
                           attributes={"id": "files_browse", "type": "submit",
                                       "name": TASK_DESIGNATE, "value": "",
                                       "class": "apply-button"})
        _p.append_child(_browse)

        _ul = TagNode(_fieldset.identifier, None, "ul",
                      attributes={"class": "wrap-panel dropzone-list"})
        _fieldset.append_child(_ul)
        for _filename in swappDepositView.__known_filenames(record):
            _li = TagNode(_ul.identifier, None, "li", attributes={"class": "wrap-item card"})
            _ul.append_child(_li)
            _li.append_child(HTMLNode(_li.identifier, None, "span", value=_filename,
                                      attributes={"class": "dropzone-name"}))
            _li.append_child(HTMLNode(_li.identifier, None, "button", value=MSG_TAKE_BACK,
                                      attributes={"type": "submit", "class": "apply-button",
                                                  "name": TASK_TAKE_BACK,
                                                  "value": _filename}))

        _p = HTMLNode(_form.identifier, None, "p")
        _form.append_child(_p)
        _p.append_child(HTMLNode(_p.identifier, None, "button", value=MSG_DONE,
                                 attributes={"type": "submit", "name": TASK_READY,
                                             "value": "", "class": "cta-button"}))

    # -----------------------------------------------------------------------

    @staticmethod
    def __known_filenames(record: swappFilesRecord) -> list:
        """Return the names of the files of the workspace, with their path.

        :param record: (swappFilesRecord) What is to be shown
        :return: (list of str) Can be empty

        """
        _filenames = list()
        if record.workspace is None:
            return _filenames

        for _path in record.workspace.get_paths():
            for _root in _path:
                for _one in _root:
                    _filenames.append(_one.get_id())

        return _filenames

    # -----------------------------------------------------------------------

    def __append_fed_file(self, parent: TagNode, name: str, size: int, refused: dict) -> None:
        """Append one fed file to the list.

        :param parent: (TagNode) The list the file is appended to
        :param name: (str) Name of the file
        :param size: (int) Size of the file, in bytes
        :param refused: (dict) The reason of every refused file, by name

        """
        _li = TagNode(parent.identifier, None, "li", attributes={"class": "wrap-item card"})
        parent.append_child(_li)

        if name in refused:
            _li.set_attribute("aria-invalid", "true")
            _mark = HTMLNode(_li.identifier, None, "span",
                             value=MSG_REFUSED + ": " + refused[name],
                             attributes={"class": "file-status file-status-error"})
            _li.append_child(_mark)
        else:
            _li.set_attribute("aria-invalid", "false")
            _mark = HTMLNode(_li.identifier, None, "span", value=MSG_ACCEPTED,
                             attributes={"class": "file-status file-status-ok"})
            _li.append_child(_mark)

        _li.append_child(HTMLNode(_li.identifier, None, "span", value=str(size),
                                  attributes={"class": "dropzone-size"}))
        _li.append_child(HTMLNode(_li.identifier, None, "span", value=name,
                                  attributes={"class": "dropzone-name"}))
        _li.append_child(HTMLNode(_li.identifier, None, "button", value=MSG_TAKE_BACK,
                                  attributes={"type": "submit", "class": "apply-button",
                                              "name": TASK_TAKE_BACK, "value": name}))

# ---------------------------------------------------------------------------


class swappDeliveryView(swappFilesBaseView):
    """Show what an app produced, and where it is reached.

    The files are grouped as the record groups them, and the sentence said of
    a file an app made nothing of is the one the record holds.

    """

    @staticmethod
    def _tag() -> str:
        """Override. Return the tag of the container (str)."""
        return "aside"

    # -----------------------------------------------------------------------

    @staticmethod
    def _identifier() -> str:
        """Override. Return the identifier of the container (str)."""
        return ID_DELIVERY_CONTAINER

    # -----------------------------------------------------------------------

    def populate_tree_content(self, record: swappFilesRecord) -> None:
        """Build the container: what was produced, and whether it is over.

        :param record: (swappFilesRecord) What is to be shown
        :raises: sppasTypeError: The given record is not a swappFilesRecord

        """
        self._validate_record(record)
        _shown = record.to_be_shown

        _title = HTMLNode(self._node.identifier, None, "h4", value=MSG_PRODUCED)
        self._node.append_child(_title)

        _produced = _shown.get("produced", dict())
        if len(_produced) == 0:
            self._node.append_child(HTMLNode(self._node.identifier, None, "p",
                                             value=MSG_NOTHING_YET))
        else:
            _ul = TagNode(self._node.identifier, None, "ul")
            self._node.append_child(_ul)
            for _root in _produced:
                self.__append_root(_ul, _root, _produced[_root], record.reachable)

        if "reachable_until" in _shown:
            self._node.append_child(HTMLNode(self._node.identifier, None, "p",
                                             value=_shown["reachable_until"]))

        _over = MSG_NOT_FINISHED
        if _shown.get("finished") is True:
            _over = MSG_FINISHED
        self._node.append_child(HTMLNode(self._node.identifier, None, "p", value=_over))

        self._append_record(self._append_form(self._node), record)

    # -----------------------------------------------------------------------

    def __append_root(self, parent: TagNode, root: str, produced: list,
                      reachable: bool) -> None:
        """Append one root and what it produced.

        A file the person reaches where it stands is shown by its name, and
        the path it stands under comes with it: the root above it says that
        path as well, so nothing is read on a hover alone. A file she reaches
        at an address is a link to it.

        :param parent: (TagNode) The list the root is appended to
        :param root: (str) Name of the root
        :param produced: (list of tuple) A name and a path or an address each, or a sentence
        :param reachable: (bool) True when the files stand where SPPAS reads them

        """
        _li = TagNode(parent.identifier, None, "li", value=root)
        parent.append_child(_li)
        _ul = TagNode(_li.identifier, None, "ul")
        _li.append_child(_ul)

        for _one in produced:
            _item = TagNode(_ul.identifier, None, "li")
            _ul.append_child(_item)
            if isinstance(_one, str) is True:
                _item.set_value(_one)
            elif reachable is True:
                _item.append_child(HTMLNode(_item.identifier, None, "span", value=_one[0],
                                            attributes={"class": "dropzone-name",
                                                        "title": _one[1]}))
            else:
                _a = HTMLNode(_item.identifier, None, "a", value=_one[0],
                              attributes={"href": _one[1]})
                _item.append_child(_a)
