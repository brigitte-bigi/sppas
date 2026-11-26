"""
:filename: sppas.ui.swapp.app_plugins.plugins_view.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The view of the Plugins application.

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
from whakerpy.htmlmaker import HTMLTree
from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import EmptyNode
from whakerpy.htmlmaker import TagNode

from sppas.core.config import sg
from sppas.ui import _

from ..swapp_base.swapp_view import swappBaseView
from ..swapp_core.swappsg import swapp_settings
from ..swapp_core.swappsg import swapp_serverstate

from .plugins_record import swappPluginsRecord
from .plugslist import swappPluginsList

# ---------------------------------------------------------------------------

MSG_HEADER = f"SPPAS {sg.__release__} » " + _("Plugins")
MSG_INSTALL = _("Install")
MSG_DELETE = _("Delete")
MSG_FILES = _("Add files")
MSG_PLUGINS = _("Plugins")
MSG_RESULTS = _("Results")
MSG_RUN = _("Let's go!")
MSG_RUN_MISSING = _("No plugin is selected.")
MSG_RESET = _("Reset")
MSG_INTRO = _("Plugins runs on your files programs added to SPPAS. Add the files, select the plugins, "
              "set their options, then click Let's go!. What each plugin did with each file is given in "
              "the results.")

# The script of the page, filled in with the folder of the scripts.
BODY_SCRIPT = """
        import {{ PluginsManager, SwappOptions }} from '/{js}sppas.js';
        import SwappFiles from '/{js}swapp_files.js';

        // The managers drive the sections of the page: they are started when
        // the page shows them, and not while it shows the help.
        if (document.getElementById('plugins_files_section') !== null) {{
            const swappFiles = new SwappFiles();
            swappFiles.handleSwappFilesOnLoad();
            // The windows of the options, which the service of the options
            // offers: their listeners are attached before the ones of the page.
            const swappOptions = new SwappOptions('plugins_form', 'plugins_options_');
            swappOptions.handleSwappOptionsOnLoad();
            const pluginsManager = new PluginsManager();
            pluginsManager.handlePluginsManagerOnLoad();
        }}
