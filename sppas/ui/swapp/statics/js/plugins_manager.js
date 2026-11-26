const wexa_statics_js = window.WEXA_JS_PATH;
const { DialogManager } = await import(`${wexa_statics_js}/dialog.js`);
const { BaseManager } = await import(`${wexa_statics_js}/transport/base_manager.js`);
const dialogManager = new DialogManager();

const ID_FORM = 'plugins_form';
const EVENT_BAKE = 'event_bake';
const TASK_RUN = 'plugins_run';
const FIELD_SELECTED = 'plugins_sel_';
const ID_RUN_STATE = 'plugins_run_state';

/**
 * :filename: sppas.ui.swapp.statics.js.plugins_manager.js
 * :author: Brigitte Bigi
 * :contact: contact@sppas.org
 * :summary: JS for the Plugins application
 *
 * .. _This file is part of SPPAS: https://sppas.org/
 * ..
 *     -------------------------------------------------------------------------
 *
 *      ######   ########   ########      ###      ######
 *     ##    ##  ##     ##  ##     ##    ## ##    ##    ##     the automatic
 *     ##        ##     ##  ##     ##   ##   ##   ##            annotation
 *      ######   ########   ########   ##     ##   ######        and
 *           ##  ##         ##         #########        ##        analysis
 *     ##    ##  ##         ##         ##     ##  ##    ##         of speech
 *      ######   ##         ##         ##     ##   ######
 *
 *     Copyright (C) 2011-2026  Brigitte Bigi, CNRS
 *     Laboratoire Parole et Langage, Aix-en-Provence, France
 *
 *     This program is free software: you can redistribute it and/or modify
 *     it under the terms of the GNU Affero General Public License as published by
 *     the Free Software Foundation, either version 3 of the License, or
 *     (at your option) any later version.
 *
 *     This program is distributed in the hope that it will be useful,
 *     but WITHOUT ANY WARRANTY; without even the implied warranty of
 *     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *     GNU Affero General Public License for more details.
 *
 *     You should have received a copy of the GNU Affero General Public License
 *     along with this program.  If not, see <https://www.gnu.org/licenses/>.
 *
 *     This banner notice must not be removed.
 *
 *     -------------------------------------------------------------------------
 */

'use strict';

// --------------------------------------------------------------------------
// Class: PluginsManager. Controls the page plugins.html
// --------------------------------------------------------------------------

/**
 * The About of each plugin is a dialog the server wrote in the page: its
 * button opens it, and nothing is asked of the server. The options of a
 * plugin are in the window the service of the options offers, which drives
 * it. What starts the runs follows the switches of the plugins, whoever
 * changes them.
 *
 * handlePluginsManagerOnLoad() has to be invoked **after** the DOM is loaded,
 * and after the windows of the options are handled.
 */
export default class PluginsManager extends BaseManager {

    // ------------------------------------------------------------------------
    // Constructor
    // ------------------------------------------------------------------------

    constructor() {
        super();
    }

    // ------------------------------------------------------------------------
    // Initialization
    // ------------------------------------------------------------------------

    /**
     * Attach the listeners of the page.
     *
     * @returns {void}
     */
    handlePluginsManagerOnLoad() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.#attach();
            });
        } else {
            this.#attach();
        }
    }

    // ------------------------------------------------------------------------
    // Private
    // ------------------------------------------------------------------------

    /**
     * Attach the listeners of the dialogs, of the form of the page, and of the switches of the plugins.
     *
     * @private
     * @returns {void}
     */
    #attach() {
        this.#attachDialogs();

        const form = document.getElementById(ID_FORM);
        if (form instanceof HTMLFormElement) {
            form.addEventListener('submit', (e) => this.#onFormSubmit(e));
        }

        // The switches of the plugins: what starts the runs follows them.
        document.querySelectorAll(`input[name^="${FIELD_SELECTED}"]`).forEach((input) => {
            input.addEventListener('change', () => this.#updateRun());
        });
    }

    // ------------------------------------------------------------------------

    /**
     * Have each button which opens a dialog of the page open it, as a modal.
     *
     * @private
     * @returns {void}
     */
    #attachDialogs() {
        document.querySelectorAll('button[aria-haspopup="dialog"][aria-controls]').forEach((button) => {
            button.addEventListener('click', () => {
                dialogManager.open(button.getAttribute('aria-controls'), true);
            });
        });
    }

    // ------------------------------------------------------------------------

    /**
     * Handle submit of the form of the page.
     *
     * The options of a plugin are asked for by the service of the options,
     * which attached its listener first: what it answered is left to it.
     * Otherwise, add the accessibility parameters (theme, contrast...) to the
     * address the form is sent to.
     *
     * @private
     * @param {SubmitEvent} event
     * @returns {void}
     */
    #onFormSubmit(event) {
        const form = event.currentTarget;
        if (!(form instanceof HTMLFormElement)) {
            return;
        }
        if (event.defaultPrevented === true) {
            return;
        }

        form.action = window.Wexa.accessibility.setUrlWithParameters(form.action);
    }

    // ------------------------------------------------------------------------

    /**
     * Enable the button which starts the runs when a plugin is selected, and disable it otherwise.
     *
     * What says no plugin is selected is hidden when one is, and shown otherwise.
     *
     * @private
     * @returns {void}
     */
    #updateRun() {
        const selected = document.querySelector(`input[name^="${FIELD_SELECTED}"]:checked`) !== null;

        const button = document.querySelector(`button[name="${EVENT_BAKE}"][value="${TASK_RUN}"]`);
        if (button !== null) {
            if (selected === true) {
                button.disabled = false;
                button.removeAttribute('aria-describedby');
            } else {
                button.disabled = true;
                button.setAttribute('aria-describedby', ID_RUN_STATE);
            }
        }

        const state = document.getElementById(ID_RUN_STATE);
        if (state !== null) {
            state.classList.toggle('hidden', selected);
        }
    }

}
