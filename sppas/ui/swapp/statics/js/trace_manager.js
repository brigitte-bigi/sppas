const wexa_statics_js = window.WEXA_JS_PATH;
const { WexaLogger } = await import(`${wexa_statics_js}/logger.js`);
const { RequestManager } = await import(`${wexa_statics_js}/transport/request.js`);

/**
 * :filename: sppas.ui.swapp.statics.js.trace_manager.js
 * :author: Brigitte Bigi
 * :contact: contact@sppas.org
 * :summary: JS for the page journal.html
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
// Class: TraceManager. Controls the page journal.html
// --------------------------------------------------------------------------

/**
 * This class sends the heartbeat of *journal.html* and drives the toggle
 * choosing which panel is shown.
 *
 * The page is the single tab displaying the traces: a periodic POST tells
 * the server that this tab is open. When the heartbeat stops, the server
 * knows the tab was closed and the Dashboard invites the user to re-open
 * it. A failed request is only logged: the server may simply be shutting
 * down.
 *
 * The toggle is a native radiogroup (see Whakerexa's togglegroup.css):
 * keyboard operation and the checked/unchecked announcement come from the
 * radio inputs themselves. Hiding a panel with the "hidden" class removes
 * it from the accessibility tree, exactly like showing it restores it --
 * nothing extra is needed for assistive technologies.
 *
 * handleTraceManagerOnLoad() has to be invoked **after** the DOM is loaded.
 *
 */
export default class TraceManager {

    // ------------------------------------------------------------------------
    // Constructor
    // ------------------------------------------------------------------------

    constructor() {
        // Milliseconds between two heartbeats.
        this.heartbeatInterval = 15000;
        this.requestManager = new RequestManager();
        // Reset to 0 by any successful heartbeat; a run of failures means
        // the server itself is gone, not a single dropped request.
        this.failedHeartbeats = 0;
        this.maxFailedHeartbeats = 2;
        this.heartbeatTimer = null;
    }

    // ------------------------------------------------------------------------
    // Initialization
    // ------------------------------------------------------------------------

    /**
     * Start the heartbeat and the panel toggle once the DOM is loaded.
     *
     * This method must be called after the page structure is available.
     *
     * @returns {void}
     */
    handleTraceManagerOnLoad() {
        WexaLogger.debug('Start the trace heartbeat');
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.#onLoad());
        } else {
            this.#onLoad();
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Start the heartbeat and attach the panel toggle listeners.
     *
     * @private
     * @returns {void}
     */
    #onLoad() {
        this.startHeartbeat();
        this.#attachPanelToggle();
    }

    // ------------------------------------------------------------------------

    /**
     * Attach the change listener of the panel-view toggle, if baked.
     *
     * @private
     * @returns {void}
     */
    #attachPanelToggle() {
        const radios = document.querySelectorAll('input[name="trace_panel_view"]');
        radios.forEach((radio) => {
            radio.addEventListener('change', () => this.#applyPanelView(radio.value));
        });
    }

    // ------------------------------------------------------------------------

    /**
     * Show the requested panel(s), hiding the other one with the "hidden"
     * class -- the same idiom already used for the feedback report blocks.
     *
     * "width_50" is a fixed 48% width: a panel left alone does not grow
     * to fill the row on its own, so its width class is switched too.
     *
     * @private
     * @param {string} view - One of "left", "both", "right".
     * @returns {void}
     */
    #applyPanelView(view) {
        const apiPanel = document.getElementById('trace_api_panel');
        const uiPanel = document.getElementById('trace_ui_panel');
        if (apiPanel === null || uiPanel === null) {
            return;
        }

        apiPanel.classList.toggle('hidden', view === 'right');
        uiPanel.classList.toggle('hidden', view === 'left');

        const apiAlone = view === 'left';
        apiPanel.classList.toggle('width_50', !apiAlone);
        apiPanel.classList.toggle('width_full', apiAlone);

        const uiAlone = view === 'right';
        uiPanel.classList.toggle('width_50', !uiAlone);
        uiPanel.classList.toggle('width_full', uiAlone);
    }

    // ------------------------------------------------------------------------

    /**
     * Send an immediate heartbeat, then one every heartbeatInterval.
     *
     * @returns {void}
     */
    startHeartbeat() {
        this.sendHeartbeat();
        this.heartbeatTimer = setInterval(() => this.sendHeartbeat(), this.heartbeatInterval);
    }

    // ------------------------------------------------------------------------
    // Actions
    // ------------------------------------------------------------------------

    /**
     * Send one heartbeat to the server.
     *
     * A run of maxFailedHeartbeats failures means the server itself is
     * gone -- not a single dropped request -- and there is no server left
     * to bake the real "session ended" page: this page has to build it.
     *
     * @private
     * @async
     * @returns {Promise<void>} Resolves when the heartbeat has been sent,
     * or when its failure has been handled.
     */
    async sendHeartbeat() {
        const pageUri = window.location.pathname.substring(1);
        // RequestManager catches its own network errors and resolves with
        // the Error object instead of rejecting: a failure is read from
        // the returned value, not from a thrown exception.
        const response = await this.requestManager.send_post_request(
            {trace_heartbeat: true}, "application/json", pageUri);

        if (response instanceof Error) {
            this.failedHeartbeats += 1;
            WexaLogger.debug(`TraceManager: heartbeat not sent: ${response}`);
            if (this.failedHeartbeats >= this.maxFailedHeartbeats) {
                this.#showSessionEnded();
            }
        } else {
            this.failedHeartbeats = 0;
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Replace the page content with the "session ended" message.
     *
     * The messages come from data attributes of #main-content -- baked in
     * the page's own language -- exactly the ones the real 410 response
     * uses, since no server is left to bake that response itself. Their
     * translation may carry a <br>, like the real response also renders
     * it raw: both come from the same, translator-controlled source, not
     * from user input.
     *
     * @private
     * @returns {void}
     */
    #showSessionEnded() {
        clearInterval(this.heartbeatTimer);

        const main = document.getElementById('main-content');
        if (main === null) {
            return;
        }
        const title = main.dataset.msgSessionEnded || '';
        const description = main.dataset.msgCloseTab || '';
        main.replaceChildren();
        const h2 = document.createElement('h2');
        h2.textContent = title;
        const p = document.createElement('p');
        p.innerHTML = description;
        main.append(h2, p);
    }
}
