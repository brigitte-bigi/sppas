const wexa_statics_js = window.WEXA_JS_PATH;
const { WexaLogger } = await import(`${wexa_statics_js}/logger.js`);
const { DialogManager } = await import(`${wexa_statics_js}/dialog.js`);
const { BaseManager } = await import(`${wexa_statics_js}/transport/base_manager.js`);
import SwappProcess from './swapp_process.js';
const dialogManager = new DialogManager();

const ID_ERROR_DIALOG = 'error_dialog';
const ID_INFO_DIALOG = 'info_dialog';
const ID_PROGRESS = 'percent_progress';
const ID_LOG_TITLE = 'annotate_log_h';
const EVENT_NAME = 'event_name';
const TASK_PERFORM = 'annotate_perform';
const TASK_COMPLETE = 'annotate_complete';
const TASK_REPORT = 'annotate_report';
const ID_REPORT = 'annotate_report';
const FIELD_FOLLOWED = 'annotate_followed';
const ID_FORM = 'annotate_form';
const PROCESS_FIELD = 'swapp_process';
const ID_FILES_PANEL = 'annotate_files_panel';
const EVENT_BAKE = 'event_bake';
const ID_SHOW_STATE = 'annotate_show_state';

/**
 * :filename: sppas.ui.swapp.statics.js.annotate_manager.js
 * :author: Brigitte Bigi
 * :contact: contact@sppas.org
 * :summary: JS for the page annotate.html
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

/**
 * This class drives the toggle choosing which panel is shown beside the
 * other: the six steps, the reports, or both.
 *
 * The toggle is a native radiogroup (see Whakerexa's togglegroup.css):
 * keyboard operation and the checked/unchecked announcement come from the
 * radio inputs themselves. Hiding a panel with the "hidden" class removes
 * it from the accessibility tree, exactly like showing it restores it --
 * nothing extra is needed for assistive technologies.
 *
 * handleAnnotateManagerOnLoad() has to be invoked **after** the DOM is loaded.
 *
 */
export default class AnnotateManager extends BaseManager {

    // ------------------------------------------------------------------------
    // Constructor
    // ------------------------------------------------------------------------

    #files;

    #intervalMs;

    /**
     * @param {Object|null} swappFiles - The manager of the container of the provision of files.
     * @param {number} intervalMs - How often the page asks where a run stands, in milliseconds.
     */
    constructor(swappFiles = null, intervalMs) {
        super();
        this.#files = swappFiles;
        this.#intervalMs = intervalMs;
    }

    // ------------------------------------------------------------------------
    // Initialization
    // ------------------------------------------------------------------------

