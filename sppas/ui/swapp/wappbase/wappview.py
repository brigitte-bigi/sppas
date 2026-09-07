"""
:filename: sppas.ui.swapp.wappbase.wappview.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: SPPAS Web-Based application Base View of the MVC paradigm.

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

from sppas.core.config import cfg
from sppas.core.config import sg
from sppas.core.config import get_language

from sppas.ui import _

from ..wappcore.wapputils import sppasImagesAccess
from ..nodes.buttons.hbutton import sppasHTMLButton
from ..wappcore.wappsg import wapp_settings
from ..nodes.layout.hheader import SwappHeader
from ..nodes.layout.hfooter import SwappFooter

# ---------------------------------------------------------------------------


MSG_WEB = _("SPPAS website")
MSG_CONTRAST = _("Contrast")
MSG_COLOR = _("Color")
MSG_THEME = _("Theme")
MSG_PIN = _("Pin menu")
MSG_EXIT = _("Exit")
# The long version of the message is in the "po" files.
MSG_EXIT_TIP = _("Stops SPPAS and saves its settings.")
MSG_DASHBOARD = _("Dashboard")
MSG_HELP = _("Help")
MSG_JOURNAL = _("Journal")
MSG_FEEDBACK = _("Feedback")
MSG_ERROR = _("Error")
MSG_INFORMATION = _("Information")

# Must be appended to the HTMLTree before sppas.js
JS_INIT = (
    f"window.WEXA_JS_PATH = '/{wapp_settings.wexa_statics}js';"
    f"window.SPPAS_DEFAULT_PAGE = '{wapp_settings.default_page()}';"
    # The namespace is written before the framework is there: its logger
    # reads the level by itself when it starts, and no page asks for it.
    "window.Wexa = window.Wexa || {};"
    f"window.Wexa.logLevel = {cfg.log_level};"
)

# What the page starts once the loader has everything ready: the loader
# calls bootPage() after it has registered the themes and the icons, and
# hands over the namespace of the framework.
JS_BOOT_PAGE = (
    "window.bootPage = function (wexa) {"
    "    window.menu = new wexa.MenuManager();"
    "    window.menu.initSideMenu();"
    "    window.menu.initMobileToggle();"

    # The keys answer by clicking the button that already carries the action:
    # a page without its document has a button without href, and the key does
    # nothing there either.
    "    window.keyboard = new wexa.KeyboardController();"
    "    window.keyboard.register({keys: ['h', 'H', '?'], label: 'Help',"
    "        action: () => document.getElementById('link-help_button').click()});"
    "    window.keyboard.register({keys: ['j', 'J'], label: 'Journal',"
    "        action: () => document.getElementById('link-trace_button').click()});"
    # Not 'd': the slides of Whakerexa answer it, and a page of SPPAS may hold
    # slides one day. 'q' as in quitting the page -- leaving SPPAS itself never
    # has a key, the browser owning ctrl+q.
    "    window.keyboard.register({keys: ['q', 'Q'], label: 'Dashboard',"
    "        action: () => document.getElementById('link-home_button').click()});"
    # What changes the look of the page is written with punctuation.
    "    window.keyboard.register({keys: ['+'], label: 'Contrast',"
    "        action: () => document.getElementById('btn-contrast').click()});"
    "    window.keyboard.register({keys: ['*'], label: 'Color',"
    "        action: () => document.getElementById('btn-color').click()});"
    "    window.keyboard.register({keys: ['>'], label: 'Theme',"
    "        action: () => document.getElementById('btn-css-theme').click()});"
    # The Journal is the only page holding a button closing its own tab: the
    # key is declared for every page, and answers where the button stands.
    "    window.keyboard.register({keys: ['w', 'W'], label: 'Close',"
    "        action: () => {"
    "            const button = document.getElementById('close-tab_button');"
    "            if (button !== null) { button.click(); }"
    "        }});"
    "    window.keyboard.init();"
    "};"
)

# ---------------------------------------------------------------------------


class swappBaseView:
    """Base View class for populating any SPPAS web application page.

    This class implements the **View** component in the MVC architecture used
    across SPPAS web applications. It receives an existing :class:`HTMLTree`
    instance and fills it with all static and semi-static HTML elements.

    The :class:`swappBaseView` focuses exclusively on building the structure and
    presentation of the interface; it does not handle user interactions or
    business logic.

    It typically defines:
        - The `<head>` section with meta tags, CSS, and JS imports.
        - The `<header>` area for branding or navigation controls.
        - The `<footer>` section for informational elements.
        - The `<script>` section for inline initialization.
    """

    def __init__(self, tree: HTMLTree, title: str, *args, **kwargs):
        """Initialize and populate the main HTML sections.

        :param tree: (HTMLTree) An existing HTML tree to populate.
        :raises: TypeError: If *tree* is not an instance of :class:`HTMLTree`.

        The constructor immediately fills all default sections of the page by
        invoking the `populate_*()` methods. Child classes can override the
        protected `_populate_*()` methods to extend or modify their content.

        """
        # The tree to populate
        if isinstance(tree, HTMLTree) is False:
            raise TypeError("swappBaseView expected a HTML tree instance. "
                            "Got {}".format(type(tree)))
        self._htree = tree
        self._htree.add_html_attribute("lang", get_language().split('_')[0])

        # Accessibility default values
        self._accessibility = {
            "color": wapp_settings.accessibility_color_scheme,  # str: (light,dark)
            "contrast": wapp_settings.accessibility_contrast    # bool
        }

        # Populate, to fill the given tree with content
        self.populate_head()
        self.populate_body_header(title)
        self.populate_body_nav()
        self.populate_body_footer()
        self.populate_body_script()

    # -----------------------------------------------------------------------
    # Public
    # -----------------------------------------------------------------------

    def set_accessibility(self,
                          color: str | None = None,
                          contrast: str | None = None) -> None:
        """Update the current accessibility parameters.

        This method sets the active color and/or contrast schemes used by the
        web interface. When a value is given, it replaces the previously stored
        one in the internal accessibility dictionary.

        :param color: (str | None) Name of the color scheme to apply
                      (e.g. 'dark', 'light'). If None, no change is made.
        :param contrast: (str | None) Name or flag of the contrast mode to apply.
                         An empty value disables contrast mode.

        """
        if color is not None:
            self._accessibility['color'] = color
        if contrast is not None:
            self._accessibility['contrast'] = len(contrast.strip()) > 0

    # -----------------------------------------------------------------------

    def populate_head(self):
        """Populate the `<head>` section of the HTML document.

        Adds favicon, CSS stylesheets, and JavaScript imports required for
        rendering the base web interface, including both Whakerexa and
        application-specific resources.

        """
        # The favicon: the same for all the pages and apps, on purpose. The
        # SPPAS tab of the browser keeps one constant identity.
        self._htree.head.link(rel="logo icon", href=wapp_settings.icons + "sppas5.ico")

        # CSS SWAPP links. The theme carries the id the ThemeManager swaps the
        # href of: without it, a second link is created and themes accumulate.
        self._htree.head.link("stylesheet", wapp_settings.css + "main_swapp.css", link_type="text/css")
        self._htree.head.link("stylesheet", wapp_settings.css + "main_swapp_identity.css", link_type="text/css")
        theme_css = HTMLNode(self._htree.head.identifier, None, "link")
        theme_css.add_attribute("id", "wexa-theme")
        theme_css.add_attribute("rel", "stylesheet")
        theme_css.add_attribute("href", wapp_settings.css + "main_swapp_theme.css")
        theme_css.add_attribute("type", "text/css")
        self._htree.head.append_child(theme_css)
        # Application CSS
        self._populate_head_css()

        # JS SWAPP module
        script = HTMLNode(self._htree.head.identifier, None, "script", value=JS_INIT)
        self._htree.head.append_child(script)
        script = HTMLNode(self._htree.head.identifier, None, "script")
        script.add_attribute("src", wapp_settings.js + "sppas.js")
        script.add_attribute("type", "module")
        self._htree.head.append_child(script)

        # What the page starts once the loader is done -- the same for all
        # apps sharing this head. Not a module: the loader looks for the
        # function on the window.
        script = HTMLNode(self._htree.head.identifier, None, "script",
                          value=JS_BOOT_PAGE)
        self._htree.head.append_child(script)

        # Application JS
        self._populate_head_js()

    # -----------------------------------------------------------------------

    def populate_body_header(self, title, *args, **kwargs):
        """Populate the `<header>` section of the page.

        Replaces the current header with a :class:`SwappHeader` instance and
        delegates additional customization to `_populate_body_header()`.

        """
        self._htree.body_header = SwappHeader(self._htree.identifier, title)
        self._populate_body_header(*args, **kwargs)

    # -----------------------------------------------------------------------

    def _home_target(self) -> str:
        """Return the window name the Dashboard button of the menu switches to.

        Empty by default: the button replaces the content of the current
        tab. Override in a page living in its own persistent tab, so that
        going to the Dashboard switches to that named tab instead of
        turning its own tab into it -- see the Journal page.

        """
        return ""

    # -----------------------------------------------------------------------

    def populate_body_nav(self, *args, **kwargs):
        """Populate the `<nav>` section with navigation and accessibility tools.

        Adds base menu styling, contrast/theme accessibility buttons, and calls
        `_populate_body_nav()` for app-specific navigation items.

        """
        self._htree.body_nav.add_attribute("id", "nav-content")
        self._htree.body_nav.add_attribute("name", "nav-content")
        self._htree.body_nav.add_attribute("class", "nav-wexa")
        self._htree.body_nav.add_attribute("class", "side")
        self._htree.body_nav.add_attribute("class", "collapsible")

        self._populate_body_nav(*args, **kwargs)

    # -----------------------------------------------------------------------

    def populate_body_footer(self, *args, **kwargs):
        """Populate the `<footer>` section of the page.

        Replaces the footer with a :class:`SwappFooter` instance and invokes
        `_populate_body_footer()` for further customization.

        """
        self._htree.body_footer = SwappFooter(self._htree.identifier)
        self._populate_body_footer(*args, **kwargs)

    # -----------------------------------------------------------------------

    def populate_body_script(self):
        """Populate the `<script>` section of the page.

        To be overridden by child views when inline initialization scripts are
        required.

        """
        pass

    # -----------------------------------------------------------------------

    def update_accessibility(self):
        """Remove the color and contrast classes from the body.

        The accessibility state is carried by the classes of the root
        element: it is restored from the URL parameters by the
        AccessibilityManager of Whakerexa. Classes on the body would
        conflict with it.

        """
        body_classes = self._htree.get_body_attribute_value("class")
        if body_classes is None:
            return

        tab_classes = body_classes.split(" ")
        for class_name in ("contrast", "light", "dark"):
            if class_name in tab_classes:
                tab_classes.remove(class_name)

        self._htree.set_body_attribute("class", " ".join(tab_classes))

    # -----------------------------------------------------------------------
    # Static methods
    # -----------------------------------------------------------------------

    @staticmethod
    def append_responsive_menu_button(parent: HTMLNode) -> None:
        """Create and append the menu button, displayed by mobile screens.

        :param parent: (HTMLNode) the parent HTML node to append the button in

        """
        # The 'menu' button for a responsive #nav-content must be outside 'nav'.
        # The drawing is asked for by its name: the icon manager of Whakerexa
        # writes it into the button, first, before anything else it holds.
        menu_button = HTMLNode(parent.identifier, None, "button")
        menu_button.add_attribute("data-icon", "menu")
        menu_button.add_attribute("id", "menu-button")
        menu_button.add_attribute("name", "menu-button")
        menu_button.add_attribute("aria-label", "Menu")
        menu_button.add_attribute("aria-expanded", "false")
        menu_button.add_attribute("aria-controls", "nav-content")
        parent.append_child(menu_button)

        # Hidden checkbox required by MenuManager.initMobileToggle() to
        # track the mobile menu open/closed state.
        mobile_checkbox = HTMLNode(parent.identifier, None, "input")
        mobile_checkbox.add_attribute("type", "checkbox")
        mobile_checkbox.add_attribute("id", "mobile")
        mobile_checkbox.add_attribute("role", "button")
        mobile_checkbox.add_attribute("aria-label", "Menu")
        mobile_checkbox.add_attribute("aria-haspopup", "true")
        mobile_checkbox.add_attribute("aria-expanded", "false")
        parent.append_child(mobile_checkbox)

    # -----------------------------------------------------------------------

    @staticmethod
    def append_accessibility_buttons(parent: HTMLNode) -> None:
        """Create and append custom contrast and theme buttons.

        :param parent: (HTMLNode) the parent HTML node to append the buttons in

        """
        # These three buttons are drawn by Whakerexa itself -- the theme by
        # its ThemeManager, the two others by its AccessibilityManager. No
        # data-icon here: it would write a second drawing.
        css_theme_button = HTMLNode(parent.identifier, None, "button",
                                    value="<span>" + MSG_THEME + "</span>")
        css_theme_button.add_attribute("id", "btn-css-theme")
        css_theme_button.add_attribute("type", "button")
        css_theme_button.add_attribute("class", "menuitem")
        css_theme_button.add_attribute("aria-label", MSG_THEME)
        css_theme_button.add_attribute("aria-keyshortcuts", ">")
        css_theme_button.add_attribute("title", MSG_THEME + " (>)")
        css_theme_button.add_attribute("onclick", "window.themes && window.themes.next()")
        parent.append_child(css_theme_button)

        # contrast
        contrast_button = HTMLNode(parent.identifier, None, "button",
                                   value="<span>" + MSG_CONTRAST + "</span>")
        contrast_button.add_attribute("id", "btn-contrast")
        contrast_button.add_attribute("class", "menuitem accessibility")
        contrast_button.add_attribute("type", "button")
        contrast_button.add_attribute("aria-label", MSG_CONTRAST)
        contrast_button.add_attribute("aria-keyshortcuts", "+")
        contrast_button.add_attribute("title", MSG_CONTRAST + " (+)")
        contrast_button.add_attribute("aria-pressed", "false")
        contrast_button.add_attribute("onclick", "window.Wexa.accessibility.switchContrastScheme();")
        parent.append_child(contrast_button)

        # color scheme
        theme_button = HTMLNode(parent.identifier, None, "button",
                                value="<span>" + MSG_COLOR + "</span>")
        theme_button.add_attribute("id", "btn-color")
        theme_button.add_attribute("class", "menuitem accessibility")
        theme_button.add_attribute("type", "button")
        theme_button.add_attribute("aria-label", MSG_COLOR)
        theme_button.add_attribute("aria-keyshortcuts", "*")
        theme_button.add_attribute("title", MSG_COLOR + " (*)")
        theme_button.add_attribute("aria-pressed", "false")
        theme_button.add_attribute("onclick", "window.Wexa.accessibility.switchColorScheme();")
        parent.append_child(theme_button)

    # -----------------------------------------------------------------------

    @staticmethod
    def append_sppas_link_button(parent: HTMLNode) -> sppasHTMLButton:
        """Create and append the sppas link button.

        :param parent: (HTMLNode) the parent HTML node to append the buttons in
        :return: (sppasHTMLButton) the sppas link button node

        """
        _button = sppasHTMLButton(parent.identifier, identifier="link-sppas_button")
        _button.add_attribute("data-href", sg.__url__)
        _button.add_attribute("class", "menuitem")
        ic = _button.set_icon(sppasImagesAccess.get_logo_filename("sppas-logo-v5"))
        ic.add_attribute("alt", "")
        _button.set_text(None, MSG_WEB)
        parent.append_child(_button)
        return _button

    # -----------------------------------------------------------------------

    @staticmethod
    def append_home_link_button(parent: HTMLNode, home_target: str = "") -> HTMLNode:
        """Create and append the button leading to the Dashboard.

        An 'a' element, because the named target is read by the
        AccessibilityManager of Whakerexa on links only. The icon is the
        inline mono SVG of the other items: it follows --nav-fg-color,
        whatever the theme, which a PNG cannot do.

        :param parent: (HTMLNode) the parent HTML node to append the button in
        :param home_target: (str) Window name to switch to, empty to replace
        the content of the current tab
        :return: (HTMLNode) the home link button node

        """
        _button = HTMLNode(parent.identifier, "link-home_button", "a",
                           value="<span>" + MSG_DASHBOARD + "</span>")
        _button.add_attribute("data-icon", "dashboard")
        _button.add_attribute("id", "link-home_button")
        _button.add_attribute("href", wapp_settings.default_page())
        _button.add_attribute("role", "button")
        _button.add_attribute("aria-label", MSG_DASHBOARD)
        _button.add_attribute("aria-keyshortcuts", "q")
        _button.add_attribute("title", MSG_DASHBOARD + " (q)")
        _button.add_attribute("class", "menuitem")
        if len(home_target) > 0:
            _button.add_attribute("data-named-target", home_target)

        parent.append_child(_button)
        return _button

    # -----------------------------------------------------------------------

    @staticmethod
    def append_help_link_button(parent: HTMLNode, page: str = "") -> HTMLNode:
        """Create and append the button opening the document of the app.

        One document per app holds both its user manual and its conceptual
        folder.

        An app whose document is not written yet gets the button disabled:
        the place of the help is the same everywhere, whether or not there
        is something to read.

        :param parent: (HTMLNode) the parent HTML node to append the button in
        :param page: (str) Path of the document, empty while it is unwritten
        :return: (HTMLNode) the help link button node

        """
        _button = HTMLNode(parent.identifier, "link-help_button", "a",
                           value="<span>" + MSG_HELP + "</span>")
        _button.add_attribute("data-icon", "help")
        _button.add_attribute("id", "link-help_button")
        _button.add_attribute("role", "button")
        _button.add_attribute("aria-label", MSG_HELP)
        _button.add_attribute("aria-keyshortcuts", "h")
        # What the label does not say: the key doing the same thing.
        _button.add_attribute("title", MSG_HELP + " (h)")
        _button.add_attribute("class", "menuitem")
        if len(page) > 0:
            _button.add_attribute("href", page)
        else:
            _button.add_attribute("aria-disabled", "true")

        parent.append_child(_button)
        return _button

    # -----------------------------------------------------------------------

    @staticmethod
    def append_trace_link_button(parent: HTMLNode) -> HTMLNode:
        """Create and append the button opening the Traces page.

        The page opens in its named tab: whatever the app the button is
        clicked from, the single "sppas_infos" tab is reused and reloaded.
        The loader registers it with handleLinksWithParameters(), through
        its data-links attribute -- see wapphead.py.

        :param parent: (HTMLNode) the parent HTML node to append the button in
        :return: (HTMLNode) the trace link button node

        """
        _button = HTMLNode(parent.identifier, None, "button",
                           value="<span>" + MSG_JOURNAL + "</span>")
        _button.add_attribute("data-icon", "info-square")
        _button.add_attribute("id", "link-trace_button")
        _button.add_attribute("aria-label", MSG_JOURNAL)
        _button.add_attribute("aria-keyshortcuts", "j")
        _button.add_attribute("title", MSG_JOURNAL + " (j)")
        _button.add_attribute("type", "button")
        _button.add_attribute("data-href", "journal.html")
        _button.add_attribute("data-target", "sppas_infos")
        _button.add_attribute("class", "menuitem")
        parent.append_child(_button)
        return _button

    # -----------------------------------------------------------------------

    @staticmethod
    def append_feedback_link_button(parent: HTMLNode) -> HTMLNode:
        """Create and append the button opening the Feedback page.

        The page opens in a new tab: the user sends a feedback without
        leaving the current app. The loader registers it, through its
        data-links attribute -- see wapphead.py.

        :param parent: (HTMLNode) the parent HTML node to append the button in
        :return: (HTMLNode) the feedback link button node

        """
        _button = HTMLNode(parent.identifier, None, "button",
                           value="<span>" + MSG_FEEDBACK + "</span>")
        _button.add_attribute("data-icon", "feedback")
        _button.add_attribute("id", "link-feedback_button")
        _button.add_attribute("aria-label", "Feedback")
        _button.add_attribute("type", "button")
        _button.add_attribute("data-href", "feedback.html")
        _button.add_attribute("class", "menuitem")
        parent.append_child(_button)
        return _button

    # -----------------------------------------------------------------------

    @staticmethod
    def append_pin_button(parent: HTMLNode) -> None:
        """Create and append the pin button of a collapsible menu.

        :param parent: (HTMLNode) the parent HTML node to append the buttons in

        """
        _button = HTMLNode(parent.identifier, None, "button",
                           value="<span>" + MSG_PIN + "</span>")
        _button.add_attribute("data-icon", "pin")
        _button.add_attribute("id", "pin-menu")
        _button.add_attribute("aria-label", "Pin Menu")
        _button.add_attribute("type", "button")
        _button.add_attribute("aria-pressed", "false")
        _button.add_attribute("class", "menuitem")
        parent.append_child(_button)
        # WAI-ARIA Authoring Practices 1.2: Use aria-controls only when the controlled
        # element is not adjacent or the relationship is not otherwise apparent to the user.
        # Notice that _button.add_attribute("aria-controls", "nav-content") is
        # ** not compatible with WhakerPy **.

    # -----------------------------------------------------------------------

    @staticmethod
    def append_exit_button(parent: HTMLNode) -> None:
        """Create and append the button leaving SPPAS.

        The label says one word: what the word does is written in the tip,
        because leaving is the one action that cannot be undone.

        :param parent: (HTMLNode) the parent HTML node to append the buttons in

        """
        exit_button = HTMLNode(parent.identifier, None, "button",
                               value="<span>" + MSG_EXIT + "</span>")
        exit_button.add_attribute("data-icon", "logout")
        exit_button.add_attribute("id", "exit-menu")
        exit_button.add_attribute("aria-label", MSG_EXIT)
        exit_button.add_attribute("title", MSG_EXIT_TIP)
        exit_button.add_attribute("type", "button")
        exit_button.add_attribute("aria-pressed", "false")
        exit_button.add_attribute("class", "menuitem menu-exit")
        parent.append_child(exit_button)

    # -----------------------------------------------------------------------

    @staticmethod
    def append_alert_dialogs(parent: HTMLNode):
        """Append the nodes of hidden dialog elements, used for messages.

        :param parent: (HTMLNode) The parent HTML node.

        """
        # A dialog to display any error message after a posted event
        dlg = HTMLNode(parent.identifier, "error_dialog", "dialog",)
        dlg.add_attribute("id", "error_dialog")
        dlg.add_attribute("role", "alertdialog")
        # Its content is written by the JS: the name has to be given here.
        dlg.add_attribute("aria-label", MSG_ERROR)
        dlg.add_attribute("class", "error hidden-alert")
        parent.append_child(dlg)

        # A dialog to display any information message after a posted event
        dlg = HTMLNode(parent.identifier, "info_dialog", "dialog",)
        dlg.add_attribute("id", "info_dialog")
        dlg.add_attribute("role", "alertdialog")
        dlg.add_attribute("aria-label", MSG_INFORMATION)
        dlg.add_attribute("class", "info hidden-alert")
        parent.append_child(dlg)

    # -----------------------------------------------------------------------
    # Protected
    # -----------------------------------------------------------------------

    def _populate_head_css(self, *args, **kwargs):
        """To be overridden by children.

        """
        self._htree.head.link("stylesheet", wapp_settings.css + "app_setup.css", link_type="text/css")

    # -----------------------------------------------------------------------

    def _populate_head_js(self, *args, **kwargs):
        """To be overridden by children.

        """
        pass

    # -----------------------------------------------------------------------

    def _populate_body_header(self, *args, **kwargs):
        """To be overridden by children.

        """
        pass

    # -----------------------------------------------------------------------

    def _populate_body_nav(self, *args, **kwargs):
        """To be overridden by children.

        """
        pass

    # -----------------------------------------------------------------------

    def _populate_body_footer(self, *args, **kwargs):
        """Can be overridden by children.

        """
        self._htree.body_footer.append_sppas_splash()
        self._htree.body_footer.append_copyright()
        self._htree.body_footer.append_scroll_top()
