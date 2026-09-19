# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.nodes.feedback.progress.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Class to create a progress bar HTMLNode.

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
import logging
from whakerpy.htmlmaker import HTMLNode

from sppas.core.coreutils import sppasBaseProgress

# ---------------------------------------------------------------------------


class swappProgressBar(sppasBaseProgress):
    """Represent a dynamic progress bar section in the SPPAS web interface.

    This class implements a progress component fully compatible with
    :class:`sppasBaseProgress`. It produces an HTML section containing a
    standard ``<progress>`` element and optionally a header and a text line.

    The progress section structure is as follows::

        <section id="progress_section">
            <h3 id="progress_header">...</h3>     <!-- optional -->
            <p id="progress_text">...</p>         <!-- optional -->
            <progress id="percent_progress" max="100" value="0"></progress>
        </section>

    This swappProgressBar component defines only the static HTML structure of a progress bar.
    It does not instantiate or reference any JavaScript module. The visual behavior
    and updates are managed by the client-side code of the active web page, which
    is responsible for creating and starting a JS swappProgressBar instance.

    Server side: builds <section> and <progress> nodes only.
    Client side: controls animation and updates.

    """

    ID = "progress_section"
    REQUIRED = ["progressbar.js"]

    # ------------------------------------------------------------------

    def __init__(self, parent_identifier: str):
        """Create a new progress bar section under the given parent node.

        :param parent_identifier: (str) Identifier of the parent HTML node.

        """
        super(swappProgressBar, self).__init__()

        # The node contains an optional header, the progres and a text
        self.__node = HTMLNode(parent_identifier, swappProgressBar.ID, "section")
        self.__node.add_attribute("id", self.__node.identifier)

        # Create the <progress> element
        progress = HTMLNode(
            self.__node.identifier,
            "percent_progress",
            "progress",
            attributes={"id": "percent_progress", "max": "100", "value": "0"},
        )
        self.__node.append_child(progress)

    # ------------------------------------------------------------------
    # GETTERS
    # ------------------------------------------------------------------

    def get_percent(self) -> float:
        """Getter of the current progress bar percent.

        :return: (int) the percent

        """
        return self._percent

    # ------------------------------------------------------------------

    def get_text(self) -> str:
        """Getter of the text bar.

        :return: (str) the text

        """
        return self._text

    # ------------------------------------------------------------------

    def get_header(self) -> str:
        """

        :return: (str)

        """
        return self._header

    # ------------------------------------------------------------------

    def get_node(self) -> HTMLNode:
        """Return the HTMLNode of the progress.

        :return: (HTMLNode) the progress section.

        """
        return self.__node

    # ------------------------------------------------------------------
    # SETTERS
    # ------------------------------------------------------------------

    def set_header(self, header: str) -> None:
        """Set or update the header text.

        If a header node does not exist yet, it is created automatically.

        :param header: (str) New progress header text.

        """
        if len(header) > 0:
            self._header = str(header)
            self.__node_header()
        else:
            self._header = ""
        logging.info(self._header)

    # ------------------------------------------------------------------
    # PUBLIC METHODS
    # ------------------------------------------------------------------

    def update(self, percent: float | None = None, message: str | None = None) -> None:
        """Update the progress state.

        This method synchronizes the server-side state of the progress bar.
        If the corresponding nodes (header, text) are missing, they are
        created automatically.

        :param percent: (float) Value between 0 and 100 representing the current progress.
            If ``None``, the percentage remains unchanged.
        :param message: (str) Descriptive text to display under the header.
            If ``None``, the text remains unchanged.

        """
        if percent is not None:
            self._percent = percent
            self.__node_percent()

        if message is not None:
            logging.info("  => " + message)
            self._text = str(message)
            self.__node_text()

    # ------------------------------------------------------------------

    def close(self) -> None:
        """Remove optional header and text nodes.

        To be called when the progress bar is no longer needed.

        """
        c = self.__node.get_child("progress_header")
        if c is not None:
            self.__node.remove_child(c)

        c = self.__node.get_child("progress_text")
        if c is not None:
            self.__node.remove_child(c)

    # ------------------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------------------

    def __node_header(self) -> None:
        """Create or update the header node.

        """
        c = self.__node.get_child("progress_header")
        if c is not None:
            c.set_value(self._header)
        else:
            msg_node = HTMLNode(
                self.__node.identifier,
                "progress_header",
                "h3",
                attributes={"id": "progress_header"},
                value=self._header,
            )
            self.__node.insert_child(0, msg_node)

    # ------------------------------------------------------------------

    def __node_text(self) -> None:
        """Create or update the descriptive text node.

        """
        c = self.__node.get_child("progress_text")
        if c is not None:
            c.set_value(self._text)
        else:
            msg_node = HTMLNode(
                self.__node.identifier,
                "progress_text",
                "p",
                attributes={"id": "progress_text"},
                value=self._text,
            )
            self.__node.append_child(msg_node)

    # ------------------------------------------------------------------

    def __node_percent(self) -> None:
        """Update the value attribute of the <progress> node.

        """
        p = self.__node.get_child("percent_progress")
        if p is not None:
            p.set_attribute("value", str(self._percent))