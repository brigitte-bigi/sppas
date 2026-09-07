const wexa_statics_js = window.WEXA_JS_PATH;
const { WexaLogger } = await import(`${wexa_statics_js}/logger.js`);
const { BaseManager } = await import(`${wexa_statics_js}/transport/base_manager.js`);
const { ProgressBar } = await import(`${wexa_statics_js}/progressbar.js`);

/**
 * :filename: sppas.ui.swapp.statics.js.setup_manager.js
 * :author: Brigitte Bigi
 * :contact: contact@sppas.org
 * :summary: JS for the Setup application
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
// Class: SetupManager. Controls the page setup.html
// --------------------------------------------------------------------------

/**
 * This class orchestrates user interactions within *setup.html*. It attaches event
 * listeners to the buttons of the main container, sends corresponding asynchronous
 * requests to the server, and updates the DOM in response. It relies on BaseManager
 * for communication logic and form submission, and on WexaLogger for debug output.
 *
 * handleSetupManagerOnLoad() has to be invoked **after** the DOM is loaded.
 *
 */
export default class SetupManager extends BaseManager {

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
     * Register event listeners once the DOM content is loaded.
     *
     * This method ensures that all setup-related listeners are attached
     * whether the DOM is already available or still loading.
     *
     * @returns {void}
     */
    handleSetupManagerOnLoad() {
        WexaLogger.debug('Attach Setup listeners');
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.attachSetupListeners();
                this.attachCheckboxListeners();
                this.#resumeProgressPolling();
            });
        } else {
            this.attachSetupListeners();
            this.attachCheckboxListeners();
            this.#resumeProgressPolling();
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Start the progress polling loop of the installation.
     *
     * The polling is the only sender of the 'complete' event leading to
     * the completed page.
     *
     * @returns {void}
     */
    #startProgressPolling() {
        const progressBar = new ProgressBar({
            requestManager: this._requestManager,
            targetUrl: '/setup.html',
            intervalMs: 1000
        });
        progressBar.start();
    }

    // ------------------------------------------------------------------------

    /**
     * Resume the progress polling when the page shows the installation.
     *
     * A page loaded while the installation is running, after a reload for
     * example, must resume the polling to reach the completed page.
     *
     * @returns {void}
     */
    #resumeProgressPolling() {
        if (document.getElementById('percent_progress') !== null) {
            this.#startProgressPolling();
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Attach click listeners to every button in the setup container.
     *
     * @returns {void}
     */
    attachSetupListeners() {
        const container = document.getElementById('main-content');
        if (!container) return;

        const buttons = container.querySelectorAll('button');
        buttons.forEach((btn) => {
            btn.addEventListener('click', (e) => this.#handleButtonClick(e.currentTarget));
        });
    }

    // ------------------------------------------------------------------------

    /**
     * Attach 'change' event listeners to every checkbox inside main container.
     * The listener only delegates handling to the dedicated method.
     *
     * @returns {void}
     */
    attachCheckboxListeners() {
        const container = document.getElementById('main-content');
        if (!container) return;

        const checkboxes = container.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach((cb) => {
            cb.addEventListener('change', (e) => this._handleCheckboxChange(e.currentTarget));
        });
    }

    // ----------------------------------------------------------------------
    // Checkboxes
    // ----------------------------------------------------------------------

    /**
     * Handle a checkbox change event.
     * Builds the POST payload and delegates the update to the server call.
     *
     * @param {HTMLInputElement} checkable - The toggled checkbox.
     * @returns {void}
     */
    _handleCheckboxChange(checkable) {
        const postData = {};
        // postData[`${checkable.name}_posted`] = checkable.value;
        postData["check_name"] = checkable.name;
        this._sendCheckboxUpdate(postData);
    }

    // ----------------------------------------------------------------------

    /**
     * Send the updated checkbox state to the server and refresh UI accordingly.
     *
     * @async
     * @param {Object} postData - Key/value pairs of data to send.
     * @returns {Promise<void>}
     */
    async _sendCheckboxUpdate(postData) {
        try {
            const response = await this._requestManager.sendPostRequest(
                postData,
                'application/json',
                this._uri
            );

            // Update every checkbox concerned by the server's response
            for (const key in response) {
                const el = document.getElementById(key);
                if (el && 'checked' in el) el.checked = response[key];
            }
        } catch (error) {
            WexaLogger.error(`Checkbox update failed: ${error}`);
        }
    }

    // ----------------------------------------------------------------------
    // Buttons event dispatch
    // ----------------------------------------------------------------------

    /**
     * Central handler for all setup buttons.
     *
     * @param {HTMLElement} btn - The clicked button element.
     * @returns {void}
     */
    #handleButtonClick(btn) {
        WexaLogger.debug(`handle button click: ${btn.id}`);
        switch (btn.id) {
            case 'next_btn':
            case 'install_btn':
                this.#browseFieldset('next_fieldset', btn.getAttribute('value'));
                break;
            case 'prev_btn':
                this.#browseFieldset('prev_fieldset', btn.getAttribute('value'));
                break;
            case 'redo_btn':
                this.#submitResetForm();
                break;
            case 'cancel_btn':
                const target = window.Wexa.accessibility.setUrlWithParameters('/');
                window.location.href = target;
                break;
            case 'exit_btn':
                this.#submitExitForm();
                break;
            default:
                WexaLogger.debug(`Unhandled button: ${btn.id}`);
        }
    }

    // ----------------------------------------------------------------------
    // Actions
    // ----------------------------------------------------------------------

    /**
     * Navigate between fieldsets (previous or next).
     *
     * @async
     * @param {string} eventName - The event identifier ("next_fieldset" or "prev_fieldset").
     * @param {string} eventValue - The value associated with the event (usually the button value).
     * @returns {Promise<void>}
     */
    async #browseFieldset(eventName, eventValue) {
        const events = {event_name: eventName, event_value: eventValue};
        WexaLogger.debug(eventName)
        WexaLogger.debug(eventValue)
        const response = await this.postEvents(events);
        let start_progress = false;

        if (response) {
            if (typeof response !== 'object') {
                WexaLogger.error(`Invalid response: ${JSON.stringify(response)}`);
                const msg = 'Invalid response from server. Please retry.';
                this._showActionResult(msg, '', false);
            } else {
                this._hideDialog("error_dialog")
                this._hideDialog("info_dialog")
                for (const [id, html] of Object.entries(response)) {
                    WexaLogger.debug(` - Update HTML content of: ${id}`);
                    const old = document.getElementById(id);
                    if (old) old.outerHTML = html;

                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    if (doc.getElementById('install_field') !== null) {
                        start_progress = true;
                    }
                }
                this.attachSetupListeners();
                this.attachCheckboxListeners();
            }
        }
        if (start_progress) {
            this.#startProgressPolling();
        }
    }

    // ----------------------------------------------------------------------

    /**
     * Trigger a reset by submitting a hidden POST form.
     *
     * This method allows the browser to perform a full HTTP POST navigation
     * handled entirely by the server before it stops.
     *
     * @returns {void}
     */
    #submitResetForm() {
        this.submitForm('event_bake', 'reset');
    }

    // ----------------------------------------------------------------------

    /**
     * Trigger a clean exit by submitting a hidden POST form.
     *
     * This method allows the browser to perform a full HTTP POST navigation
     * handled entirely by the server before it stops.
     *
     * @returns {void}
     */
    #submitExitForm() {
        this.submitForm('event_bake', 'close');
    }

}