    /**
     * Start the panel toggle once the DOM is loaded.
     *
     * This method must be called after the page structure is available.
     *
     * @returns {void}
     */
    handleAnnotateManagerOnLoad() {
        WexaLogger.debug('Start the annotate panel toggle');
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.#onLoad());
        } else {
            this.#onLoad();
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Attach the panel toggle listeners, and open the dialog of the errors
     * when the server wrote something in it.
     *
     * @private
     * @returns {void}
     */
    #onLoad() {
        this.#attach();
        this.#say();

        // A page asked for while a run goes follows it.
        if (document.getElementById(ID_PROGRESS) !== null) {
            this.#follow();
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Attach the listeners to what the server wrote in the main content of the page.
     *
     * @private
     * @returns {void}
     */
    #attach() {
        this.#attachPanelToggle();

        // The report of the run, folded under the progress, is asked for as
        // soon as it is unfolded.
        const report = document.getElementById(ID_REPORT);
        if (report !== null && report.parentElement instanceof HTMLDetailsElement) {
            report.parentElement.addEventListener('toggle', () => this.#askReport());
        }

        // Checking a report makes no request: the button which shows it is
        // offered in the page, or disabled when no report is checked.
        const reports = document.querySelectorAll('input[name="annotate_report"]');
        reports.forEach((radio) => {
            radio.addEventListener('change', () => this.#updateShow());
        });

        const form = document.getElementById(ID_FORM);
        if (form instanceof HTMLFormElement) {
            form.addEventListener('submit', (e) => this.#onFormSubmit(e));
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Open the dialog of the errors, then the one of the information, when the server wrote in it.
     *
     * @private
     * @returns {void}
     */
    #say() {
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
     * Send the request which performs the annotations, put in the page what the server wrote, and follow the run.
     *
     * @private
     * @param {Object} fields - What is sent.
     * @returns {Promise<void>}
     */
    async #perform(fields) {
        await this.#post(fields);
        if (document.getElementById(ID_PROGRESS) !== null) {
            this.#follow();
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Ask where the run stands until it has ended, then ask for its results.
     *
     * The run is a process of swapp: it is followed as every process is, by
     * the name the form transmits. At each refresh, the report is asked for
     * as it is written, when it is unfolded.
     *
     * @private
     * @returns {void}
     */
    #follow() {
        const form = document.getElementById(ID_FORM);
        if (!(form instanceof HTMLFormElement)) {
            WexaLogger.error('AnnotateManager: the form of the page was not found.');
            return;
        }
        const process = form.elements.namedItem(PROCESS_FIELD);
        if (process === null) {
            WexaLogger.error('AnnotateManager: the name of the process of the run was not found.');
            return;
        }
        new SwappProcess(this.#intervalMs).follow(process.value,
                                                  async () => await this.#complete(),
                                                  async () => await this.#askReport());
    }

    // ------------------------------------------------------------------------

    /**
     * Ask for the report of the run the page follows, when it is unfolded, and put it in place of the one shown.
     *
     * @private
     * @returns {Promise<void>}
     */
    async #askReport() {
        const report = document.getElementById(ID_REPORT);
        if (report === null || !(report.parentElement instanceof HTMLDetailsElement) || report.parentElement.open === false) {
            return;
        }
        const form = document.getElementById(ID_FORM);
        const fields = {};
        fields[EVENT_NAME] = TASK_REPORT;
        fields[FIELD_FOLLOWED] = form.elements.namedItem(FIELD_FOLLOWED).value;

        const answered = await this.postEvents(fields);
        if (answered === null || answered === undefined || !(ID_REPORT in answered)) {
            return;
        }
        const shown = document.getElementById(ID_REPORT);
        if (shown !== null) {
            shown.outerHTML = answered[ID_REPORT];
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Ask for the results of the run, with the fields of the form of the page.
     *
     * @private
     * @returns {Promise<void>}
     */
    async #complete() {
        const fields = this.#fieldsOf(document.getElementById(ID_FORM), null);
        fields[EVENT_BAKE] = TASK_COMPLETE;
        await this.#post(fields);
    }

    // ------------------------------------------------------------------------

    /**
     * Send the fields, and put in the page what the server wrote, by identifier.
     *
     * The panel which arrives takes the focus by its title.
     *
     * @private
     * @param {Object} fields - What is sent.
     * @returns {Promise<void>}
     */
    async #post(fields) {
        // Nothing is given back when the server said something: it was shown.
        const answered = await this.postEvents(fields);
        if (answered === null || answered === undefined) {
            return;
        }

        for (const [id, html] of Object.entries(answered)) {
            const former = document.getElementById(id);
            if (former === null) {
                continue;
            }
            former.outerHTML = html;
            const fresh = document.getElementById(id);
            if (fresh !== null && window.Wexa && window.Wexa.icons) {
                window.Wexa.icons.run(fresh);
            }
        }

        // The container of the provision of files stands in the panel of the
        // files only: its listeners are attached again when it is written.
        if (this.#files !== null && document.getElementById(ID_FILES_PANEL) !== null) {
            this.#files.handleSwappFilesOnLoad();
        }

        this.#attach();
        this.#say();
        const title = document.getElementById(ID_LOG_TITLE);
        if (title !== null) {
            title.setAttribute('tabindex', '-1');
            title.focus();
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Handle submit of the form of the page.
     *
     * The options of an annotation are asked for by the service of the
     * options, which attached its listener first: what it answered is left
     * to it. Otherwise, add the accessibility parameters (theme, contrast...)
     * to the address the form is sent to.
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

        const submitter = event.submitter;

        // The annotations are performed without reloading the page, and the
        // run is followed.
        if (submitter !== null && submitter.name === EVENT_BAKE && submitter.value === TASK_PERFORM) {
            event.preventDefault();
            this.#perform(this.#fieldsOf(form, submitter));
            return;
        }

        form.action = window.Wexa.accessibility.setUrlWithParameters(form.action);
    }

    // ------------------------------------------------------------------------

    /**
     * Offer the button which shows the checked report when one is checked, and disable it otherwise.
     *
     * What says no report is checked is hidden when one is, and shown otherwise.
     *
     * @private
     * @returns {void}
     */
    #updateShow() {
        const checked = document.querySelector('input[name="annotate_report"]:checked') !== null;

        const button = document.querySelector(`button[name="${EVENT_BAKE}"][value="annotate_show"]`);
        if (button !== null) {
            if (checked === true) {
                button.disabled = false;
                button.removeAttribute('aria-describedby');
            } else {
                button.disabled = true;
                button.setAttribute('aria-describedby', ID_SHOW_STATE);
            }
        }

        const state = document.getElementById(ID_SHOW_STATE);
        if (state !== null) {
            state.classList.toggle('hidden', checked);
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

    // ------------------------------------------------------------------------

    /**
     * Attach the change listener of the panel-view toggle, if baked.
     *
     * @private
     * @returns {void}
     */
    #attachPanelToggle() {
        const radios = document.querySelectorAll('input[name="annotate_panel_view"]');
        radios.forEach((radio) => {
            radio.addEventListener('change', () => this.#applyPanelView(radio.value));
        });
    }

    // ------------------------------------------------------------------------

    /**
     * Show the requested panel(s), hiding the other one with the "hidden"
     * class.
     *
     * "width_70" and "width_30" are fixed widths: a panel left alone does
     * not grow to fill the row on its own, so its width class is switched
     * too.
     *
     * @private
     * @param {string} view - One of "left", "both", "right".
     * @returns {void}
     */
    #applyPanelView(view) {
        const stepsPanel = document.getElementById('annotate_actions_panel');
        const reportsPanel = document.getElementById('annotate_reports_panel');
        if (stepsPanel === null || reportsPanel === null) {
            return;
        }

        stepsPanel.classList.toggle('hidden', view === 'right');
        reportsPanel.classList.toggle('hidden', view === 'left');

        const stepsAlone = view === 'left';
        stepsPanel.classList.toggle('width_70', !stepsAlone);
        stepsPanel.classList.toggle('width_full', stepsAlone);

        const reportsAlone = view === 'right';
        reportsPanel.classList.toggle('width_30', !reportsAlone);
        reportsPanel.classList.toggle('width_full', reportsAlone);
    }
}
