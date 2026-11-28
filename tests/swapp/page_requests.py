# -*- coding: UTF-8 -*-
"""
:filename: tests.swapp.page_requests.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: What a page of swapp sends, rebuilt from its HTML as a browser and its scripts build it.

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

    A test sends what the page sends, and nothing written by hand: the fields
    are read in the HTML the server answered.

    - A button which submits a form sends the fields of that form, as a
      browser builds them: a field belongs to the form it stands in, or to
      the one its attribute "form" names; a checkbox or a radio is sent when
      it is checked; a select sends its selected option, or its first one;
      a disabled field and the other buttons are not sent. The button sends
      its name and its value.
    - swapp_files.js sends the hidden fields of the container of the
      provision of files, then the task and what it carries.

"""

from __future__ import annotations
from html.parser import HTMLParser

# ---------------------------------------------------------------------------

# The types of input a browser never sends as a field of a form.
NOT_SENT = ("submit", "button", "reset", "image", "file")

# ---------------------------------------------------------------------------


class swappPageFields(HTMLParser):
    """Read the fields of an HTML page, as a browser holds them."""

    def __init__(self, html: str):
        """Read the given HTML.

        :param html: (str) A page, or a part of a page

        """
        super(swappPageFields, self).__init__(convert_charrefs=True)
        self.__forms = list()
        self.__anonymous = 0
        self.__controls = list()
        self.__buttons = list()
        self.__select = None
        self.feed(html)
        self.close()

    # -----------------------------------------------------------------------

    def submitted(self, name: str, value: str, identifier: str = "") -> dict:
        """Return what the browser sends when the button of the given name and value is pressed.

        :param name: (str) Name of the button
        :param value: (str) Value of the button
        :param identifier: (str) Identifier of the button, empty for the first one in the page
        :raises: ValueError: No button has that name and that value
        :return: (dict) The fields of its form, and its name and value

        """
        _owner = None
        for _button in self.__buttons:
            if _owner is not None:
                break
            if _button["name"] != name or _button["value"] != value:
                continue
            if len(identifier) > 0 and _button["attributes"].get("id") != identifier:
                continue
            _owner = _button["owner"]
        if _owner is None:
            raise ValueError("No button {:s}={:s} in the page.".format(name, value))

        _fields = self.fields_of(_owner)
        _fields[name] = value

        return _fields

    # -----------------------------------------------------------------------

    def fields_of(self, owner: str) -> dict:
        """Return the fields the given form sends, its buttons left out.

        :param owner: (str) Identifier of the form
        :return: (dict) One value per name, the last one when a name is given twice

        """
        _fields = dict()
        for _control in self.__controls:
            if _control["owner"] != owner or _control["disabled"] is True or len(_control["name"]) == 0:
                continue
            if _control["type"] in ("checkbox", "radio") and _control["checked"] is False:
                continue
            _fields[_control["name"]] = _control["value"]

        return _fields

    # -----------------------------------------------------------------------

    def hidden(self) -> dict:
        """Return the hidden fields of what was read, whatever their form.

        :return: (dict) One value per name

        """
        _fields = dict()
        for _control in self.__controls:
            if _control["type"] == "hidden" and len(_control["name"]) > 0:
                _fields[_control["name"]] = _control["value"]

        return _fields

    # -----------------------------------------------------------------------

    def button(self, identifier: str) -> dict:
        """Return the attributes of the button of the given identifier.

        :param identifier: (str) Identifier of the button
        :return: (dict) Empty when no button has it

        """
        for _button in self.__buttons:
            if _button["attributes"].get("id") == identifier:
                return dict(_button["attributes"])
        return dict()

    # -----------------------------------------------------------------------
    # Override HTMLParser
    # -----------------------------------------------------------------------

    def handle_starttag(self, tag, attrs):
        _attributes = dict(attrs)
        if tag == "form":
            _identifier = _attributes.get("id")
            if _identifier is None:
                self.__anonymous += 1
                _identifier = "#form{:d}".format(self.__anonymous)
            self.__forms.append(_identifier)
            return

        _owner = ""
        if len(self.__forms) > 0:
            _owner = self.__forms[-1]
        if "form" in _attributes:
            _owner = _attributes["form"]

        if tag == "button":
            self.__buttons.append({"owner": _owner, "name": _attributes.get("name", ""),
                                   "value": _attributes.get("value", ""), "attributes": _attributes})

        elif tag == "input":
            _type = _attributes.get("type", "text")
            if _type in ("submit", "image"):
                self.__buttons.append({"owner": _owner, "name": _attributes.get("name", ""),
                                       "value": _attributes.get("value", ""), "attributes": _attributes})
            if _type in NOT_SENT:
                return
            _default = ""
            if _type in ("checkbox", "radio"):
                _default = "on"
            _value = _attributes.get("value")
            if _value is None:
                _value = _default
            self.__controls.append({"owner": _owner, "type": _type, "name": _attributes.get("name", ""),
                                    "value": _value, "checked": "checked" in _attributes,
                                    "disabled": "disabled" in _attributes})

        elif tag == "select":
            self.__select = {"owner": _owner, "type": "select", "name": _attributes.get("name", ""),
                             "value": None, "first": None, "checked": True,
                             "disabled": "disabled" in _attributes}

        elif tag == "option" and self.__select is not None:
            _value = _attributes.get("value", "")
            if self.__select["first"] is None:
                self.__select["first"] = _value
            if "selected" in _attributes:
                self.__select["value"] = _value

    # -----------------------------------------------------------------------

    def handle_endtag(self, tag):
        if tag == "form" and len(self.__forms) > 0:
            self.__forms.pop()

        elif tag == "select" and self.__select is not None:
            if self.__select["value"] is None:
                self.__select["value"] = self.__select["first"]
            if self.__select["value"] is not None:
                self.__controls.append(self.__select)
            self.__select = None

# ---------------------------------------------------------------------------


def main_of(page: str) -> str:
    """Return the main content of a page, without the main element itself.

    :param page: (str) The HTML of a page
    :return: (str) Empty when the page has no main content

    """
    _start = page.find("<main")
    if _start == -1:
        return ""
    _start = page.find(">", _start) + 1
    _end = page.rfind("</main>")

    return page[_start:_end]

# ---------------------------------------------------------------------------


def files_request(container: str, task: str, carried: dict) -> dict:
    """Return what swapp_files.js sends for a task of the provision of files.

    It is what #transmittedFields() reads -- the hidden fields of the
    container -- then the task, and what it carries.

    :param container: (str) The HTML of the container, as the server answered it
    :param task: (str) The task, under the field "task"
    :param carried: (dict) What the task carries: a name, a size, a content
    :return: (dict)

    """
    _posted = swappPageFields(container).hidden()
    _posted["task"] = task
    for _name in carried:
        _posted[_name] = carried[_name]

    return _posted

# ---------------------------------------------------------------------------


def with_container(events: dict, container: str) -> dict:
    """Return what a form sends once the container of the provision of files was replaced.

    swapp_files.js replaces the container by the one the server answered: the
    hidden fields of the record it holds are tied to the form of the app, so
    the next request of that form sends them, and not the ones the page held
    before.

    :param events: (dict) What the form sends, as the page held it
    :param container: (str) The HTML of the container, as the server answered it last
    :return: (dict)

    """
    _events = dict(events)
    _events.update(swappPageFields(container).hidden())

    return _events
