"""
:filename: sppas.ui.swapp.app_setup.fieldsets.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Create and manage the fieldset' nodes of the setup app.

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

    Copyright (C) 2011-2025  Brigitte Bigi, CNRS
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
from whakerpy.htmlmaker import HTMLNode

from .base_fieldset import swappSetupBaseFieldset
from .fieldset_welcome import swappSetupHomeFieldset
from .fieldset_license import swappSetupLicenseFieldset
from .fieldset_feature import swappSetupDepsFieldset
from .fieldset_feature import swappSetupLangFieldset
from .fieldset_feature import swappSetupAnnotFieldset
from .fieldset_feature import swappSetupSpinOffFieldset
from .fieldset_install import swappSetupInstallFieldset

# ---------------------------------------------------------------------------


class swappSetupFieldsets:
    """Create the fieldset nodes of the Setup, each one written from the model.

    A fieldset which holds choices is made anew each time it is asked for:
    what it shows is what the model holds at that moment, and no fieldset
    keeps a state of its own. The fieldset of the installation is made once:
    it shows an operation which is running, and its progress.

    """

    # The number of fieldsets, in the order a person goes through them.
    NUMBER = 7

    def __init__(self, model, uri: str = ""):
        """Create the maker of the fieldsets.

        :param model: (swappSetupModel) What the fieldsets are written from
        :param uri: (str) Name of the page

        """
        self.__model = model
        self.__uri = uri
        self.__install = swappSetupInstallFieldset(None)

        _keys = list()
        _messages = list()
        for i in range(swappSetupFieldsets.NUMBER):
            _field = self.create(i)
            _keys.append(_field.identifier)
            _messages.append(_field.get_msg())
        self.__keys = tuple(_keys)
        self.__messages = tuple(_messages)

    # -----------------------------------------------------------------------

    def create(self, idx: int) -> swappSetupBaseFieldset:
        """Return the fieldset of the given index, written from the model.

        :param idx: (int) Index of the fieldset
        :raises: IndexError: No fieldset has this index
        :return: (swappSetupBaseFieldset)

        """
        if idx == 0:
            return swappSetupHomeFieldset(None, self.__uri,
                                          self.__model.is_accepted("check_ref"),
                                          self.__model.is_accepted("check_prod"))
        if idx == 1:
            return swappSetupLicenseFieldset(None, self.__uri, self.__model.is_accepted("check_license"))
        if idx == 2:
            return swappSetupDepsFieldset(None, self.__model, self.__uri)
        if idx == 3:
            return swappSetupLangFieldset(None, self.__model, self.__uri)
        if idx == 4:
            return swappSetupAnnotFieldset(None, self.__model, self.__uri)
        if idx == 5:
            return swappSetupSpinOffFieldset(None, self.__model, self.__uri)
        if idx == 6:
            return self.__install

        raise IndexError("No fieldset of index {:d}".format(idx))

    # -----------------------------------------------------------------------

    def get_msg(self, idx: int) -> str:
        """Return the title message of the fieldset of the given index (str)."""
        return self.__messages[idx]

    # -----------------------------------------------------------------------

    def get_index(self, field: swappSetupBaseFieldset) -> int:
        """Return the index of the given field.

        :param field: (HTMLNode)
        :raises: ValueError: if field is unknown

        """
        return self.__keys.index(field.identifier)

    # -----------------------------------------------------------------------

    def get_index_from_name(self, field_name: str) -> int:
        """Return the index of the given field from its identifier.

        :param field_name: (str) Name of the field to get index
        :raises: ValueError: if field_name is unknown

        """
        return self.__keys.index(field_name)

    # -----------------------------------------------------------------------

    def get_identifier(self, idx) -> str:
        return self.__keys[idx]

    # -----------------------------------------------------------------------

    def next_field(self, current):
        """Return the next field.

        :return: (HTMLNode) a fieldset

        """
        if isinstance(current, HTMLNode) is False:
            raise TypeError
        if current.identifier not in self.__keys:
            raise KeyError
        # Get the index of the given field and offset it by +1
        next_index = min(self.__keys.index(current.identifier) + 1, len(self.__keys)-1)
        # Return the next field, or the current if no next
        return self.create(next_index)

    # -----------------------------------------------------------------------

    def prev_field(self, current):
        """Return the previous field.

        :return: (HTMLNode) a fieldset

        """
        if isinstance(current, HTMLNode) is False:
            raise TypeError
        if current.identifier not in self.__keys:
            raise KeyError
        # Get the index of the given field and offset it by -1
        prev_index = max(0, self.__keys.index(current.identifier) - 1)
        # Return the previous field, or the current if no previous
        return self.create(prev_index)

    # -----------------------------------------------------------------------

    def get_progress(self) -> object:
        """Return the progress of the installation or None."""
        return self.__install.get_progress()

    # -----------------------------------------------------------------------
    # Overloads
    # -----------------------------------------------------------------------

    def __contains__(self, field):
        return field.identifier in self.__keys

    def __iter__(self):
        for i in range(len(self.__keys)):
            yield self.create(i)

    def __getitem__(self, i):
        return self.create(i)

    def __len__(self):
        return len(self.__keys)

    def __index__(self, field):
        return self.__keys.index(field.identifier)
