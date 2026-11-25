const wexa_statics_js = window.WEXA_JS_PATH;
const { BaseManager } = await import(`${wexa_statics_js}/transport/base_manager.js`);
const { ProgressBar } = await import(`${wexa_statics_js}/progressbar.js`);

const EVENT_NAME = 'event_name';
const PROGRESS_EVENT = 'swapp_progress';
const PROCESS_FIELD = 'swapp_process';

/**
 * :filename: sppas.ui.swapp.statics.js.swapp_process.js
 * :author: Brigitte Bigi
 * :contact: contact@sppas.org
 * :summary: JS following a long process of any app of swapp
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
 * This class follows a long process of an app, the same way for every app.
 *
 * Where the process stands is asked at regular intervals, by the name of the
 * process, and shown by the progress bar of Whakerexa which the page holds.
 * The server reads it in the file of the process: the app is asked nothing.
 * Once the process has ended, what the app does next is the app's: it is
 * given as a function.
 *
 */
export default class SwappProcess extends BaseManager {

    // ------------------------------------------------------------------------
    // Constructor
    // ------------------------------------------------------------------------

    #intervalMs;

    /**
     * @param {number} intervalMs - How often the page asks where the process stands, in milliseconds.
     */
    constructor(intervalMs) {
        super();
        this.#intervalMs = intervalMs;
    }

    // ------------------------------------------------------------------------
    // Public
    // ------------------------------------------------------------------------

    /**
     * Ask where the process stands until it has ended, then call the given function.
     *
     * @param {string} name - The name of the process, as the server gave it to the page.
     * @param {Function} ended - What the app does once the process has ended.
     * @param {Function|null} refreshed - What the app does at each refresh, if anything.
     * @returns {void}
     */
    follow(name, ended, refreshed = null) {
        const asked = {};
        asked[EVENT_NAME] = PROGRESS_EVENT;
        asked[PROCESS_FIELD] = name;
        const progressBar = new ProgressBar({
            // Nothing given back is said as null: the bar then calls the end.
            updateCallback: async () => {
                const answered = (await this.postEvents(asked)) ?? null;
                if (refreshed !== null) {
                    await refreshed();
                }
                return answered;
            },
            completeCallback: async () => await ended(),
            intervalMs: this.#intervalMs
        });
        progressBar.start();
    }
}
