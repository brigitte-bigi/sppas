import { BaseManager } from '../transport/base_manager.js';
import { OnLoadManager } from '../dom-loader.js';
import { icons } from './icons.js';

/**
:filename: statics.js.customize.theme_manager.js
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: A class to manage CSS theme switching for Whakerexa.

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

Architecture:
  - Two orthogonal modes (light/dark, normal/contrast) are managed by AccessibilityManager.
  - CSS themes (wexa_theme_*.css) are managed HERE, independently.
  - Theme switching swaps the href of a <link id="wexa-theme"> element injected in <head>.
  - The active theme is persisted via the URL parameter "wexa_theme",
    propagated across internal navigation through setUrlWithParameters().

Usage:
  import { ThemeManager } from './customize/theme_manager.js';
  const themes = new ThemeManager();
  themes.register('aurora', 'css/extras/wexa_theme_aurora.css');
  themes.activate('aurora');   // apply a named theme
  themes.next();               // cycle to the next registered theme

*/

/**
 * Manage CSS theme switching for a Whakerexa page.
 *
 * Themes are standalone CSS files containing only an @layer theme block.
 * Each theme is registered under a name and a path relative to the page.
 * The active theme is persisted via the URL parameter "wexa_theme" and
 * propagated across internal navigation. "" always means the default theme.
 */
export class ThemeManager extends BaseManager {

    // -----------------------------------------------------------------------
    // FIELDS
    // -----------------------------------------------------------------------

    #themes;        // Map<name, path>
    #activeTheme;   // "" or a registered name
    #defaultTheme;  // "" or a registered name applied when no URL param is present

    static get THEME_PARAMETER_NAME() { return "wexa_theme"; }
    static get LINK_ID()              { return "wexa-theme"; }

    // -----------------------------------------------------------------------
    // CONSTRUCTOR
    // -----------------------------------------------------------------------

