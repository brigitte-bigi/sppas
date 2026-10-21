const wexa_statics_js = window.WEXA_JS_PATH;
const { WexaLogger } = await import(`${wexa_statics_js}/logger.js`);
const { RequestManager } = await import(`${wexa_statics_js}/transport/request.js`);
const { DialogManager } = await import(`${wexa_statics_js}/dialog.js`);

/**
 * :filename: sppas.ui.swapp.statics.js.swapp_files.js
 * :author: Brigitte Bigi
 * :contact: contact@sppas.org
 * :summary: JS for the container of the provision of files
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
// Class: SwappFiles. Controls the container of the provision of files
// --------------------------------------------------------------------------

const DEPOSIT_CONTAINER_ID = 'files_deposit';
const FILES_INPUT_ID = 'files_input';
const DROPZONE_CLASS = 'dropzone';
const TASK_DESIGNATE = 'designate';
const TASK_SEND = 'send';
const FIELD_TASK = 'task';
const FIELD_NAME = 'name';
const FIELD_SIZE = 'size';
const FIELD_CONTENT = 'content';
const FIELD_CONTAINER = 'container';
const FIELD_INFO = 'info';
const ID_INFO_DIALOG = 'info_dialog';
const DRAGGED_OVER_CLASS = 'dragged-over';
const JSON_TYPE = 'application/json';

/**
 * This class carries what a person composes, and sends it when she asks.
 *
 * The container of the provision of files is built by the server, and this
 * class does two things the server cannot do alone: it reads the name and
 * the size of a file the person designates, and it sends the bytes when she
 * sends. Nothing of a content leaves the browser before that moment.
 *
 * The page is never reloaded while she composes: the files she designated
 * are held here, by name, and a reload would lose them -- a browser gives
 * no content back once its page is gone. So every gesture posts its task,
 * the server answers the container it built, and that container replaces
 * the one which was shown.
 *
 * No text is written here: what is displayed comes from the server, which
 * is the only one knowing what is accepted and what was refused.
 *
 * handleSwappFilesOnLoad() has to be invoked **after** the DOM is loaded.
 *
 */
export default class SwappFiles {

    /** The container the server built, the one which is shown. */
    #container;

    /** The files a person designated, by name, held until she sends. */
    #designated;

    /** What posts a task to the server and reads its answer. */
    #request;

    /** What opens the dialog of information of the page. */
    #dialog;

    // ------------------------------------------------------------------------
    // Constructor
    // ------------------------------------------------------------------------

    constructor() {
        this.#container = null;
        this.#designated = new Map();
        this.#request = new RequestManager();
        this.#dialog = new DialogManager();
    }

    // ------------------------------------------------------------------------
    // Initialization
    // ------------------------------------------------------------------------