"""

# ---------------------------------------------------------------------------


class swappPluginsView(swappBaseView):
    """View class responsible for populating the page of Plugins.

    It builds the header and the nav of the page, and the main content from
    a record: it decides nothing, and shows what it is given.

    """

    def __init__(self, tree: HTMLTree, form_id: str):
        """Initialize and populate the Plugins view structure.

        :param tree: (HTMLTree) An existing HTML tree to populate
        :param form_id: (str) Identifier of the form which carries the record of the app
        :raises: TypeError: tree is not an instance of HTMLTree

        """
        if isinstance(tree, HTMLTree) is False:
            raise TypeError("swappPluginsView: tree must be an instance of HTMLTree. "
                            "Got {} instead.".format(type(tree)))
        # Set before the base view populates the nav with it.
        self.__form_id = form_id
        # The section the container of the provision of files is written in.
        self.__files = None
        # The container of the options of the plugin which is set, and what
        # the page writes of a plugin in its form.
        self.__options = None
        self.__values = dict()
        super(swappPluginsView, self).__init__(tree, MSG_HEADER)

    # -----------------------------------------------------------------------
    # Populate the tree
    # -----------------------------------------------------------------------

    def _populate_head_css(self, *args, **kwargs):
        """Override. Add the sheet of Plugins."""
        super()._populate_head_css(*args, **kwargs)
        self._htree.head.link("stylesheet", swapp_settings.css + "app_plugins.css", link_type="text/css")

    # -----------------------------------------------------------------------

    def _populate_body_header(self):
        """Override. Populate the header area of the page."""
        self.append_responsive_menu_button(self._htree.body_header)

    # -----------------------------------------------------------------------

    def _form_id(self) -> str:
        """Override. Return the identifier of the form which carries the record of the app."""
        return self.__form_id


    # -----------------------------------------------------------------------

    def populate_body_script(self):
        """Override. Populate the script body section."""
        self._htree.body_script.add_attribute("type", "module")
        self._htree.body_script.set_value(BODY_SCRIPT.format(js=swapp_settings.js))

    # -----------------------------------------------------------------------

    def populate_tree_content(self, record: swappPluginsRecord) -> None:
        """Populate the main content of the page from what the record says is to be shown.

        :param record: (swappPluginsRecord) What is to be shown

        """
        _shown = record.to_be_shown

        # The form of the page: every button and every switch of the page is
        # tied to it by its attribute "form". What was decided is carried in
        # it, hidden, but the selection of a plugin, which its switch carries:
        # the next request rebuilds the record from all of it.
        _form = TagNode(self._htree.body_main.identifier, None, "form",
                        attributes={"id": self.__form_id, "method": "post"})
        self._htree.body_main.append_child(_form)
        _data = record.serialize()
        for _name in _data:
            if _name.startswith("plugins_sel_") is False:
                _form.append_child(EmptyNode(_form.identifier, None, "input",
                                             attributes={"type": "hidden", "name": _name, "value": _data[_name]}))

        self._htree.body_main.append_child(HTMLNode(self._htree.body_main.identifier, None, "p",
                                                    value=MSG_INTRO))

        # The sections of the page, in their order: the files, the plugins,
        # and the results, when there are some.
        self.__files = self.__append_section("plugins_files_section", MSG_FILES)
        _plugins = self.__append_section("plugins_section", MSG_PLUGINS)
        # Installing and deleting a plugin happen where SPPAS runs on the
        # machine of the person, and nowhere else: above the cards, as above
        # the list in the desktop interface.
        if swapp_serverstate.local is True:
            _p = TagNode(_plugins.identifier, None, "p")
            _plugins.append_child(_p)
            for _identifier, _label in (("plugins_install", MSG_INSTALL), ("plugins_delete", MSG_DELETE)):
                _p.append_child(HTMLNode(_p.identifier, None, "button", value=_label,
                                         attributes={"type": "button", "id": _identifier}))
        # The container of the options of the plugin which is set stands in
        # the dialog of that plugin.
        self.__options = _shown.get("options", None)
        self.__values = _shown.get("values", dict())
        _plugins.append_child(swappPluginsList(_plugins.identifier,
                                               _shown.get("plugins", list()),
                                               _shown.get("readmes", dict()),
                                               record.selected,
                                               _shown.get("configured", ""),
                                               self.__options,
                                               self.__form_id))
        # What starts the runs is disabled while no plugin is selected.
        _attributes = {"type": "submit", "class": "action-button", "form": self.__form_id,
                       "name": "event_bake", "value": "plugins_run"}
        _class = "plugins-missing hidden"
        if len(record.selected) == 0:
            _attributes["disabled"] = None
            _attributes["aria-describedby"] = "plugins_run_state"
            _class = "plugins-missing"
        _plugins.append_child(HTMLNode(_plugins.identifier, None, "button", value=MSG_RUN,
                                       attributes=_attributes))
        # A reset is a reset: the decisions and the files go together, so it
        # is asked of the server.
        _plugins.append_child(HTMLNode(_plugins.identifier, None, "button", value=MSG_RESET,
                                       attributes={"type": "submit", "form": self.__form_id,
                                                   "name": "event_bake", "value": "plugins_reset"}))
        # What says no plugin is selected is always written, and hidden when
        # one is: selecting a plugin in the page makes no request.
        _plugins.append_child(HTMLNode(_plugins.identifier, None, "p", value=MSG_RUN_MISSING,
                                       attributes={"id": "plugins_run_state", "class": _class}))
        if "results" in _shown:
            self.__append_section("plugins_run_section", MSG_RESULTS)

    # -----------------------------------------------------------------------

    def get_files(self) -> TagNode | None:
        """Return the section the container of the provision of files is written in, None before the page is built."""
        return self.__files

    # -----------------------------------------------------------------------

    def get_options(self):
        """Return the container of the options of the plugin which is set, None when none is set."""
        return self.__options

    # -----------------------------------------------------------------------

    def get_values(self) -> dict:
        """Return what the page writes of a plugin in its form, empty if nothing (dict)."""
        return self.__values

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __append_section(self, identifier: str, title: str) -> TagNode:
        """Append a section of the page, under its title, and return it.

        :param identifier: (str) Identifier of the section
        :param title: (str) Its title
        :return: (TagNode) The section

        """
        _section = TagNode(self._htree.body_main.identifier, identifier, "section",
                           attributes={"id": identifier, "class": "panel"})
        self._htree.body_main.append_child(_section)
        _section.append_child(HTMLNode(_section.identifier, None, "h2", value=title))

        return _section

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    files = property(get_files, None)
    options = property(get_options, None)
    values = property(get_values, None)
