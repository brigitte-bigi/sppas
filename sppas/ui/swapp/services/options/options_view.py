"""
:filename: sppas.ui.swapp.services.options.options_view.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The container an app places in its page: one line per option.

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

from __future__ import annotations
import html

from whakerpy.htmlmaker import EmptyNode
from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import TagNode

from sppas.core.coreutils import sppasTypeError
from sppas.ui import _

from .options_record import swappOptionsRecord
from .options_record import FIELD_PREFIX
from .options_record import TASK_FILE
from .options_record import TASK_VALIDATE

# ---------------------------------------------------------------------------

ID_CONTAINER = "options_container"

MSG_OPTIONS = _("Options")
MSG_APPLY = _("Apply")
MSG_BROWSE = _("Browse")

# What a field of a number accepts: the bounds and the increment of the
# desktop interface.
NUMBER_MIN = "0"
NUMBER_MAX = "2000"
FLOAT_STEP = "0.01"

# ---------------------------------------------------------------------------


class swappOptionsView:
    """Build the container of the options: one line per option.

    A line holds the label of its option and what suits its kind, filled in
    with the value the option holds. Nothing is decided here, and the texts
    of a line are the ones its option carries.

    """

    def __init__(self, parent: str | None = None):
        """Create the container, with nothing in it.

        :param parent: (str) Identifier of the node an app appends it to

        """
        self.__node = TagNode(parent, ID_CONTAINER, "section",
                              attributes={"id": ID_CONTAINER, "aria-label": MSG_OPTIONS})

    # -----------------------------------------------------------------------

    def get_node(self) -> TagNode:
        """Return the container, to be appended by an app.

        :return: (TagNode)

        """
        return self.__node

    # -----------------------------------------------------------------------

    def serialize(self) -> str:
        """Return the container and its content, in HTML.

        :return: (str)

        """
        return self.__node.serialize()

    # -----------------------------------------------------------------------

    def populate_tree_content(self, record: swappOptionsRecord) -> None:
        """Build the content of the container: one line per option of the set.

        :param record: (swappOptionsRecord) What is to be shown
        :raises: sppasTypeError: The given record is not a swappOptionsRecord

        """
        if isinstance(record, swappOptionsRecord) is False:
            raise sppasTypeError(record, "swappOptionsRecord")
        if len(record.to_be_shown) > 0:
            raise NotImplementedError

        self.__node.clear_children()
        _form = TagNode(self.__node.identifier, None, "form", attributes={"method": "post"})
        self.__node.append_child(_form)

        _carried = record.serialize()
        for _name in _carried:
            _form.append_child(EmptyNode(_form.identifier, None, "input",
                                         attributes={"type": "hidden", "name": _name,
                                                     "value": html.escape(str(_carried[_name]), quote=True)}))

        for _option in record.set.for_app():
            self.__append_line(_form, _option)

        if len(record.said) > 0:
            _form.append_child(HTMLNode(_form.identifier, None, "p", value=html.escape(record.said, quote=False),
                                        attributes={"role": "status"}))

        _form.append_child(HTMLNode(_form.identifier, None, "button", value=MSG_APPLY,
                                    attributes={"type": "submit", "name": TASK_VALIDATE, "value": "",
                                                "class": "action-button"}))

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __append_line(self, form: TagNode, option) -> None:
        """Append the line of one option: its label, and what suits its kind.

        :param form: (TagNode) The form the line is appended to
        :param option: (sppasOption) The option of the line

        """
        _line = TagNode(form.identifier, None, "p")
        form.append_child(_line)

        _kind = option.get_type()
        _field = FIELD_PREFIX + str(option.get_key())
        _text = html.escape(str(option.get_text()), quote=False)
        _value = html.escape(str(option.get_untypedvalue()), quote=True)
        _named = _field + "_label"
        _label = HTMLNode(_line.identifier, None, "label", value=_text, attributes={"for": _field, "id": _named})

        if _kind == "bool":
            _attributes = {"type": "checkbox", "id": _field, "name": _field, "value": "True"}
            if option.get_value() is True:
                _attributes["checked"] = None
            _line.append_child(EmptyNode(_line.identifier, None, "input", attributes=_attributes))
            _line.append_child(_label)
            return

        _line.append_child(_label)
        _attributes = {"type": "text", "id": _field, "name": _field, "value": _value}
        if _kind == "int":
            _attributes["type"] = "number"
            _attributes["min"] = NUMBER_MIN
            _attributes["max"] = NUMBER_MAX
            _attributes["step"] = "1"
        elif _kind == "float":
            _attributes["type"] = "number"
            _attributes["min"] = NUMBER_MIN
            _attributes["max"] = NUMBER_MAX
            _attributes["step"] = FLOAT_STEP

        # The field of a file and what asks for one stand side by side. They
        # are one group, named by the label of the option, and the button is
        # named by its own text followed by that label: several options which
        # take a file do not give several buttons of the same name.
        if _kind.startswith("file") is True:
            _browse = _field + "_browse"
            _holder = TagNode(_line.identifier, None, "span",
                              attributes={"class": "wrap-panel", "role": "group", "aria-labelledby": _named})
            _line.append_child(_holder)
            # A field takes the whole width of what holds it: the width is
            # given to what holds it, and not to the field.
            _sized = TagNode(_holder.identifier, None, "span", attributes={"class": "wrap-item width_70"})
            _holder.append_child(_sized)
            _sized.append_child(EmptyNode(_sized.identifier, None, "input", attributes=_attributes))
            _holder.append_child(HTMLNode(_holder.identifier, None, "button", value=MSG_BROWSE,
                                          attributes={"type": "submit", "name": TASK_FILE, "id": _browse,
                                                      "class": "wrap-item width_20",
                                                      "aria-labelledby": _browse + " " + _named,
                                                      "value": html.escape(str(option.get_key()), quote=True)}))
            return

        _line.append_child(EmptyNode(_line.identifier, None, "input", attributes=_attributes))