    /**
     * Register the listeners of the container once the DOM content is loaded.
     *
     * @returns {void}
     */
    handleSwappFilesOnLoad() {
        WexaLogger.debug('Attach the listeners of the provision of files');
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded',
                () => this.#attachListeners());
        } else {
            this.#attachListeners();
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Find the container and attach what a person does in it.
     *
     * It is called again after every answer of the server: the container is
     * a new node, so the listeners of the one before are gone with it.
     *
     * @returns {void}
     */
    #attachListeners() {
        this.#container = document.getElementById(DEPOSIT_CONTAINER_ID);
        if (this.#container === null) {
            console.error('SwappFiles: no container of the provision of files was found.');
            return;
        }

        const form = this.#container.querySelector('form');
        if (form === null) {
            console.error('SwappFiles: the container holds no form.');
            return;
        }
        form.addEventListener('submit', (event) => this.#onFormSubmitted(event));

        // A file dropped on a page is opened by the browser, which replaces
        // what the person was composing. It is refused on the whole
        // container, wherever it is dropped in it, and taken in only where
        // she gives contents.
        this.#container.addEventListener('dragover', (event) => event.preventDefault());
        this.#container.addEventListener('drop', (event) => event.preventDefault());

        // Where the files stand already on the machine, the person designates
        // a path and the server asks her for it: there is no field of files,
        // so a content is given nowhere and nothing is taken from a drop.
        const input = document.getElementById(FILES_INPUT_ID);
        if (input === null) {
            return;
        }
        input.addEventListener('change', () => this.#onFilesDesignated(input.files));

        const dropzone = this.#container.querySelector('.' + DROPZONE_CLASS);
        if (dropzone !== null) {
            dropzone.addEventListener('dragover', (event) => this.#onDraggedOver(event, dropzone));
            dropzone.addEventListener('dragleave', () => dropzone.classList.remove(DRAGGED_OVER_CLASS));
            dropzone.addEventListener('drop', (event) => this.#onDropped(event, dropzone));
        }
    }

    // ------------------------------------------------------------------------
    // Private
    // ------------------------------------------------------------------------

    /**
     * Answer what a person pressed in the container, and never reload.
     *
     * A button of the container carries its task by its name: it is posted
     * as it is, with what the page transmits, and the answer replaces the
     * container. The default is prevented because a reload would lose the
     * files which were designated.
     *
     * @param {SubmitEvent} event - The submission of the form of the container.
     * @returns {Promise<void>}
     */
    async #onFormSubmitted(event) {
        event.preventDefault();

        const pressed = event.submitter;
        if (pressed === null || pressed === undefined) {
            console.error('SwappFiles: the form was submitted by no control.');
            return;
        }

        if (pressed.name === TASK_SEND && this.#designated.size > 0) {
            await this.#sendDesignatedFiles();
            return;
        }

        const posted = this.#transmittedFields();
        posted[FIELD_TASK] = pressed.name;
        posted[pressed.name] = pressed.value;
        await this.#post(posted);
    }

    // ------------------------------------------------------------------------

    /**
     * Hold the files a person designated, and have each of them answered.
     *
     * A name and a size travel, and nothing else: the bytes stay in the
     * browser until she sends. The files are held here by name, so what the
     * server refuses is shown beside what it took in.
     *
     * @param {FileList} files - What the person designated.
     * @returns {Promise<void>}
     */
    async #onFilesDesignated(files) {
        if (files.length === 0) {
            return;
        }

        for (const file of files) {
            this.#designated.set(file.name, file);
            const posted = this.#transmittedFields();
            posted[FIELD_TASK] = TASK_DESIGNATE;
            posted[FIELD_NAME] = file.name;
            posted[FIELD_SIZE] = file.size.toString();
            await this.#post(posted);
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Send the bytes of every file which was designated, one request each.
     *
     * One file per request, because the record travels with it and a request
     * carries one state: the server answers the container it built, which
     * says what was written and what was refused.
     *
     * @returns {Promise<void>}
     */
    async #sendDesignatedFiles() {
        for (const [name, file] of this.#designated) {
            let content = '';
            try {
                content = await SwappFiles.#readAsBase64(file);
            } catch (error) {
                console.error('SwappFiles: the file ' + name + ' could not be read.', error);
                continue;
            }

            const posted = this.#transmittedFields();
            posted[FIELD_TASK] = TASK_SEND;
            posted[FIELD_NAME] = name;
            posted[FIELD_CONTENT] = content;
            await this.#post(posted);
        }

        this.#designated.clear();
    }

    // ------------------------------------------------------------------------

    /**
     * Mark the dropzone while files are dragged over it.
     *
     * @param {DragEvent} event - The drag over the dropzone.
     * @param {HTMLElement} dropzone - The zone which is marked.
     * @returns {void}
     */
    #onDraggedOver(event, dropzone) {
        event.preventDefault();
        dropzone.classList.add(DRAGGED_OVER_CLASS);
    }

    // ------------------------------------------------------------------------

    /**
     * Take in the files which were dropped, as if they had been designated.
     *
     * @param {DragEvent} event - The drop on the dropzone.
     * @param {HTMLElement} dropzone - The zone which was marked.
     * @returns {Promise<void>}
     */
    async #onDropped(event, dropzone) {
        event.preventDefault();
        dropzone.classList.remove(DRAGGED_OVER_CLASS);

        if (event.dataTransfer === null) {
            console.error('SwappFiles: the drop carried no file.');
            return;
        }
        await this.#onFilesDesignated(event.dataTransfer.files);
    }

    // ------------------------------------------------------------------------

    /**
     * Return what the page transmits, as the hidden fields carry it.
     *
     * A request which lost them is a request which starts from nothing, and
     * the person would see her list vanish without having touched it.
     *
     * @returns {Object} One entry per hidden field of the container.
     */
    #transmittedFields() {
        const fields = {};
        const hidden = this.#container.querySelectorAll('input[type="hidden"]');
        for (const one of hidden) {
            fields[one.name] = one.value;
        }
        return fields;
    }

    // ------------------------------------------------------------------------

    /**
     * Post one task and replace the container by what the server answers.
     *
     * The task is posted to the page which holds the container: the root of
     * the server answers with the page it serves by default, which is another
     * application, and the task would be unknown there.
     *
     * @param {Object} posted - The task, and what it carries.
     * @returns {Promise<void>}
     */
    async #post(posted) {
        const pageUri = window.location.pathname.substring(1);
        const answered = await this.#request.sendPostRequest(posted, JSON_TYPE, pageUri);
        if (answered === null || answered === undefined) {
            console.error('SwappFiles: the server answered nothing.');
            return;
        }
        if (FIELD_CONTAINER in answered === false) {
            console.error('SwappFiles: the answer holds no container.', answered);
            return;
        }

        const place = this.#container.parentElement;
        this.#container.outerHTML = answered[FIELD_CONTAINER];
        this.#attachListeners();
        // The icons of what the server wrote are placed, as the ones of the page
        // were. The replaced node is out of the document, so what held it is
        // walked instead.
        if (place !== null && window.Wexa && window.Wexa.icons) {
            window.Wexa.icons.run(place);
        }

        if (FIELD_INFO in answered && answered[FIELD_INFO].length > 0) {
            this.#showInfo(answered[FIELD_INFO]);
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Display a message in the dialog of information of the page.
     *
     * @param {string} message - The message the server answered.
     * @returns {void}
     */
    #showInfo(message) {
        const dlg = document.getElementById(ID_INFO_DIALOG);
        if (dlg === null) {
            alert(message);
            return;
        }
        dlg.innerHTML = `<p>${message}</p>`;
        this.#dialog.open(ID_INFO_DIALOG);
    }

    // ------------------------------------------------------------------------

    /**
     * Return the bytes of a file, encoded in base64.
     *
     * The bytes of a file are not text, and what a request carries is: the
     * encoding is what makes a content travel in the same entry as a name.
     *
     * @param {File} file - The file to be read.
     * @returns {Promise<string>} The content, without the prefix of the reader.
     */
    static #readAsBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                const read = reader.result;
                const separator = read.indexOf(',');
                if (separator === -1) {
                    reject(new Error('The reader answered no base64 content.'));
                    return;
                }
                resolve(read.substring(separator + 1));
            };
            reader.onerror = () => reject(reader.error);
            reader.readAsDataURL(file);
        });
    }
}
