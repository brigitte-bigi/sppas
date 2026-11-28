const wexa_statics_js = window.WEXA_JS_PATH;
const { BaseManager } = await import(`${wexa_statics_js}/transport/base_manager.js`);

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