    /**
     * Create a new ThemeManager.
     *
     * Restores the active theme from the URL parameter on page load.
     * Propagates the theme parameter through all internal links.
     *
     * @constructor
     * @returns {ThemeManager}
     */
    constructor() {
        super();
        this.#themes = new Map();
        this.#activeTheme = "";
        this.#defaultTheme = "";

        OnLoadManager.addLoadFunction(this.#loadFromUrl.bind(this));
        OnLoadManager.addLoadFunction(this.#injectButtonIcon.bind(this));
    }

    // -----------------------------------------------------------------------
    // GETTERS
    // -----------------------------------------------------------------------

    /**
     * Names of all registered themes, in registration order.
     * @returns {string[]}
     */
    get themeNames() {
        return [...this.#themes.keys()];
    }

    // -----------------------------------------------------------------------

    /**
     * Name of the currently active theme, or "" for the default.
     * @returns {string}
     */
    get activeTheme() {
        return this.#activeTheme;
    }

    // -----------------------------------------------------------------------
    // PUBLIC METHODS
    // -----------------------------------------------------------------------

    /**
     * Register a CSS theme under a name.
     *
     * The path must be relative to the HTML page loading the theme.
     * Registration order defines the cycle order used by next().
     *
     * @param {string} name - Identifier for this theme (e.g. "aurora").
     * @param {string} path - Path to the CSS file (e.g. "css/extras/wexa_theme_aurora.css").
     * @returns {void}
     */
    register(name, path) {
        if (typeof name !== 'string' || typeof path !== 'string') {
            console.error("ThemeManager.register: name and path must be strings.");
            return;
        }
        this.#themes.set(name, path);
    }

    // -----------------------------------------------------------------------

    /**
     * Declare the theme to apply when no URL parameter is present, or when
     * it names a theme the page does not carry.
     *
     * Must be called after register(). Ignored if name is unknown.
     *
     * @param {string} name - A registered theme name.
     * @returns {void}
     */
    setDefault(name) {
        if (!this.#themes.has(name)) {
            console.error(`ThemeManager.setDefault: unknown theme "${name}".`);
            return;
        }
        this.#defaultTheme = name;

        const params = new URLSearchParams(window.location.search);
        if (params.has(ThemeManager.THEME_PARAMETER_NAME)) {

            // What the address says, when it is a theme the page carries.
            // A name it does not carry does not leave the page without a
            // theme: the default applies, and the address is written with it.
            const urlTheme = params.get(ThemeManager.THEME_PARAMETER_NAME);
            if (this.#themes.has(urlTheme)) {
                this.activate(urlTheme);
            } else {
                console.warn(`ThemeManager.setDefault: the address names "${urlTheme}", which is not declared. The default "${name}" applies.`);
                this.activate(name);
            }

        } else if (this.#activeTheme === "") {
            this.activate(name);
        }
    }

    // -----------------------------------------------------------------------

    /**
     * Activate a theme by name, or restore the default with "".
     *
     * Injects or updates a <link id="wexa-theme"> element in <head>.
     * Updates the URL parameter and notifies the server.
     *
     * @async
     * @param {string} name - Theme name, or "" for the default.
     * @returns {Promise<void>}
     */
    async activate(name) {
        if (name !== "" && !this.#themes.has(name)) {
            console.error(`ThemeManager.activate: unknown theme "${name}".`);
            return;
        }

        this.#activeTheme = name;
        this.#applyLink(name === "" ? "" : this.#themes.get(name));
        history.replaceState(null, '', this.setUrlWithParameters(window.location.href));
        await this.postEvents({"theme": name});
    }

    // -----------------------------------------------------------------------

    /**
     * Cycle to the next registered theme.
     *
     * Order: default ("") → theme1 → theme2 → … → default.
     *
     * @async
     * @returns {Promise<void>}
     */
    async next() {
        const names = this.themeNames;
        if (names.length === 0) {
            return;
        }

        if (this.#activeTheme === "") {
            const defaultIdx = names.indexOf(this.#defaultTheme);
            const nextIdx = defaultIdx + 1;
            await this.activate(nextIdx >= names.length ? "" : names[nextIdx]);
            return;
        }

        const idx = names.indexOf(this.#activeTheme);
        const nextIdx = idx + 1;

        await this.activate(nextIdx >= names.length ? this.#defaultTheme : names[nextIdx]);
    }

    // -----------------------------------------------------------------------

    /**
     * Append the wexa_theme parameter to a URL.
     *
     * Removes the parameter when no theme is active.
     *
     * @param {string} url - The URL to modify.
     * @returns {string} The updated URL.
     */
    setUrlWithParameters(url) {
        if (url === null || url === '') {
            return '';
        }
        const customUrl = new URL(url, window.location.href);

        if (this.#activeTheme !== '') {
            customUrl.searchParams.set(ThemeManager.THEME_PARAMETER_NAME, this.#activeTheme);
        } else {
            customUrl.searchParams.delete(ThemeManager.THEME_PARAMETER_NAME);
        }

        return customUrl.href;
    }

    // -----------------------------------------------------------------------
    // PRIVATE METHODS
    // -----------------------------------------------------------------------

    /**
     * Inject the theme SVG icon into btn-css-theme if present.
     * @private
     * @async
     * @returns {Promise<void>}
     */
    async #injectButtonIcon() {
        await icons.inject(document.getElementById('btn-css-theme'), 'theme');
    }

    // -----------------------------------------------------------------------

    /**
     * Inject or update the <link id="wexa-theme"> element.
     * Removes it when path is empty (default theme).
     * @private
     * @param {string} path
     */
    #applyLink(path) {
        let link = document.getElementById(ThemeManager.LINK_ID);

        if (path === "") {
            if (link !== null) {
                link.remove();
            }
            return;
        }

        if (link === null) {
            link = document.createElement('link');
            link.id = ThemeManager.LINK_ID;
            link.rel = 'stylesheet';
            document.head.appendChild(link);
        }

        link.href = path;
    }

    // -----------------------------------------------------------------------

    /**
     * Restore the active theme from the URL parameter on page load.
     * Silently ignored if the saved name is not registered.
     * @private
     * @async
     * @returns {Promise<void>}
     */
    async #loadFromUrl() {
        const params = new URLSearchParams(window.location.search);

        if (params.has(ThemeManager.THEME_PARAMETER_NAME)) {
            const name = params.get(ThemeManager.THEME_PARAMETER_NAME);
            if (this.#themes.has(name)) {
                await this.activate(name);
            } else {
                console.log(ThemeManager.THEME_PARAMETER_NAME + " unknown value: " + name);
            }
        } else if (this.#defaultTheme !== "" && this.#activeTheme === "") {
            await this.activate(this.#defaultTheme);
        }
    }

}

