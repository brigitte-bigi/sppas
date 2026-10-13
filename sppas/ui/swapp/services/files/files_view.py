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
import os

from whakerpy.htmlmaker import EmptyNode
from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import TagNode

from sppas.core.coreutils import sppasTypeError
from sppas.ui import _

from .files_record import swappFilesRecord
from .files_record import TASK_DESIGNATE
from .files_record import TASK_READY
from .files_record import TASK_SEND
from .files_record import TASK_TAKE_BACK

# ---------------------------------------------------------------------------

ID_DEPOSIT_CONTAINER = "files_deposit"

MSG_ADD_FILES = _("Add files")
MSG_IN_USE = _("The files to be treated")
MSG_WORKSPACE = _("Workspace:")
MSG_SELECT_FILES = _("Select files")
MSG_OR_DROP = _(", or drag and drop files here.")
MSG_TAKE_BACK = _("Take back")
MSG_SEND = _("Send")
MSG_DONE = _("Done")
MSG_REFUSED = _("Refused")
MSG_DEPOSITED = _("Deposited")
MSG_TREATED = _("Treated")


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

        self._node.append_child(HTMLNode(self._node.identifier, None, "h3", value=MSG_ADD_FILES))
        _form = self._append_form(self._node)
        self._append_record(_form, record)

        _zone = TagNode(_form.identifier, None, "div", attributes={"class": "dropzone"})
        _form.append_child(_zone)

        _label = HTMLNode(_zone.identifier, None, "label", value=MSG_SELECT_FILES,
                          attributes={"for": "files_input"})
        _zone.append_child(_label)
        _input = EmptyNode(_zone.identifier, "files_input", "input",
                           attributes={"id": "files_input", "type": "file",
                                       "multiple": "multiple"})
        _zone.append_child(_input)
        _zone.append_child(HTMLNode(_zone.identifier, None, "span", value=MSG_OR_DROP))

        _panel = TagNode(_zone.identifier, None, "section", attributes={"class": "cards-panel"})
        _zone.append_child(_panel)
        _refused = _shown.get("refused", dict())
        _listed = list()
        _treated = swappDepositView.__treated_names(record)
        for _name, _size in record.fed:
            self.__append_fed_file(_panel, _name, _size, _refused, _treated)
            _listed.append(_name)

        for _name in _refused:
            if len(_name) > 0 and _name not in _listed:
                self.__append_fed_file(_panel, _name, 0, _refused, _treated)

        if "accepted" in _shown:
            _zone.append_child(HTMLNode(_zone.identifier, None, "p",
                                            value=_shown["accepted"]))

        if "no_place" in _shown:
            return

        _button = HTMLNode(_form.identifier, None, "button", value=MSG_SEND,
                           attributes={"type": "submit", "name": TASK_SEND,
                                       "value": "", "class": "cta-button"})
        _form.append_child(_button)

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
        volume. Nothing is handed either: the files stand where SPPAS reads
        them, so there is nothing to send and nothing to declare finished.

        :param record: (swappFilesRecord) What is to be shown

        """
        self._node.append_child(HTMLNode(self._node.identifier, None, "h3", value=MSG_ADD_FILES))
        _form = self._append_form(self._node)
        self._append_record(_form, record)

        _zone = TagNode(_form.identifier, None, "div", attributes={"class": "dropzone"})
        _form.append_child(_zone)

        if "failed" in record.to_be_shown:
            _zone.append_child(HTMLNode(_zone.identifier, None, "p",
                                            value=record.to_be_shown["failed"]))

        _browse = HTMLNode(_zone.identifier, "files_browse", "button", value=MSG_SELECT_FILES,
                           attributes={"id": "files_browse", "type": "submit",
                                       "name": TASK_DESIGNATE, "value": ""})
        _zone.append_child(_browse)

        _panel = TagNode(_zone.identifier, None, "section", attributes={"class": "cards-panel"})
        _zone.append_child(_panel)
        for _filename in swappDepositView.__known_filenames(record):
            _treated = _filename in record.treated
            _card, _header, _body, _footer = swappDepositView.__append_card(_panel)
            swappDepositView.__append_state(_header, _treated)
            _body.append_child(HTMLNode(_body.identifier, None, "span", value=os.path.basename(_filename),
                                        attributes={"class": "dropzone-name", "title": _filename}))
            _button = {"type": "submit", "name": TASK_TAKE_BACK, "value": _filename}
            if _treated is True:
                _button["disabled"] = None
            _footer.append_child(HTMLNode(_footer.identifier, None, "button", value=MSG_TAKE_BACK,
                                          attributes=_button))

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

    def __append_fed_file(self, parent: TagNode, name: str, size: int, refused: dict, treated: list) -> None:
        """Append the card of one fed file: its size, its name, what became of it.

        :param parent: (TagNode) The panel of cards the card is appended to
        :param name: (str) Name of the file
        :param size: (int) Size of the file, in bytes
        :param refused: (dict) The reason of every refused file, by name
        :param treated: (list of str) Names of the files an app treated

        """
        _card, _header, _body, _footer = swappDepositView.__append_card(parent)
        _body.append_child(HTMLNode(_body.identifier, None, "span", value=str(size),
                                    attributes={"class": "dropzone-size"}))
        _body.append_child(HTMLNode(_body.identifier, None, "span", value=name,
                                    attributes={"class": "dropzone-name"}))

        # A refusal says its reason, under the name.
        if name in refused:
            _card.set_attribute("aria-invalid", "true")
            _header.append_child(HTMLNode(_header.identifier, None, "span", value="",
                                          attributes={"class": "file-status file-status-error", "data-icon": "no",
                                                      "role": "img", "aria-label": MSG_REFUSED}))
            _body.append_child(HTMLNode(_body.identifier, None, "p", value=refused[name],
                                        attributes={"class": "file-status file-status-error"}))
        else:
            _card.set_attribute("aria-invalid", "false")
            swappDepositView.__append_state(_header, name in treated)

        _button = {"type": "submit", "name": TASK_TAKE_BACK, "value": name}
        if name in treated:
            _button["disabled"] = None
        _footer.append_child(HTMLNode(_footer.identifier, None, "button", value=MSG_TAKE_BACK, attributes=_button))

    # -----------------------------------------------------------------------

    @staticmethod
    def __append_card(parent: TagNode) -> tuple:
        """Append the card of one file, with its header, its body and its footer.

        :param parent: (TagNode) The panel of cards the card is appended to
        :return: (tuple) The card, its header, its body and its footer

        """
        _card = TagNode(parent.identifier, None, "article", attributes={"class": "card"})
        parent.append_child(_card)
        _header = TagNode(_card.identifier, None, "div", attributes={"class": "card-header"})
        _card.append_child(_header)
        _body = TagNode(_card.identifier, None, "div", attributes={"class": "card-body"})
        _card.append_child(_body)
        _footer = TagNode(_card.identifier, None, "div", attributes={"class": "card-footer"})
        _card.append_child(_footer)
        return _card, _header, _body, _footer

    # -----------------------------------------------------------------------

    @staticmethod
    def __append_state(header: TagNode, treated: bool) -> None:
        """Append where a file stands: deposited, or treated by an app.

        The state is an icon whose shape says it, and whose text alternative
        says it to a screen reader.

        :param header: (TagNode) The header of the card of the file
        :param treated: (bool) An app treated the file

        """
        _class, _icon, _label = "file-status", "upload", MSG_DEPOSITED
        if treated is True:
            _class, _icon, _label = "file-status file-status-ok", "yes", MSG_TREATED
        header.append_child(HTMLNode(header.identifier, None, "span", value="",
                                     attributes={"class": _class, "data-icon": _icon,
                                                 "role": "img", "aria-label": _label}))

    # -----------------------------------------------------------------------

    @staticmethod
    def __treated_names(record: swappFilesRecord) -> list:
        """Return the names, without their path, of the files an app treated.

        :param record: (swappFilesRecord) What is to be shown
        :return: (list of str)

        """
        _names = list()
        for _filename in record.treated:
            _names.append(os.path.basename(_filename))
        return _names
