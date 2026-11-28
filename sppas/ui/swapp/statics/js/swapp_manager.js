const wexa_statics_js = window.WEXA_JS_PATH;
const { BaseManager } = await import(`${wexa_statics_js}/transport/base_manager.js`);
const { WexaLogger } = await import(`${wexa_statics_js}/logger.js`);

const ID_ERROR_DIALOG = 'error_dialog';
const ID_INFO_DIALOG = 'info_dialog';
const DATA_ERROR = 'error';
const DATA_INFO = 'info';
const JSON_TYPE = 'application/json';

/**
 * :filename: sppas.ui.swapp.statics.js.swapp_manager.js
 * :author: Brigitte Bigi
 * :contact: contact@sppas.org
 * :summary: JS manager of any app of swapp, and the address its requests are sent to
 *
 * .. _This file is part of SPPAS: https://sppas.org/
 * ..
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
 * Return the address the requests of the page are sent to.
 *
 * It is the address of the page itself, with what follows its name: online,
 * an app is reached at a secret name, and what authorizes that name is
 * carried after it. A request sent to the name alone would be refused.
 *
 * @returns {string} The address, without its leading slash.
 */
export function pageAddress() {
    const url = new URL(window.location.href);
    return url.pathname.substring(1) + url.search;
}

// ---------------------------------------------------------------------------

/**
 * This class is the manager of any app of swapp.
 *
 * It is the manager of Whakerexa, whose requests are sent to the address of
 * the page, as pageAddress() gives it.
 *
 */
export default class SwappManager extends BaseManager {

    /**
     * Create the manager, which sends its requests to the address of the page.
     *
     * @constructor
     */
    constructor() {
        super();
        this._uri = pageAddress();
    }

    // ------------------------------------------------------------------------

    /**
     * Send events to the address of the page, and return what the server answered.
     *
     * What the server said is said in the dialog of the errors or in the one
     * of the information, and the page is not reloaded: a reload is a request
     * which transmits nothing, and what was said would be lost with what the
     * page holds. The answer is given back all the same, so that what the
     * server wrote is put in the page. A request which failed is said in the
     * dialog of the errors, as the base manager says it, and nothing is given
     * back.
     *
     * @param {Object} events - What is sent, by name.
     * @returns {Promise<Object|undefined>} The answer, undefined when there is none or when the request failed.
     */
    async postEvents(events) {
        let answered;
        try {
            answered = await this._requestManager.sendPostRequest(events, JSON_TYPE, this._uri);
        } catch (error) {
            WexaLogger.error(`SwappManager: no answer from the server. ${error}`);
            return;
        }
        if (answered === null || answered === undefined) {
            return;
        }

        const error = answered[DATA_ERROR] || '';
        const info = answered[DATA_INFO] || '';
        if (this._requestManager.status !== 200) {
            if (error.length > 0 || info.length > 0) {
                this._showActionResult(error, info, false);
                return;
            }
            return answered;
        }
        if (error.length > 0) {
            this._say(ID_ERROR_DIALOG, error);
        } else if (info.length > 0) {
            this._say(ID_INFO_DIALOG, info);
        }

        return answered;
    }

    // ------------------------------------------------------------------------

    /**
     * Say one thing in the dialog of the given identifier, in place of what it said.
     *
     * @param {string} id - Identifier of the dialog.
     * @param {string} text - What is said.
     * @returns {void}
     */
    _say(id, text) {
        const dialog = document.getElementById(id);
        if (!(dialog instanceof HTMLDialogElement)) {
            WexaLogger.error(`SwappManager: the dialog ${id} was not found.`);
            return;
        }
        const p = document.createElement('p');
        p.textContent = text;
        dialog.replaceChildren(p);
        this._dialog.open(id, true);
    }

    // ------------------------------------------------------------------------

    /**
     * Send fields as a navigation, so that the server answers the whole page.
     *
     * WhakerPy signs the address of a link in a page it serves, and in nothing
     * else: what the page answered holds, the links of the produced files
     * included, is signed where it has to be. The form is sent to the address
     * of the page, and stays in the document: a form removed once submitted
     * leaves the browser abandoning the navigation it was starting.
     *
     * @param {Object} fields - What is sent, by name.
     * @returns {void}
     */
    submitFields(fields) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/' + pageAddress();
        form.hidden = true;
        for (const [name, value] of Object.entries(fields)) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = name;
            input.value = String(value);
            form.appendChild(input);
        }
        document.body.appendChild(form);
        form.submit();
    }

}
