const wexa_statics_js = window.WEXA_JS_PATH;
const { WexaLogger } = await import(`${wexa_statics_js}/logger.js`);
const { BaseManager } = await import(`${wexa_statics_js}/transport/base_manager.js`);
const { SortaTable } = await import(`${wexa_statics_js}/extras/sortatable.js`);
const { ToggleSelector } = await import(`${wexa_statics_js}/toggleselect.js`);
const { ProgressBar } = await import(`${wexa_statics_js}/progressbar.js`);

/**
 * :filename: sppas.ui.swapp.statics.js.convert_manager.js
 * :author: Brigitte Bigi
 * :contact: contact@sppas.org
 * :summary: Controls the section of the conversion of the Convert application
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
// Class: ConvertManager. Controls the section of the conversion of convert.html
// --------------------------------------------------------------------------

const SECTION_ID = 'convert_section';
const ID_DESTINATION = 'convert_destination';
const FORM_ID = 'convert_form';
const ID_INFO_DIALOG = 'info_dialog';
const HIDDEN_CLASS = 'hidden';
const ID_COMPARE_OPEN = 'convert_compare_open';
const ID_COMPARE_DIALOG = 'convert_compare_dialog';
const ID_COMPARE_COLUMNS = 'convert_compare_columns';
const ID_COMPARE_APPLY = 'convert_compare_apply';
const ID_COMPARE_TABLE = 'convert_compare_table';
const EVENT_TASK = 'convert_task';
const EVENT_NAME = 'event_name';
const EVENT_BAKE = 'event_bake';
const TASK_UPDATE = 'update';
const TASK_COMPLETE = 'complete';
const TASK_RESET = 'reset';
const MAIN_ID = 'main-content';
const DATA_CONVERT = 'convert';
const DATA_CONTAINER = 'container';
const ID_PROGRESS = 'progress_section';
const DEPOSIT_CONTAINER_ID = 'files_deposit';
const INTERVAL_MS = 1000;

/**
 * This class shows, among what the server wrote, the part of the format chosen.
 *
 * The page is written by the server, with one block per format which loses
 * something: what reaching that format costs. One is shown, the one of the
 * format chosen if it has one, and the others are hidden. When a format is
 * chosen, and when the form of the conversion is reset, the block of the
 * format chosen is shown and the others are hidden. Nothing is created,
 * nothing is replaced, and nothing is sent.
 *
 * A task of the conversion is sent with the fields of the form, without
 * reloading the page. While the conversion runs, where it stands is asked at
 * regular intervals and shown by the progress bar; once it has ended, its
 * results are asked for, and what the server wrote replaces the section of
 * the conversion and the container of the provision of files, whose
 * listeners are attached again. Once started over, the page is back at its
 * top, and the focus is given to its main content, where the skip link leads.
 *
 * The formats are compared in a modal dialog, whose table sorts on its
 * columns and shows the columns chosen in its list.
 *
 * handleConvertManagerOnLoad() has to be invoked **after** the DOM is loaded.
 *
 */
export default class ConvertManager extends BaseManager {

    // ------------------------------------------------------------------------
    // Constructor
    // ------------------------------------------------------------------------

    #files;

    /**
     * @param {Object|null} swappFiles - The manager of the container of the provision of files.
     */
    constructor(swappFiles = null) {
        super();
        this.#files = swappFiles;
    }

    // ------------------------------------------------------------------------
    // Initialization
    // ------------------------------------------------------------------------

