"""
:filename: sppas.ui.swapp.services.options.options_set.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The options an app hands over, and the value each one holds.

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
import json

from sppas.core.coreutils import sppasTypeError
from sppas.src.structs.baseoption import sppasOption

from .options_acceptance import swappValueAcceptance

# ---------------------------------------------------------------------------


class swappOptionSet:
    """The options an app hands over at one time, and what each one holds.

    It is the only class of this service which touches an sppasOption. It
    changes the value of an option and nothing else of it, and it keeps the
    value every option held when the set arrived.

    """

    def __init__(self, options: list | None = None):
        """Create a set with the options an app hands over.

        :param options: (list of sppasOption) None for an empty set
        :raises: sppasTypeError: One of the given options is not an sppasOption

        """
        self.__options = list()
        self.__arrived = dict()
        if options is None:
            return

        for _option in options:
            if isinstance(_option, sppasOption) is False:
                raise sppasTypeError(_option, "sppasOption")
            self.__options.append(_option)
            self.__arrived[_option.get_key()] = _option.get_untypedvalue()

    # -----------------------------------------------------------------------

    @staticmethod
    def rebuild(transported: str) -> swappOptionSet:
        """Return the set a page transmitted.

        What cannot be read gives an empty set, and nothing is raised: a page
        which transmits nothing is a first request.

        :param transported: (str) What serialize() gave, as it came back
        :return: (swappOptionSet)

        """
        _set = swappOptionSet()
        try:
            _entries = json.loads(transported)
        except (ValueError, TypeError):
            return _set
        if isinstance(_entries, list) is False:
            return _set

        for _entry in _entries:
            if isinstance(_entry, dict) is False or "key" not in _entry:
                continue
            _option = sppasOption(_entry["key"], _entry.get("type", "str"), _entry.get("value", ""))
            _option.set_text(_entry.get("text", ""))
            _option.set_name(_entry.get("name", ""))
            _set.__options.append(_option)
            _set.__arrived[_option.get_key()] = _entry.get("arrived", _option.get_untypedvalue())

        return _set

    # -----------------------------------------------------------------------

    def serialize(self) -> str:
        """Return everything a next request needs to rebuild this set.

        :return: (str) The options, with what each one carries

        """
        _entries = list()
        for _option in self.__options:
            _entry = dict()
            _entry["key"] = _option.get_key()
            _entry["type"] = _option.get_type()
            _entry["value"] = str(_option.get_untypedvalue())
            _entry["arrived"] = str(self.__arrived[_option.get_key()])
            _entry["text"] = _option.get_text()
            _entry["name"] = _option.get_name()
            _entries.append(_entry)

        return json.dumps(_entries)

    # -----------------------------------------------------------------------

    def for_app(self) -> list:
        """Return the options, every one holding the value it holds.

        :return: (list of sppasOption)

        """
        return list(self.__options)

    # -----------------------------------------------------------------------

    def value_of(self, key: str):
        """Return the value the option of the given key holds, as it was given.

        :param key: (str) Key of an option of the set
        :raises: KeyError: No option of the set has this key
        :return: The un-typed value

        """
        return self.__option_of(key).get_untypedvalue()

    # -----------------------------------------------------------------------

    def value_on_arrival_of(self, key: str):
        """Return the value the option of the given key held when the set arrived.

        :param key: (str) Key of an option of the set
        :raises: KeyError: No option of the set has this key
        :return: The un-typed value

        """
        if key not in self.__arrived:
            raise KeyError("No option of key {}".format(key))

        return self.__arrived[key]

    # -----------------------------------------------------------------------

    def set_value(self, key: str, value) -> None:
        """Set the value of the option of the given key.

        It sets and it does not judge: whether the value suits the option was
        answered before.

        :param key: (str) Key of an option of the set
        :param value: The un-typed value
        :raises: KeyError: No option of the set has this key

        """
        self.__option_of(key).set_value(value)

    # -----------------------------------------------------------------------

    def validate(self, given: dict) -> None:
        """Take in the values which suit their option, one by one.

        A value which does not suit its option is not taken in: that option
        keeps the value it held. A key which names no option is dropped.

        :param given: (dict) The values, by key of option

        """
        _acceptance = swappValueAcceptance()
        for _key in given:
            _concerned = None
            for _option in self.__options:
                if _option.get_key() == _key:
                    _concerned = _option
            if _concerned is None:
                continue
            if _acceptance.accepts(_concerned, given[_key]) is True:
                _concerned.set_value(given[_key])

    # -----------------------------------------------------------------------

    def put_back(self, key: str) -> None:
        """Put the option of the given key back to the value it arrived with.

        :param key: (str) Key of an option of the set

        """
        raise NotImplementedError

    # -----------------------------------------------------------------------

    def put_all_back(self) -> None:
        """Put every option back to the value it arrived with."""
        raise NotImplementedError

    # -----------------------------------------------------------------------

    def refusals(self) -> list:
        """Return what is said of the values which were not taken in.

        :return: (list) One refusal per option whose value was refused

        """
        raise NotImplementedError

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __option_of(self, key: str) -> sppasOption:
        """Return the option of the given key.

        :param key: (str) Key of an option of the set
        :raises: KeyError: No option of the set has this key
        :return: (sppasOption)

        """
        for _option in self.__options:
            if _option.get_key() == key:
                return _option

        raise KeyError("No option of key {}".format(key))
