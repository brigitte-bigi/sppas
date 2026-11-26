/**
 * :filename: sppas.ui.swapp.statics.js.sppas.js
 * :author: Brigitte Bigi
 * :contact: contact@sppas.org
 * :summary: JS for any SPPAS web application
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
 *     Copyright (C) 2011-2025  Brigitte Bigi, CNRS
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

import SetupManager from './setup_manager.js';
import DashboardManager from './dashboard_manager.js';
import FeedbackManager from './feedback_manager.js';
import TraceManager from './trace_manager.js';
import ConvertManager from './convert_manager.js';
import AnnotateManager from './annotate_manager.js';
import PluginsManager from './plugins_manager.js';

const wexa_statics_js = window.WEXA_JS_PATH;
const { WexaLogger } = await import(`${wexa_statics_js}/logger.js`);
const { DialogManager } = await import(`${wexa_statics_js}/dialog.js`);
const { BaseManager } = await import(`${wexa_statics_js}/transport/base_manager.js`);
const dialogManager = new DialogManager();

const EVENT_BAKE = 'event_bake';
const ID_OPTIONS_CONTAINER = 'options_container';
const OPTIONS_VALIDATE = 'options_validate';
const OPTIONS_CLOSE = 'options_close';
const DATA_OPTIONS = 'options';
const DATA_VALUES = 'values';

// --------------------------------------------------------------------------
// Class: SwappOptions. The windows of the options, an extra of the service
// of the options.
// --------------------------------------------------------------------------

/**
 * The windows of the options of a page, which the service of the options
 * offers the apps.
 *
 * What sets the options of a thing is a button of the form of the app,
 * whose value is the task of that thing and the identifier of its window.
 * The options are asked for without leaving the page: the container of the
 * service is placed in the window, and what the server answers of that thing
 * is written in the form of the app, which carries it from one request to
 * the next. Applying the options closes the window; closing it without
 * applying them is said to the server.
 *
 * handleSwappOptionsOnLoad() has to be invoked **after** the DOM is loaded,
 * and before the manager of the app attaches its own listeners.
 */
class SwappOptions extends BaseManager {

    /**
     * The identifier of the form of the app.
     * @type {string}
     */
    #formId;

    /**
     * What the task of the options of a thing starts with, and the identifier of its window.
     * @type {string}
     */
    #prefix;

    /**
     * The identifier of the window which is closed because its options were applied, null if none.
     * @type {string|null}
     */
    #closedByApply;

    // ------------------------------------------------------------------------
    // Constructor
    // ------------------------------------------------------------------------

    /**
     * @param {string} formId - The identifier of the form of the app.
     * @param {string} prefix - What the task of the options of a thing starts with.
     */
    constructor(formId, prefix) {
        super();
        this.#formId = formId;
        this.#prefix = prefix;
        this.#closedByApply = null;
    }

    // ------------------------------------------------------------------------
    // Initialization
    // ------------------------------------------------------------------------