    /**
     * Register the event listeners once the DOM content is loaded.
     *
     * @returns {void}
     */
    handleConvertManagerOnLoad() {
        WexaLogger.debug('Attach Convert listeners');
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.#start());
        } else {
            this.#start();
        }
    }

    // ------------------------------------------------------------------------
    // Private
    // ------------------------------------------------------------------------

    /**
     * Listen to the section, and open the dialog of information if it was filled in.
     *
     * @returns {void}
     */
    #start() {
        this.#attachListeners();
        this.#attachCompare();

        const infoDlg = document.getElementById(ID_INFO_DIALOG);
        if (infoDlg instanceof HTMLDialogElement && infoDlg.textContent.trim().length > 0) {
            this._dialog.open(ID_INFO_DIALOG, true);
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Attach the listeners to the radio buttons of the formats and to the form.
     *
     * @returns {void}
     */
    #attachListeners() {
        const section = document.getElementById(SECTION_ID);
        if (section === null) {
            WexaLogger.error('ConvertManager: the section of the conversion was not found.');
            return;
        }

        const radios = section.querySelectorAll('input[type="radio"]');
        for (const radio of radios) {
            radio.addEventListener('change', () => this.#show(section, radio));
        }

        const form = document.getElementById(FORM_ID);
        if (form === null) {
            WexaLogger.error('ConvertManager: the form of the conversion was not found.');
            return;
        }
        // The fields are put back after the event: the format checked is read then.
        form.addEventListener('reset', () => setTimeout(() => this.#showChecked(section), 0));
        // A task of the conversion is sent without reloading the page.
        section.addEventListener('submit', (event) => this.#onSubmitted(event));
    }

    // ------------------------------------------------------------------------

    /**
     * Attach the dialog which compares the formats: its opening, its sort, its columns.
     *
     * @returns {void}
     */
    #attachCompare() {
        const open = document.getElementById(ID_COMPARE_OPEN);
        if (open === null) {
            WexaLogger.error('ConvertManager: the button which compares the formats was not found.');
            return;
        }
        open.addEventListener('click', () => this._dialog.open(ID_COMPARE_DIALOG, true));

        // Closed by Escape too: the dialog is hidden again, and the focus goes
        // back to the button which opened it.
        const dialog = document.getElementById(ID_COMPARE_DIALOG);
        dialog.addEventListener('close', () => {
            this._dialog.close(ID_COMPARE_DIALOG);
            open.focus();
        });

        const sortatable = new SortaTable(ID_COMPARE_TABLE);
        sortatable.attachSortListeners();

        const toggleSelector = new ToggleSelector(ID_COMPARE_COLUMNS);
        const details = document.getElementById(ID_COMPARE_COLUMNS);
        const toggle = details.querySelector('summary button[data-toggle]');
        toggle.addEventListener('click', (event) => toggleSelector.toggleSelection(event));
        toggle.addEventListener('keydown', (event) => toggleSelector.toggleSelection(event));

        const apply = document.getElementById(ID_COMPARE_APPLY);
        apply.addEventListener('click', () => sortatable.toggleColumnVisibility(toggleSelector.getCheckboxes()));
    }

    // ------------------------------------------------------------------------

    /**
     * Show the block of the format which is checked.
     *
     * @param {HTMLElement} section - The section of the conversion.
     * @returns {void}
     */
    #showChecked(section) {
        const checked = section.querySelector('input[type="radio"]:checked');
        if (checked === null) {
            WexaLogger.error('ConvertManager: no format is checked.');
            return;
        }
        this.#show(section, checked);
    }

    // ------------------------------------------------------------------------

    /**
     * Show the block a radio button controls, and hide the others.
     *
     * A format which loses nothing controls no block: none is shown.
     *
     * @param {HTMLElement} section - The section of the conversion.
     * @param {HTMLInputElement} radio - The radio button of a format.
     * @returns {void}
     */
    #show(section, radio) {
        const column = document.getElementById(ID_DESTINATION);
        if (column === null) {
            WexaLogger.error('ConvertManager: the column of the destination was not found.');
            return;
        }
        for (const one of column.children) {
            one.classList.add(HIDDEN_CLASS);
        }
        if (radio.hasAttribute('aria-controls') === false) {
            return;
        }
        const block = document.getElementById(radio.getAttribute('aria-controls'));
        if (block === null) {
            WexaLogger.error(`ConvertManager: the block of ${radio.value} was not found.`);
            return;
        }
        block.classList.remove(HIDDEN_CLASS);
    }

    // ------------------------------------------------------------------------

    /**
     * Send a task of the conversion with the fields of its form.
     *
     * @param {SubmitEvent} event - The submission of a form of the section.
     * @returns {Promise<void>}
     */
    async #onSubmitted(event) {
        const submitter = event.submitter;
        if (submitter === null || submitter.name !== EVENT_TASK) {
            return;
        }
        event.preventDefault();
        const replaced = await this.#post(this.#fieldsOf(event.target, submitter));
        if (replaced === true && submitter.value === TASK_RESET) {
            this.#backToTop();
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Bring the page back to its top, and give the focus to its main content.
     *
     * The button which was used is replaced: its focus would be lost.
     *
     * @returns {void}
     */
    #backToTop() {
        window.scrollTo(0, 0);
        const main = document.getElementById(MAIN_ID);
        if (main === null) {
            WexaLogger.error('ConvertManager: the main content was not found.');
            return;
        }
        main.setAttribute('tabindex', '-1');
        main.focus({ preventScroll: true });
    }

    // ------------------------------------------------------------------------

    /**
     * Return the fields a form transmits, those which belong to it by their attribute included.
     *
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
     * Send the fields, put in the page what the server wrote, and follow a conversion which runs.
     *
     * @param {Object} fields - What is sent.
     * @returns {Promise<boolean>} Whether what the server wrote was put in the page.
     */
    async #post(fields) {
        // Nothing is given back when the server said something: it was shown.
        const answered = await this.postEvents(fields);
        if (answered === null || answered === undefined) {
            return false;
        }
        this.#replace(answered);
        if (document.getElementById(ID_PROGRESS) !== null) {
            this.#follow();
        }
        return true;
    }

    // ------------------------------------------------------------------------

    /**
     * Put in the page the section and the container the server wrote.
     *
     * @param {Object} answered - What the server answered.
     * @returns {void}
     */
    /**
     * Place the icons of what the server wrote, as the ones of the page were.
     *
     * The replaced node is out of the document: the new one is asked for
     * again, by the identifier it carries.
     *
     * @param {string} id - Identifier of what has just been replaced.
     * @returns {void}
     */
    #placeIcons(id) {
        const fresh = document.getElementById(id);
        if (fresh !== null && window.Wexa && window.Wexa.icons) {
            window.Wexa.icons.run(fresh);
        }
    }

    // -----------------------------------------------------------------------

    #replace(answered) {
        if (DATA_CONVERT in answered) {
            const section = document.getElementById(SECTION_ID);
            if (section !== null) {
                section.outerHTML = answered[DATA_CONVERT];
                this.#placeIcons(SECTION_ID);
            }
        }
        if (DATA_CONTAINER in answered) {
            const container = document.getElementById(DEPOSIT_CONTAINER_ID);
            if (container !== null) {
                container.outerHTML = answered[DATA_CONTAINER];
                this.#placeIcons(DEPOSIT_CONTAINER_ID);
            }
            if (this.#files !== null) {
                this.#files.handleSwappFilesOnLoad();
            }
        }
        // The icons of what the server wrote are placed, as the ones of the page were.
        if (window.Wexa && window.Wexa.icons) {
            for (const id of [SECTION_ID, DEPOSIT_CONTAINER_ID]) {
                const written = document.getElementById(id);
                if (written !== null) {
                    window.Wexa.icons.run(written);
                }
            }
        }
        this.#attachListeners();
        this.#attachCompare();
    }

    // ------------------------------------------------------------------------

    /**
     * Ask where the conversion stands until it has ended, then ask for its results.
     *
     * The progress bar of Whakerexa is used in its managed mode: the page asks
     * where the conversion stands, with the name of its report, at each refresh.
     *
     * @returns {void}
     */
    #follow() {
        const form = document.getElementById(FORM_ID);
        if (form === null) {
            WexaLogger.error('ConvertManager: the form of the conversion was not found.');
            return;
        }
        const updated = this.#fieldsOf(form, null);
        updated[EVENT_NAME] = TASK_UPDATE;
        const completed = this.#fieldsOf(form, null);
        completed[EVENT_BAKE] = TASK_COMPLETE;
        const progressBar = new ProgressBar({
            // Nothing given back is said as null: the bar then asks for the results.
            updateCallback: async () => (await this.postEvents(updated)) ?? null,
            completeCallback: async () => await this.#post(completed),
            intervalMs: INTERVAL_MS
        });
        progressBar.start();
    }
}
