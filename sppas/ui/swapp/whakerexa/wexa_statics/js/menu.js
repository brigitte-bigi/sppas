import { WexaLogger } from './logger.js';

/**
 :filename: wexa_statics.js.menu.js
 :author: Brigitte Bigi
 :contact: contact@sppas.org
 :summary: A class to manage menus/submenus in web apps.

 -------------------------------------------------------------------------

 This file is part of Whakerexa: https://github.com/brigitte-bigi/Whakerexa

 Copyright (C) 2023-2026 Brigitte Bigi, CNRS
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

 */

'use strict';


// --------------------------------------------------------------------------
// Class: SubMenuManager
// --------------------------------------------------------------------------

/**
 * Manage the behavior of a single accessible submenu.
 *
 * This class handles only the submenu content itself:
 * open/close transitions, focus management, and CSS-based
 * positioning or alignment. It does not handle any parent
 * menu logic or toggle button events.
 */
class SubMenuManager {
    // --------------------------------------------------------------------
    // Protected members
    // --------------------------------------------------------------------
    #asideElement;
    #menuLinks;
    _focusTrapHandler;

    // --------------------------------------------------------------------
    // Constructor
    // --------------------------------------------------------------------

    /**
     * Create a SubMenuManager instance.
     *
     * @param {string} asideId - ID of the aside element containing the submenu.
     */
    constructor(asideId = 'appmenu') {
        this.#asideElement = document.getElementById(asideId);

        // Include both <a> and <button> elements as focusable links.
        this.#menuLinks = this.#asideElement
            ? this.#asideElement.querySelectorAll('a, button')
            : [];

        // Bind the focus trap handler to preserve context when used as an event listener.
        this._focusTrapHandler = this.#trapFocus.bind(this);
    }

    // --------------------------------------------------------------------
    // Public methods
    // --------------------------------------------------------------------

    /**
     * Open the submenu and manage its internal focus state.
     *
     * @returns {void}
     */
    openSubmenu() {
        this.#setOpenState(true);
    }

    // --------------------------------------------------------------------

    /**
     * Close the submenu and disable focus trapping.
     *
     * @returns {void}
     */
    closeSubmenu() {
        this.#setOpenState(false);
    }

    // --------------------------------------------------------------------
    // Private methods
    // --------------------------------------------------------------------

    /**
     * Define the open or closed state of the submenu.
     *
     * When opened, tabindex values are enabled and focus is trapped
     * within the submenu. When closed, all links become unfocusable.
     *
     * @private
     * @param {boolean} open - True to open the submenu, false to close it.
     * @returns {void}
     */
    #setOpenState(open) {
        if (this.#asideElement === null) return;

        const opened = open === true;

        // Toggle CSS class to open or close the submenu.
        this.#asideElement.classList.toggle('open', opened);

        // Update tab index of contained links.
        this.#setLinksTabIndex(opened ? 0 : -1);

        // Manage focus trapping when opened.
        if (opened === true) {
            document.addEventListener('keydown', this._focusTrapHandler, true);

            const onTransitionEnd = (ev) => {
                if (['left', 'right', 'top', 'bottom'].includes(ev.propertyName)) {
                    this.#menuLinks[0]?.focus();
                    this.#asideElement.removeEventListener('transitionend', onTransitionEnd);
                }
            };
            this.#asideElement.addEventListener('transitionend', onTransitionEnd);
        } else {
            document.removeEventListener('keydown', this._focusTrapHandler, true);
        }

        // Apply CSS-based positioning and alignment.
        this.#adjustSubmenuPosition();
        this.#adjustSubmenuAlignment();
    }

    // --------------------------------------------------------------------

    /**
     * Read CSS variable '--appmenu-position' and update the data attribute.
     *
     * @private
     * @returns {void}
     */
    #adjustSubmenuPosition() {
        const position = getComputedStyle(this.#asideElement)
            .getPropertyValue('--appmenu-position')
            .trim();

        // Default to 'left' if no value found.
        this.#asideElement.setAttribute('data-submenu-position', position || 'left');

        // Force a reflow to ensure visual update.
        this.#asideElement.offsetHeight;
    }

    // --------------------------------------------------------------------

    /**
     * Read CSS variable '--appmenu-align' and update alignment attributes.
     *
     * @private
     * @returns {void}
     */
    #adjustSubmenuAlignment() {
        const align = getComputedStyle(this.#asideElement)
            .getPropertyValue('--appmenu-align')
            .trim();

        const [horizontal = 'center', vertical = 'center'] = align.split(' ');

        this.#asideElement.setAttribute('data-submenu-align-horizontal', horizontal);
        this.#asideElement.setAttribute('data-submenu-align-vertical', vertical);

        // Force reflow to apply updated alignment.
        this.#asideElement.offsetHeight;
    }

    // --------------------------------------------------------------------

