const wexa_statics_js = window.WEXA_JS_PATH;
const { WexaLogger } = await import(`${wexa_statics_js}/logger.js`);
const { DialogManager } = await import(`${wexa_statics_js}/dialog.js`);
const dialogManager = new DialogManager();

const ID_ERROR_DIALOG = 'error_dialog';

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
export default class AnnotateManager {

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

        const errorDlg = document.getElementById(ID_ERROR_DIALOG);
        if (errorDlg instanceof HTMLDialogElement && errorDlg.textContent.trim().length > 0) {
            dialogManager.open(ID_ERROR_DIALOG, true);
        }
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
