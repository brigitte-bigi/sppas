const wexa_statics_js = window.WEXA_JS_PATH;
const { WexaLogger } = await import(`${wexa_statics_js}/logger.js`);
const { DialogManager } = await import(`${wexa_statics_js}/dialog.js`);
import SwappManager from './swapp_manager.js';
import SwappProcess from './swapp_process.js';
const dialogManager = new DialogManager();

const ID_FORM = 'plugins_form';
const ID_PLUGINS_SECTION = 'plugins_section';
const ID_WAITING = 'plugins_waiting';
const ID_RUN_SECTION = 'plugins_run_section';
const ID_PROGRESS = 'progress_section';
const ID_INFO_DIALOG = 'info_dialog';
const ID_ERROR_DIALOG = 'error_dialog';
const EVENT_BAKE = 'event_bake';
const TASK_RUN = 'plugins_run';
const TASK_COMPLETE = 'plugins_complete';
const TASK_INSTALL = 'plugins_install';
const FIELD_SELECTED = 'plugins_sel_';
const PROCESS_FIELD = 'swapp_process';
const ID_RUN_STATE = 'plugins_run_state';
const DATA_RUN = 'run';
const DATA_INFO = 'info';
const DATA_ERROR = 'error';
const DATA_PLUGINS = 'plugins';
const JSON_TYPE = 'application/json';

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
 * changes them. The runs are started without leaving the page, and they are
 * followed as every process of swapp is; once they are over, their results
 * are asked for with the form of the page. A plugin is installed without
 * leaving the page as well, and the section of the plugins the server
 * answers replaces the one of the page.
 *
 * handlePluginsManagerOnLoad() has to be invoked **after** the DOM is loaded,
 * and after the windows of the options are handled.
 */
export default class PluginsManager extends SwappManager {

    /**
     * How often the page asks where the runs stand, in milliseconds.
     * @type {number}
     */
    #intervalMs;

    // ------------------------------------------------------------------------
    // Constructor
    // ------------------------------------------------------------------------

    /**
     * @param {number} intervalMs - How often the page asks where the runs stand, in milliseconds.
     */
    constructor(intervalMs) {
        super();
        this.#intervalMs = intervalMs;
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
        this.#attachDialogs(document);
        this.#open();

        const form = document.getElementById(ID_FORM);
        if (form instanceof HTMLFormElement) {
            form.addEventListener('submit', (e) => this.#onFormSubmit(e));
        }

        this.#attachSwitches(document);

        // A page asked for while the runs go follows them.
        if (document.getElementById(ID_PROGRESS) !== null) {
            this.#follow();
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Have each button which opens a dialog open it, as a modal.
     *
     * @private
     * @param {Document|HTMLElement} root - What holds the buttons.
     * @returns {void}
     */
    #attachDialogs(root) {
        root.querySelectorAll('button[aria-haspopup="dialog"][aria-controls]').forEach((button) => {
            button.addEventListener('click', () => {
                dialogManager.open(button.getAttribute('aria-controls'), true);
            });
        });
    }

    // ------------------------------------------------------------------------

    /**
     * Have what starts the runs follow the switches of the plugins.
     *
     * @private
     * @param {Document|HTMLElement} root - What holds the switches.
     * @returns {void}
     */
    #attachSwitches(root) {
        root.querySelectorAll(`input[name^="${FIELD_SELECTED}"]`).forEach((input) => {
            input.addEventListener('change', () => this.#updateRun());
        });
    }

    // ------------------------------------------------------------------------

    /**
     * Open the dialog of the errors, then the one of the information, when the server wrote in it.
     *
     * @private
     * @returns {void}
     */
    #open() {
        for (const id of [ID_ERROR_DIALOG, ID_INFO_DIALOG]) {
            const dialog = document.getElementById(id);
            if (dialog instanceof HTMLDialogElement && dialog.textContent.trim().length > 0) {
                dialogManager.open(id, true);
                return;
            }
        }
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

        // The runs are started without leaving the page, and followed.
        const submitter = event.submitter;
        if (submitter !== null && submitter.name === EVENT_BAKE && submitter.value === TASK_RUN) {
            event.preventDefault();
            this.#post(this.#fieldsOf(form, submitter));
            return;
        }

        // A plugin is installed without leaving the page.
        if (submitter !== null && submitter.name === EVENT_BAKE && submitter.value === TASK_INSTALL) {
            event.preventDefault();
            this.#install(this.#fieldsOf(form, submitter), submitter);
            return;
        }

        form.action = window.Wexa.accessibility.setUrlWithParameters(form.action);
    }

    // ------------------------------------------------------------------------

    /**
     * Send the fields, put in the page what the server wrote, and follow the runs which go.
     *
     * @private
     * @param {Object} fields - What is sent.
     * @returns {Promise<void>}
     */
    async #post(fields) {
        // What the server said is shown by the page: postEvents() would
        // reload it instead, and what was said would be lost.
        const answered = await this._requestManager.sendPostRequest(fields, JSON_TYPE, this._uri);
        if (answered === null || answered === undefined) {
            WexaLogger.error('PluginsManager: the server answered nothing.');
            return;
        }
        // A request which failed is said in the dialog of the errors, as
        // the base manager says it.
        if (this._requestManager.status !== 200) {
            this._showActionResult(answered.error || '', '', false);
            return;
        }
        if (DATA_PLUGINS in answered) {
            this.#placePlugins(answered[DATA_PLUGINS]);
        }
        if (DATA_ERROR in answered) {
            this.#say(ID_ERROR_DIALOG, answered[DATA_ERROR]);
        } else if (DATA_INFO in answered) {
            this.#say(ID_INFO_DIALOG, answered[DATA_INFO]);
        }
        if (DATA_RUN in answered) {
            this.#placeRun(answered[DATA_RUN]);
            if (document.getElementById(ID_PROGRESS) !== null) {
                this.#follow();
            }
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Send the fields of the installation of a plugin, and say that the server waits for the archive.
     *
     * The server waits for what is chosen in the selection window: the page
     * says so until it answers, and the button which opens that window does
     * not answer meanwhile, so that only one window is opened. The answer
     * replaces the section of the plugins, with what said it and the button,
     * when a plugin was installed; when nothing replaced it, both are given
     * back as they were.
     *
     * @private
     * @param {Object} fields - What is sent.
     * @param {HTMLButtonElement} pressed - The button which installs.
     * @returns {Promise<void>}
     */
    async #install(fields, pressed) {
        const waiting = document.getElementById(ID_WAITING);
        if (waiting !== null) {
            waiting.hidden = false;
        }
        pressed.disabled = true;
        await this.#post(fields);
        if (waiting !== null) {
            waiting.hidden = true;
        }
        pressed.disabled = false;
    }

    // ------------------------------------------------------------------------

    /**
     * Write what the server said in a dialog, and open it.
     *
     * @private
     * @param {string} id - The identifier of the dialog: the one of the information, or the one of the errors.
     * @param {string} text - What the server said.
     * @returns {void}
     */
    #say(id, text) {
        const dialog = document.getElementById(id);
        if (!(dialog instanceof HTMLDialogElement)) {
            WexaLogger.error(`PluginsManager: the dialog ${id} was not found.`);
            return;
        }
        const p = document.createElement('p');
        p.textContent = text;
        dialog.replaceChildren(p);
        dialogManager.open(id, true);
    }