    /**
     * Attach the listeners of the form of the app and of the windows of the options.
     *
     * @returns {void}
     */
    handleSwappOptionsOnLoad() {
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
     * Attach the listeners of the form of the app, and of the windows of the options.
     *
     * @private
     * @returns {void}
     */
    #attach() {
        const form = document.getElementById(this.#formId);
        if (form instanceof HTMLFormElement) {
            form.addEventListener('submit', (e) => this.#onFormSubmit(e));
        }

        // The forms of the container, in the windows, and the windows
        // however they are closed.
        document.querySelectorAll(`dialog[id^="${this.#prefix}"]`).forEach((dialog) => {
            dialog.addEventListener('submit', (e) => this.#onOptionsSubmit(e, dialog));
            dialog.addEventListener('close', () => this.#onOptionsClose(dialog));
        });
    }

    // ------------------------------------------------------------------------

    /**
     * Handle submit of the form of the app: the options of a thing are asked for without leaving the page.
     *
     * @private
     * @param {SubmitEvent} event
     * @returns {void}
     */
    #onFormSubmit(event) {
        const submitter = event.submitter;
        if (submitter === null || submitter.name !== EVENT_BAKE || !submitter.value.startsWith(this.#prefix)) {
            return;
        }
        event.preventDefault();
        this.#configure(submitter.value, this.#fieldsOf(event.currentTarget, submitter), false);
    }

    // ------------------------------------------------------------------------

    /**
     * Handle submit of a form of the container, in its window.
     *
     * It is sent with the fields of the form of the app, and with the task of
     * the thing the window is the one of.
     *
     * @private
     * @param {SubmitEvent} event
     * @param {HTMLDialogElement} dialog - The window.
     * @returns {void}
     */
    #onOptionsSubmit(event, dialog) {
        if (!(event.target instanceof HTMLFormElement) || event.target.closest('#' + ID_OPTIONS_CONTAINER) === null) {
            return;
        }
        event.preventDefault();

        const fields = this.#fieldsOf(document.getElementById(this.#formId), null);
        Object.assign(fields, this.#fieldsOf(event.target, event.submitter));
        fields[EVENT_BAKE] = dialog.id;

        // Applying the options closes the window once what the server
        // answered is written in the page.
        const applied = (event.submitter !== null && event.submitter.name === OPTIONS_VALIDATE);
        this.#configure(dialog.id, fields, applied);
    }

    // ------------------------------------------------------------------------

    /**
     * Handle the closing of a window: closed without its options being applied, it is said to the server.
     *
     * What the server answers of that thing is written in the form of the app.
     *
     * @private
     * @param {HTMLDialogElement} dialog - The window.
     * @returns {Promise<void>}
     */
    async #onOptionsClose(dialog) {
        if (this.#closedByApply === dialog.id) {
            this.#closedByApply = null;
            return;
        }

        const fields = this.#fieldsOf(document.getElementById(this.#formId), null);
        fields[EVENT_BAKE] = dialog.id;
        fields[OPTIONS_CLOSE] = '';
        const answered = await this.postEvents(fields);
        if (answered === null || answered === undefined || !(DATA_VALUES in answered)) {
            return;
        }
        this.#writeValues(answered[DATA_VALUES]);
    }

    // ------------------------------------------------------------------------

    /**
     * Send a request of the options of a thing, and put what the server wrote in the page.
     *
     * The container is placed in the window of that thing, and what the
     * server answers of it is written in the form of the app.
     *
     * @private
     * @param {string} task - The task, which is the identifier of the window.
     * @param {Object} fields - What is sent.
     * @param {boolean} close - Whether the window is closed once the values are written.
     * @returns {Promise<void>}
     */
    async #configure(task, fields, close) {
        // Nothing is given back when the server said something: it was shown.
        const answered = await this.postEvents(fields);
        if (answered === null || answered === undefined || !(DATA_OPTIONS in answered)) {
            return;
        }

        const dialog = document.getElementById(task);
        if (!(dialog instanceof HTMLDialogElement)) {
            WexaLogger.error(`SwappOptions: the window ${task} was not found.`);
            return;
        }
        this.#placeOptions(dialog, answered[DATA_OPTIONS]);
        this.#writeValues(answered[DATA_VALUES]);
        if (close === true) {
            this.#closedByApply = task;
            dialogManager.close(task);
        } else if (dialog.open === false) {
            dialogManager.open(task, true);
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Place the container of the options in a window.
     *
     * One container stands in the page: the one of the thing whose options
     * are asked for. The one of another thing becomes an empty section.
     *
     * @private
     * @param {HTMLDialogElement} dialog - The window of the thing.
     * @param {string} container - The container, in HTML.
     * @returns {void}
     */
    #placeOptions(dialog, container) {
        const former = document.getElementById(ID_OPTIONS_CONTAINER);
        if (former !== null && dialog.contains(former) === false) {
            former.replaceChildren();
            former.removeAttribute('id');
        }

        dialog.querySelector('section').outerHTML = container;
        const fresh = document.getElementById(ID_OPTIONS_CONTAINER);
        if (fresh !== null && window.Wexa && window.Wexa.icons) {
            window.Wexa.icons.run(fresh);
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Write values in the fields of the form of the app.
     *
     * A checkbox, which belongs to the form by its attribute, is checked when
     * its value is "True", and says that it changed; another field takes the
     * value.
     *
     * @private
     * @param {Object} values - One value per name of field.
     * @returns {void}
     */
    #writeValues(values) {
        const form = document.getElementById(this.#formId);
        for (const name in values) {
            const field = form.elements.namedItem(name);
            if (field instanceof HTMLInputElement && field.type === 'checkbox') {
                const checked = (values[name] === 'True');
                if (field.checked !== checked) {
                    field.checked = checked;
                    field.dispatchEvent(new Event('change', { bubbles: true }));
                }
            } else if (field instanceof HTMLInputElement) {
                field.value = values[name];
            }
        }
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

}

export { SetupManager, DashboardManager, FeedbackManager, TraceManager, ConvertManager, AnnotateManager, PluginsManager, SwappOptions };