    /**
     * Trap focus inside the submenu when the Tab key is pressed.
     *
     * @private
     * @param {KeyboardEvent} e - The keyboard event.
     * @returns {void}
     */
    #trapFocus(e) {
        if (e.key !== 'Tab') return;

        const focusable = Array.from(this.#menuLinks);
        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey) {
            // Shift + Tab: move from first to last
            if (document.activeElement === first) {
                e.preventDefault();
                last.focus();
            }
        } else {
            // Tab: move from last to first
            if (document.activeElement === last) {
                e.preventDefault();
                first.focus();
            }
        }
    }

    // --------------------------------------------------------------------

    /**
     * Set tabindex for each submenu link.
     *
     * @private
     * @param {number} value - Tabindex value (-1 to disable, 0 to enable).
     * @returns {void}
     */
    #setLinksTabIndex(value) {
        for (const link of this.#menuLinks) {
            link.tabIndex = value;
        }
    }
}

// --------------------------------------------------------------------------
// Manager for an accessible menu
// --------------------------------------------------------------------------

/**
 * @class MenuManager
 * @classdesc
 * Controls the behavior of navigation menus within Whakerexa.
 * This class manages both global and contextual menus, registers
 * submenus, and ensures accessibility compliance (ARIA, focus, keyboard).
 *
 * A single instance should control one main <nav> element.
 * The default target is the element with id 'nav-content', unless
 * another id is provided at construction.
 *
 * @example
 * // Typical initialization
 * const menu = new MenuManager();                // Uses #nav-content
 * menu.initSideMenu();
 * menu.registerSubmenu('appmenu-profile', 'submenu-toggle-profile');
 *
 * @property {HTMLElement} #navElement - The main navigation element controlled by this instance.
 * @property {Array<SubMenuManager>} #submenus - A list of registered submenus managed by this instance.
 * @static {string} DEFAULT_NAV_ID - Default id of the main navigation element.
 *
 */
export class MenuManager {
    // --------------------------------------------------------------------
    // Protected members
    // --------------------------------------------------------------------
    // The '<nav>' element this class is managing
    #navElement;
    // A dictionary of registered submenus: each key is the submenu
    // identifier, and the value is its associated toggle button element.
    #submenus = new Map();

    // --------------------------------------------------------------------
    // Public members
    // --------------------------------------------------------------------
    static DEFAULT_NAV_ID = 'nav-content';

    // ----------------------------------------------------------------------

    /**
     * Creates a manager bound to a specific <nav>.
     *
     * @param {string} [navId=MenuManager.DEFAULT_NAV_ID] - ID of the <nav> to control.
     * @throws {Error} If the <nav> element cannot be found.
     */
    constructor(navId = MenuManager.DEFAULT_NAV_ID) {
        this.#navElement = document.getElementById(navId);
        if (!this.#navElement) {
            throw new Error(`MenuManager: nav with id '${navId}' not found.`);
        }

        // Dictionary of registered submenus.
        this.#submenus = new Map();

        document.addEventListener('click', (e) => this.#handleBodyClick(e), true);
    }

    // ----------------------------------------------------------------------

    /**
     * Register a submenu and its toggle button.
     *
     * @param {string} asideId - ID of the submenu <aside> element.
     * @param {string} toggleButtonId - ID of the button controlling this submenu.
     * @returns {void}
     */
    registerSubmenu(asideId, toggleButtonId) {
        const aside = document.getElementById(asideId);
        const toggle = document.getElementById(toggleButtonId);

        // Validate required elements.
        if (aside === null || toggle === null) {
            WexaLogger.warn(`MenuManager: Invalid submenu registration: '${asideId}'.`);
            return;
        }

        // Create submenu instance and store association.
        const submenu = new SubMenuManager(asideId);
        this.#submenus.set(submenu, toggle);

        this.#initToggleAttributes(toggle, asideId);
        this.#bindToggleEvents(submenu, toggle);
    }

    // ----------------------------------------------------------------------

    /**
     * Initializes pin/unpin behavior for a side menu.
     *
     * This handles the click on the "pin menu" button to expand/collapse
     * the side navigation bar, updating ARIA attributes accordingly.
     *
     * @param {string} navSelector - CSS selector of the side nav element.
     * @param {string} pinButtonId - ID of the pin/unpin button.
     * @returns {void}
     */
    initSideMenu(navSelector = 'nav#nav-content.side.collapsible', pinButtonId = 'pin-menu') {
        const nav = document.querySelector(navSelector);
        const pinBtn = document.getElementById(pinButtonId);

        if (!nav) {
            WexaLogger.warn(`MenuManager: Side menu not found with selector '${navSelector}'.`);
            return;
        }
        if (!pinBtn) {
            WexaLogger.warn(`MenuManager: Pin button not found with id '${pinButtonId}'.`);
            return;
        }

        pinBtn.addEventListener('click', () => {
            const isPinned = nav.classList.toggle('expanded');
            nav.setAttribute('aria-pinned', isPinned ? 'true' : 'false');
            pinBtn.setAttribute('aria-pressed', String(isPinned));
            pinBtn.setAttribute('aria-label', isPinned ? 'Unpin menu' : 'Pin menu');
        });
    }

    // ----------------------------------------------------------------------

    /**
     * Initialize mobile menu toggle behavior.
     *
     * Link the hidden checkbox, navigation container, and visible menu button.
     * Ensure synchronization between checkbox state and ARIA attributes.
     *
     * @param {string} checkboxId - ID of the controlling checkbox.
     * @param {string} buttonId - ID of the visible menu button.
     * @returns {void}
     */
    initMobileToggle(checkboxId = 'mobile', buttonId = 'menu-button') {
        const checkbox = document.getElementById(checkboxId);
        const button = document.getElementById(buttonId);

        // Validate required elements.
        if (checkbox === null || button === null) {
            WexaLogger.warn('MenuManager: Missing elements for mobile toggle.');
            return;
        }

        // Bind state synchronization.
        checkbox.addEventListener('change', () => {
            this.#updateMobileState(checkbox, button);
        });

        // Bind button activation.
        button.addEventListener('click', () => {
            checkbox.checked = !checkbox.checked;
            this.#updateMobileState(checkbox, button);
        });

        // Initialize current state.
        this.#updateMobileState(checkbox, button);
    }

    // ----------------------------------------------------------------------
    // Private
    // ----------------------------------------------------------------------

    /**
     * Initialize ARIA attributes of a toggle button.
     *
     * @private
     * @param {HTMLElement} toggle - Toggle button element.
     * @param {string} asideId - ID of the associated submenu.
     */
    #initToggleAttributes(toggle, asideId) {
        toggle.setAttribute('aria-controls', asideId);
        // What the page wrote is kept: 'true' and 'menu' both say a popup, and
        // the value is the author's. One is written only when none is there.
        if (toggle.hasAttribute('aria-haspopup') === false) {
            toggle.setAttribute('aria-haspopup', 'menu');
        }
        toggle.setAttribute('aria-expanded', 'false');
    }