    // ------------------------------------------------------------------------

    /**
     * Place the section of the plugins the server wrote, in place of the one of the page.
     *
     * The buttons which open a dialog and the switches of the plugins of
     * that section are given their listeners, as the ones of the page were.
     *
     * @private
     * @param {string} section - The section, in HTML.
     * @returns {void}
     */
    #placePlugins(section) {
        const former = document.getElementById(ID_PLUGINS_SECTION);
        if (former === null) {
            WexaLogger.error('PluginsManager: the section of the plugins was not found.');
            return;
        }
        former.outerHTML = section;
        const fresh = document.getElementById(ID_PLUGINS_SECTION);
        if (fresh === null) {
            return;
        }
        if (window.Wexa && window.Wexa.icons) {
            window.Wexa.icons.run(fresh);
        }
        this.#attachDialogs(fresh);
        this.#attachSwitches(fresh);
    }

    // ------------------------------------------------------------------------

    /**
     * Place the section of the runs the server wrote: in place of the one of the page, or after the plugins.
     *
     * @private
     * @param {string} section - The section, in HTML.
     * @returns {void}
     */
    #placeRun(section) {
        const former = document.getElementById(ID_RUN_SECTION);
        if (former !== null) {
            former.outerHTML = section;
        } else {
            const plugins = document.getElementById(ID_PLUGINS_SECTION);
            if (plugins === null) {
                WexaLogger.error('PluginsManager: the section of the plugins was not found.');
                return;
            }
            plugins.insertAdjacentHTML('afterend', section);
        }
        const fresh = document.getElementById(ID_RUN_SECTION);
        if (fresh !== null && window.Wexa && window.Wexa.icons) {
            window.Wexa.icons.run(fresh);
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Ask where the runs stand until they have ended, then ask for their results.
     *
     * The runs are a process of swapp: they are followed as every process is,
     * by the name the form transmits. The results are asked for with the
     * fields of the form, the name of the report included.
     *
     * @private
     * @returns {void}
     */
    #follow() {
        const form = document.getElementById(ID_FORM);
        if (form === null) {
            WexaLogger.error('PluginsManager: the form of the page was not found.');
            return;
        }
        const process = form.elements.namedItem(PROCESS_FIELD);
        if (process === null) {
            WexaLogger.error('PluginsManager: the name of the process of the runs was not found.');
            return;
        }
        const completed = this.#fieldsOf(form, null);
        completed[EVENT_BAKE] = TASK_COMPLETE;
        new SwappProcess(this.#intervalMs).follow(process.value, async () => await this.#post(completed));
    }

    // ------------------------------------------------------------------------

    /**
     * Return the fields a form transmits, those which belong to it by their attribute included.
     *
     * @private
     * @param {HTMLFormElement} form - The form.
     * @param {HTMLElement|null} submitter - The button which sent it, if any.
     * @returns {Object} One entry per field.
     */
    #fieldsOf(form, submitter) {
        const fields = {};
        const data = (submitter === null) ? new FormData(form) : new FormData(form, submitter);
        for (const [name, value] of data) {
            fields[name] = value;
        }
        return fields;
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
