const wexa_statics_js = window.WEXA_JS_PATH;
const { DialogManager } = await import(`${wexa_statics_js}/dialog.js`);
const dialogManager = new DialogManager();

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
 * button opens it, and nothing is asked of the server.
 *
 * handlePluginsManagerOnLoad() has to be invoked **after** the DOM is loaded.
 */
export default class PluginsManager {

    /**
     * Attach the listeners of the page.
     *
     * @returns {void}
     */
    handlePluginsManagerOnLoad() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.#attachDialogs();
            });
        } else {
            this.#attachDialogs();
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Have each button which opens a dialog of the page open it, as a modal.
     *
     * @private
     * @returns {void}
     */
    #attachDialogs() {
        document.querySelectorAll('button[aria-haspopup="dialog"][aria-controls]').forEach((button) => {
            button.addEventListener('click', () => {
                dialogManager.open(button.getAttribute('aria-controls'), true);
            });
        });
    }

}