    // ----------------------------------------------------------------------

    /**
     * Bind activation events for the toggle button.
     *
     * @private
     * @param {SubMenuManager} submenu - Associated submenu manager.
     * @param {HTMLElement} toggle - Toggle button element.
     */
    #bindToggleEvents(submenu, toggle) {
        const activate = (event) => {
            event.preventDefault();
            event.stopPropagation();

            // Collapse main menu if not pinned.
            const pin = document.getElementById('pin-menu');
            const isPinned = pin !== null && pin.getAttribute('aria-pressed') === 'true';
            if (isPinned === false) {
                this.#navElement.classList.remove('expanded');
                this.#navElement.setAttribute('aria-expanded', 'false');
            }

            this.#closeOtherSubmenus(submenu);
            submenu.openSubmenu();
            toggle.setAttribute('aria-expanded', 'true');
        };

        toggle.addEventListener('click', activate);
        toggle.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') activate(e);
        });
    }

    // ----------------------------------------------------------------------

    /**
     * Close all registered submenus except the given one.
     *
     * @private
     * @param {SubMenuManager} current - Submenu to keep open.
     */
    #closeOtherSubmenus(current) {
        for (const [submenu, toggle] of this.#submenus) {
            if (submenu !== current) {
                submenu.closeSubmenu();
                toggle.setAttribute('aria-expanded', 'false');
            }
        }
    }

    // ----------------------------------------------------------------------

    /**
     * Handle clicks on the document body to close submenus.
     *
     * @private
     * @param {MouseEvent} event - The click event.
     * @returns {void}
     */
    #handleBodyClick(event) {
        const target = event.target;

        // Ignore clicks inside the main nav or any open aside
        const insideNav   = this.#navElement.contains(target);
        const insideAside = target.closest('aside.appmenu.open') !== null;

        if (insideNav || insideAside) return;

        // Otherwise close all submenus
        for (const [submenu, toggle] of this.#submenus) {
            submenu.closeSubmenu();
            toggle.setAttribute('aria-expanded', 'false');
        }

        // Remove transient state flags
        this.#navElement.classList.remove('submenu-active');
    }

    // ----------------------------------------------------------------------

    /**
     * Update ARIA attributes and menu class for the mobile toggle.
     *
     * @private
     * @param {HTMLInputElement} checkbox - Checkbox controlling the menu.
     * @param {HTMLElement} button - Visible menu button.
     * @returns {void}
     */
    #updateMobileState(checkbox, button) {
        const expanded = checkbox.checked === true;
        this.#navElement.classList.toggle('expanded', expanded);
        this.#navElement.setAttribute('aria-expanded', String(expanded));
        button.setAttribute('aria-expanded', String(expanded));
    }

}
