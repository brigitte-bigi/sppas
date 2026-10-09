const wexa_statics_js = window.WEXA_JS_PATH;
const { WexaLogger } = await import(`${wexa_statics_js}/logger.js`);
const { BaseManager } = await import(`${wexa_statics_js}/transport/base_manager.js`);

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
const FIELD_TASK = 'convert_task';
const FIELD_DESTINATION = 'destination';
const FIELD_CONVERT = 'convert';
const TASK_DESTINATION = 'destination';
const TASK_GENERAL = 'general';
const GENERAL_OPTIONS = ['override', 'heuristic'];
const FILES_ANSWERED = 'swappfiles:answered';

/**
 * This class sends the decisions of a person, and shows what the server answers.
 *
 * The section of the conversion is built by the server, which is the only one
 * knowing what a format holds. Choosing a format or setting a general
 * option posts the task with everything decided so far, and the
 * section the server answers replaces the one which was shown: the page is not
 * reloaded. Running the conversion and starting a new one are plain posts of
 * the form, because their answer changes the container of the provision of
 * files as well.
 *
 * The container of the provision of files has its own manager. When it is
 * answered, the section of the conversion is replaced by the one which came
 * with it: what is still missing may have changed.
 *
 * handleConvertManagerOnLoad() has to be invoked **after** the DOM is loaded.
 *
 */
export default class ConvertManager extends BaseManager {

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
     * Listen to the answers of the provision of files, and to the section.
     *
     * @returns {void}
     */
    #start() {
        document.addEventListener(FILES_ANSWERED, (event) => this.#replaceSection(event.detail));
        this.#attachListeners();
    }

    // ------------------------------------------------------------------------

    /**
     * Attach the listeners to the radio buttons of the formats and to the general options.
     *
     * @returns {void}
     */
    #attachListeners() {
        const section = document.getElementById(SECTION_ID);
        if (section === null) {
            WexaLogger.error('ConvertManager: the section of the conversion was not found.');
            return;
        }

        const formatRadios = section.querySelectorAll(`input[type="radio"][name="${FIELD_DESTINATION}"]`);
        for (const radio of formatRadios) {
            radio.addEventListener('change', () => this.#postTask(TASK_DESTINATION, radio.value));
        }

        for (const name of GENERAL_OPTIONS) {
            const box = section.querySelector(`input[name="${name}"]`);
            if (box === null) {
                WexaLogger.error(`ConvertManager: the general option ${name} was not found.`);
                continue;
            }
            box.addEventListener('change', () => this.#postTask(TASK_GENERAL, this.#destination(section)));
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Return the destination the section carries.
     *
     * @param {HTMLElement} section - The section of the conversion.
     * @returns {string} The extension of the destination, empty if none.
     */
    #destination(section) {
        const field = section.querySelector(`input[type="hidden"][name="${FIELD_DESTINATION}"]`);
        if (field === null) {
            WexaLogger.error('ConvertManager: the field of the destination was not found.');
            return '';
        }
        return field.value;
    }

    // ------------------------------------------------------------------------

    /**
     * Post one task with everything decided so far, and show the answer.
     *
     * @param {string} task - The task to be done.
     * @param {string} destination - The extension of the destination, empty if none.
     * @returns {Promise<void>}
     */
    async #postTask(task, destination) {
        const section = document.getElementById(SECTION_ID);
        if (section === null) {
            WexaLogger.error('ConvertManager: the section of the conversion was not found.');
            return;
        }

        const events = {};
        events[FIELD_TASK] = task;
        events[FIELD_DESTINATION] = destination;
        for (const name of GENERAL_OPTIONS) {
            events[name] = 'False';
            const box = section.querySelector(`input[name="${name}"]`);
            if (box !== null && box.checked === true) {
                events[name] = 'True';
            }
        }

        const answered = await this.postEvents(events);
        if (answered === undefined) {
            return;
        }
        this.#replaceSection(answered);
    }

    // ------------------------------------------------------------------------

    /**
     * Replace the section of the conversion by the one the server answered.
     *
     * @param {Object} answered - What the server answered.
     * @returns {void}
     */
    #replaceSection(answered) {
        if (answered === null || answered === undefined) {
            WexaLogger.error('ConvertManager: the server answered nothing.');
            return;
        }
        if (FIELD_CONVERT in answered === false) {
            WexaLogger.error('ConvertManager: the answer holds no section of the conversion.');
            return;
        }

        const section = document.getElementById(SECTION_ID);
        if (section === null) {
            WexaLogger.error('ConvertManager: the section of the conversion was not found.');
            return;
        }
        section.outerHTML = answered[FIELD_CONVERT];
        this.#attachListeners();
    }
}
