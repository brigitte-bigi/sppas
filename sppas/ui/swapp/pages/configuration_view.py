"""
:filename: sppas.ui.swapp.pages.configuration_view.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: View of the web page "Configuration" of SPPAS.

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
from whakerpy.htmlmaker import TagNode

from sppas.core.config import sg
from sppas.core.config import cfg
from sppas.ui import _
from sppas.ui.swapp.swapp_base.swapp_view import swappBaseView
from sppas.ui.swapp.swapp_core.swappsg import swapp_settings

# ---------------------------------------------------------------------------


# Ce que SPPAS retient d'un lancement à l'autre.
MSG_PURPOSE = _("The choices SPPAS is remembering from one launch to the next one.")

# Ce que SPPAS écrit dans les fichiers
MSG_FILES = _("What SPPAS writes into the files")
# Conserver ce que le format de destination ne sait pas contenir
MSG_INTEROPERABILITY = _("Preserve what the destination format can't hold")
# Les métadonnées, les vocabulaires contrôlés et les médias sont alors écrits
# dans un tier nommé DoNotEdit, que SPPAS relit. Sans cela, ils sont perdus.
MSG_INTEROPERABILITY_SAYS = _("The metadata, the controlled vocabularies and the media are then written into a tier named DoNotEdit, which SPPAS reads back. Without it, they are lost.")
# Enregistrer
MSG_SAVE = _("Save")
# Certains changements ne seront effectifs qu'au prochain démarrage de SPPAS.
MSG_RESTART = _("Some of the changes only take effect the next time SPPAS starts.")

# Ce que SPPAS écrit dans le Journal
MSG_JOURNAL = _("What SPPAS writes in the Journal")
# Debug
MSG_LOG_DEBUG = _("Debug")
# Information
MSG_LOG_INFO = _("Info")
# Avertissement
MSG_LOG_WARNING = _("Warning")
# De tout dire à ne signaler que ce qui cloche. Le debug ajoute les messages
# destinés au développement : utiles dans un message de feedback, encombrants
# le reste du temps.
MSG_LOG_SAYS = _("From saying everything to reporting only what goes wrong. Debug adds the messages meant for the development: useful in a feedback message, cluttering the rest of the time.")

# Ce qui se règle ailleurs
MSG_ELSEWHERE = _("What is set elsewhere")
# L'affichage - couleurs, contraste, taille du texte - se règle dans la barre de chaque page.
MSG_ACCESSIBILITY = _("The display -- colors, contrast, text size -- is set in the bar of every page.")
# Les composantes installées se règlent dans l'application Setup.
MSG_FEATURES = _("The installed features are set in the Setup application.")

# ---------------------------------------------------------------------------

MSG_HEADER = f"SPPAS {sg.__release__} » " + _("Configuration")

# ---------------------------------------------------------------------------


class swappConfigurationView(swappBaseView):
    """View class responsible for populating the *configuration.html* page.

    This class represents the **View** component of the "Configuration"
    page. It states each choice as a sentence saying what it changes, with
    its current value, and sends them back with a native form: the page
    holds no business logic and needs no script of its own.

    """

    # The levels of the logging system the user chooses between: the
    # standard ones. A level is a threshold, the messages of a level
    # greater or equal are passing, so a value is read as the highest
    # threshold of its ten.
    LOG_LEVELS = (10, 20, 30)

    def __init__(self, tree: HTMLTree):
        """Initialize and populate the "Configuration" view structure.

        :param tree: (HTMLTree) An existing HTML tree to populate with
                     the page-specific content.
        :raises: TypeError: tree is not an instance of HTMLTree

        """
        if isinstance(tree, HTMLTree) is False:
            raise TypeError("swappConfigurationView: tree must be an instance of HTMLTree. Got {}".format(type(tree)))
        super().__init__(tree, MSG_HEADER)

    # -----------------------------------------------------------------------

    @staticmethod
    def level_of(log_level: int) -> int:
        """Return the level of the group the given threshold belongs to.

        :param log_level: (int) A level of the logging system
        :returns: (int) One of LOG_LEVELS

        """
        for level in swappConfigurationView.LOG_LEVELS:
            if int(log_level) <= level:
                return level
        return swappConfigurationView.LOG_LEVELS[-1]

    # -----------------------------------------------------------------------
    # Populate the tree
    # -----------------------------------------------------------------------

    def _populate_head_css(self):
        """Override. Populate the `<head>` section of the HTML tree for CSS links.

        The toggle group of Whakerexa is the only component this page adds
        to the shared stylesheets.

        """
        self._htree.head.link("stylesheet",
                              swapp_settings.wexa_statics + "css/togglegroup.css",
                              link_type="text/css")

    # -----------------------------------------------------------------------

    def _populate_body_header(self):
        """Override. Populate the header area of the page.

        """
        self.append_responsive_menu_button(self._htree.body_header)

    # -----------------------------------------------------------------------

    def _populate_body_nav(self):
        """Override. Populate the nav area of the page.

        """
        _s = TagNode(self._htree.body_nav.identifier, None, "section")
        self.append_pin_button(_s)
        self.append_accessibility_buttons(_s)
        self._htree.body_nav.append_child(_s)

        self.append_home_link_button(self._htree.body_nav, self._home_target())
        self.append_trace_link_button(self._htree.body_nav)

    # -----------------------------------------------------------------------
    # Update the tree -- for baking the page
    # -----------------------------------------------------------------------

    def populate_tree_content(self, status_message: str = ""):
        """Populate the tree content with the choices of the user.

        :param status_message: (str) What the last post did, if anything.

        """
        _purpose = HTMLNode(self._htree.body_main.identifier, None, "p", value=MSG_PURPOSE)
        self._htree.body_main.append_child(_purpose)

        # The form posts to the page itself, query string included, so the
        # accessibility parameters of Whakerexa are preserved.
        _form = TagNode(self._htree.body_main.identifier, None, "form")
        _form.set_attribute("id", "configuration_choices")
        _form.set_attribute("method", "post")
        self._htree.body_main.append_child(_form)

        self._append_files_section(_form)
        self._append_journal_section(_form)

        # The confirmation of the last post: an inline message, announced
        # to screen readers when its content changes.
        _status = HTMLNode(_form.identifier, None, "p", value=status_message)
        _status.set_attribute("id", "configuration_status")
        _status.set_attribute("class", "status-message")
        _status.set_attribute("aria-live", "polite")
        _form.append_child(_status)

        _save = HTMLNode(_form.identifier, None, "button", value=MSG_SAVE)
        _save.set_attribute("type", "submit")
        _save.set_attribute("class", "action-button")
        _save.set_attribute("name", "event_bake")
        _save.set_attribute("value", "handle_configuration_save")
        _form.append_child(_save)

        _restart = HTMLNode(_form.identifier, None, "p", value=MSG_RESTART)
        _restart.set_attribute("class", "details")
        _form.append_child(_restart)

        self._append_elsewhere_section(self._htree.body_main)

    # -----------------------------------------------------------------------

    @staticmethod
    def _append_files_section(parent: TagNode):
        """Append the choices weighing on what SPPAS writes.

        :param parent: (TagNode) The form of the page

        """
        _fieldset = TagNode(parent.identifier, None, "fieldset")
        _fieldset.set_attribute("id", "configuration_files")
        parent.append_child(_fieldset)

        _legend = HTMLNode(_fieldset.identifier, None, "legend", value=MSG_FILES)
        _fieldset.append_child(_legend)

        # A control is written beside its label, not inside it: wexa.css
        # hides a control put inside a label, which is how it dresses one
        # as a button.
        ident = "configuration_interoperability"
        _check = HTMLNode(_fieldset.identifier, ident, "input")
        _check.set_attribute("id", ident)
        _check.set_attribute("type", "checkbox")
        _check.set_attribute("name", ident)
        if cfg.interoperability is True:
            _check.set_attribute("checked", None)
        _fieldset.append_child(_check)

        _label = HTMLNode(_fieldset.identifier, None, "label", value=MSG_INTEROPERABILITY)
        _label.set_attribute("for", ident)
        _fieldset.append_child(_label)

        _says = HTMLNode(_fieldset.identifier, None, "p", value=MSG_INTEROPERABILITY_SAYS)
        _says.set_attribute("class", "details")
        _fieldset.append_child(_says)

    # -----------------------------------------------------------------------

    @staticmethod
    def _append_journal_section(parent: TagNode):
        """Append the choice weighing on what SPPAS is saying.

        The levels are the ones of the logging system: the normal one is
        the default of the configuration, the other is the lowest, which
        lets every message through.

        :param parent: (TagNode) The form of the page

        """
        _fieldset = TagNode(parent.identifier, None, "fieldset")
        _fieldset.set_attribute("id", "configuration_journal")
        parent.append_child(_fieldset)

        _legend = HTMLNode(_fieldset.identifier, None, "legend", value=MSG_JOURNAL)
        _fieldset.append_child(_legend)

        # The toggle group of Whakerexa: mutually-exclusive choices reading
        # as one connected control. Its markup contract is a section of
        # labels, each one holding its radio button.
        _group = TagNode(_fieldset.identifier, None, "section")
        _group.set_attribute("class", "toggle-group")
        _group.set_attribute("role", "radiogroup")
        _group.set_attribute("aria-label", MSG_JOURNAL)
        _fieldset.append_child(_group)

        current = swappConfigurationView.level_of(cfg.log_level)
        for level, message in zip(swappConfigurationView.LOG_LEVELS,
                                  (MSG_LOG_DEBUG, MSG_LOG_INFO, MSG_LOG_WARNING)):
            ident = "configuration_log_" + str(level)
            _label = TagNode(_group.identifier, None, "label")
            _label.set_attribute("class", "menuitem")
            _label.set_attribute("for", ident)
            _group.append_child(_label)

            _radio = HTMLNode(_label.identifier, ident, "input")
            _radio.set_attribute("id", ident)
            _radio.set_attribute("type", "radio")
            _radio.set_attribute("name", "configuration_log_level")
            _radio.set_attribute("value", str(level))
            if level == current:
                _radio.set_attribute("checked", None)
            _label.append_child(_radio)

            _text = HTMLNode(_label.identifier, None, "span", value=message)
            _label.append_child(_text)

        _says = HTMLNode(_fieldset.identifier, None, "p", value=MSG_LOG_SAYS)
        _says.set_attribute("class", "details")
        _fieldset.append_child(_says)

    # -----------------------------------------------------------------------

    @staticmethod
    def _append_elsewhere_section(parent: TagNode):
        """Append what this page does not hold, and where it is held.

        :param parent: (TagNode) The main of the page

        """
        _section = TagNode(parent.identifier, None, "section")
        _section.set_attribute("id", "configuration_elsewhere")
        parent.append_child(_section)

        _title = HTMLNode(_section.identifier, None, "h2", value=MSG_ELSEWHERE)
        _section.append_child(_title)

        for message in (MSG_ACCESSIBILITY, MSG_FEATURES):
            _p = HTMLNode(_section.identifier, None, "p", value=message)
            _section.append_child(_p)
