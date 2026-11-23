const wexa_statics_js = window.WEXA_JS_PATH;
const { WexaLogger } = await import(`${wexa_statics_js}/logger.js`);
const { DialogManager } = await import(`${wexa_statics_js}/dialog.js`);
const { BaseManager } = await import(`${wexa_statics_js}/transport/base_manager.js`);
const dialogManager = new DialogManager();

const ID_ERROR_DIALOG = 'error_dialog';
const ID_FORM = 'annotate_form';
const ID_ANNOTATIONS_PANEL = 'annotate_annotations_panel';
const ID_OPTIONS_CONTAINER = 'options_container';
const EVENT_BAKE = 'event_bake';
const TASK_OPTIONS = 'annotate_options_';
const DATA_OPTIONS = 'options';
const DATA_VALUES = 'values';
const ID_SHOW_STATE = 'annotate_show_state';
const OPTIONS_VALIDATE = 'options_validate';

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
        this.#attachPanelToggle();

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

        // The forms of the service of the options, in the dialogs.
        const panel = document.getElementById(ID_ANNOTATIONS_PANEL);
        if (panel !== null) {
            panel.addEventListener('submit', (e) => this.#onOptionsSubmit(e));
        }

        const errorDlg = document.getElementById(ID_ERROR_DIALOG);
        if (errorDlg instanceof HTMLDialogElement && errorDlg.textContent.trim().length > 0) {
            dialogManager.open(ID_ERROR_DIALOG, true);
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Handle submit of the form of the page.
     *
     * The options of an annotation are asked for without leaving the page.
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

        const submitter = event.submitter;
        if (submitter !== null && submitter.name === EVENT_BAKE && submitter.value.startsWith(TASK_OPTIONS)) {
            event.preventDefault();
            this.#configure(submitter.value, this.#fieldsOf(form, submitter), false);
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
                button.removeAttribute('aria-disabled');
                button.removeAttribute('aria-describedby');
            } else {
                button.setAttribute('aria-disabled', 'true');
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
     * Handle submit of a form of the service of the options, in its dialog.
     *
     * It is sent with the fields of the form of the page, and with the task
     * of the annotation the dialog is the one of.
     *
     * @private
     * @param {SubmitEvent} event
     * @returns {void}
     */
    #onOptionsSubmit(event) {
        const dialog = event.target.closest('dialog');
        if (dialog === null || !dialog.id.startsWith(TASK_OPTIONS)) {
            return;
        }
        event.preventDefault();

        const fields = this.#fieldsOf(document.getElementById(ID_FORM), null);
        Object.assign(fields, this.#fieldsOf(event.target, event.submitter));
        fields[EVENT_BAKE] = dialog.id;

        // Applying the options confirms them: the dialog is closed once the
        // values are written in the page.
        const applied = (event.submitter !== null && event.submitter.name === OPTIONS_VALIDATE);
        this.#configure(dialog.id, fields, applied);
    }

    // ------------------------------------------------------------------------

    /**
     * Send a request of the options of an annotation, and put what the server wrote in the page.
     *
     * The container is placed in the dialog of the annotation, and the values
     * of its options are written in the hidden fields of the form of the page.
     *
     * @private
     * @param {string} task - The task, which is the identifier of the dialog.
     * @param {Object} fields - What is sent.
     * @param {boolean} close - Whether the dialog is closed once the values are written.
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
            WexaLogger.error(`AnnotateManager: the dialog ${task} was not found.`);
            return;
        }
        this.#placeOptions(dialog, answered[DATA_OPTIONS]);
        this.#writeValues(answered[DATA_VALUES]);
        if (close === true) {
            dialogManager.close(task);
        } else if (dialog.open === false) {
            dialogManager.open(task, true);
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Place the container of the options in a dialog.
     *
     * One container stands in the page: the one of the annotation which is
     * configured. The one of another annotation becomes an empty section.
     *
     * @private
     * @param {HTMLDialogElement} dialog - The dialog of the annotation.
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
     * Write values in the hidden fields of the form of the page.
     *
     * @private
     * @param {Object} values - One value per name of field.
     * @returns {void}
     */
    #writeValues(values) {
        const form = document.getElementById(ID_FORM);
        for (const name in values) {
            const field = form.querySelector(`input[name="${CSS.escape(name)}"]`);
            if (field !== null) {
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
