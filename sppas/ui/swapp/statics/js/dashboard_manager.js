const wexa_statics_js = window.WEXA_JS_PATH;
const { WexaLogger } = await import(`${wexa_statics_js}/logger.js`);
const { BaseManager } = await import(`${wexa_statics_js}/transport/base_manager.js`);
const { DialogManager } = await import(`${wexa_statics_js}/dialog.js`);
const dialogManager = new DialogManager();

/**
 * :filename: sppas.ui.swapp.statics.js.dashboard_manager.js
 * :author: Brigitte Bigi
 * :contact: contact@sppas.org
 * :summary: JS for the Dashboard application
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
// Class: DashboardManager. Controls the page dashboard.html
// --------------------------------------------------------------------------

/**
 * This class orchestrates user interactions within *dashboard.html*. It attaches event
 * listeners to the buttons of the main container, sends corresponding asynchronous
 * requests to the server, and updates the DOM in response. It relies on BaseManager
 * for communication logic and form submission, and on WexaLogger for debug output.
 *
 * handleDashboardManagerOnLoad() has to be invoked **after** the DOM is loaded.
 *
 */
export default class DashboardManager extends BaseManager {

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
     * Register event listeners once the DOM content is loaded.
     *
     * This method must be called after the page structure is available.
     * It attaches listeners to all buttons within the main container.
     *
     * @returns {void}
     */
    handleDashboardManagerOnLoad() {
        // Self-name this tab, whatever opened it -- including the very
        // first one, launched by the OS browser command, which no
        // window.open() call ever named. The Journal's home button reuses
        // this name to switch to this tab instead of opening a duplicate.
        window.name = 'sppas_dashboard';

        WexaLogger.debug("Attach Dashboard listeners")
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.attachDashboardListeners());
        } else {
            this.attachDashboardListeners();
        }
    }

    // ------------------------------------------------------------------------

    /**
     * Attach click listeners to every button in the dashboard container.
     *
     * @returns {void}
     */
    attachDashboardListeners() {
        const container = document.getElementById('main-content');
        if (!container) return;

        // Redirections in any button -- with data-href. The links to the
        // internal pages of the WEB_PAGES registry are not here: they are
        // 'a' elements, followed by goToLink() of Whakerexa.
        const redirectButtons = container.querySelectorAll(
            '#apps_section button.app-button[data-href]');
        for (const redirectButton of redirectButtons) {
            if (!(redirectButton instanceof HTMLButtonElement)) {
                continue;
            }
            redirectButton.addEventListener('click', (event) => this.#onRedirectButtonClick(event));
            redirectButton.addEventListener('keydown', (event) => this.#onRedirectButtonKeydown(event));
        }

        // Action of any button -- without data-href
        const buttons = container.querySelectorAll('button:not([data-href])');
        buttons.forEach((btn) => {
            btn.addEventListener('click', (e) => this.#handleButtonClick(e.currentTarget));
        });

        // Attach the Exit button of the menu
        const exitBtn = document.getElementById('exit-menu');
        if (exitBtn) {
            exitBtn.addEventListener('click', (e) => this.#handleButtonClick(e.currentTarget));
        }

        // Attach the button of the Infos dialog, when the dialog is baked
        const traceDialogBtn = document.getElementById('trace_dialog_button');
        if (traceDialogBtn) {
            traceDialogBtn.addEventListener('click', (e) => this.#openTraceTabFromDialog(e.currentTarget));
        }

        // The menu button opens the same Infos tab: it also dismisses the
        // dialog, whose invitation has no reason to stay once the tab is open.
        const traceMenuBtn = document.getElementById('link-trace_button');
        if (traceMenuBtn) {
            traceMenuBtn.addEventListener('click', () => this.#hideTraceDialog());
        }

        // The displayed workspace name follows the server state: the wx
        // interface can change it at any time.
        const workspaceName = document.getElementById('workspace_name');
        if (workspaceName) {
            setInterval(() => this.#refreshWorkspaceName(), 3000);
        }
    }

    // ----------------------------------------------------------------------

    /**
     * Ask the server for the current workspace and update the displayed name.
     *
     * A failed request is only logged: the server may simply be shutting
     * down.
     *
     * @private
     * @async
     * @returns {Promise<void>} Resolves when the name has been updated,
     * or when the failure has been logged.
     */
    async #refreshWorkspaceName() {
        const nameSpan = document.getElementById('workspace_name');
        if (nameSpan === null) {
            return;
        }

        // RequestManager catches its own network errors and resolves with
        // the Error object instead of rejecting: the guard below already
        // discards it, since it never has a workspace_name string.
        const pageUri = window.location.pathname.substring(1) || window.SPPAS_DEFAULT_PAGE;
        const response = await this._requestManager.sendPostRequest(
            {workspace_name: true}, "application/json", pageUri);

        if (response instanceof Error) {
            WexaLogger.debug(`Workspace name not refreshed: ${response}`);
            return;
        }
        if (response && typeof response.workspace_name === 'string') {
            nameSpan.textContent = response.workspace_name;
            if (typeof response.workspace_path === 'string' && response.workspace_path.length > 0) {
                nameSpan.setAttribute('title', response.workspace_path);
            } else {
                nameSpan.removeAttribute('title');
            }
        }
        if (response && typeof response.trace_alive === 'boolean') {
            this.#toggleTraceDialog(response.trace_alive);
        }
    }

    // ----------------------------------------------------------------------

    /**
     * Show or hide the Infos dialog, following the Journal tab liveness
     * reported by the periodic poll -- no page reload needed.
     *
     * @private
     * @param {boolean} traceAlive - True when the Journal tab is open.
     * @returns {void}
     */
    #toggleTraceDialog(traceAlive) {
        const dlg = document.getElementById('trace_dialog');
        if (dlg === null) {
            return;
        }
        if (traceAlive === true) {
            this.#hideTraceDialog();
        } else if (dlg.classList.contains('hidden-alert')) {
            dlg.classList.remove('hidden-alert');
            dialogManager.open('trace_dialog', true);
        }
    }

   // ----------------------------------------------------------------------

    /**
     * Open data-href (Enter/Space support) while preserving accessibility parameters.
     *
     * @param {KeyboardEvent} event
     * @returns {void}
     */
    #onRedirectButtonKeydown(event) {
        if (event.key !== 'Enter' && event.key !== ' ') {
            return;
        }
        event.preventDefault();
        this.#openRedirectFromEventTarget(event);
    }

   // ----------------------------------------------------------------------

    /**
     * Open data-href while preserving accessibility parameters.
     *
     * @param {MouseEvent} event
     * @returns {void}
     */
    #onRedirectButtonClick(event) {
        event.preventDefault();
        this.#openRedirectFromEventTarget(event);
    }

    // ----------------------------------------------------------------------

    /**
     * Extract data-href from the event target and open it in a new tab.
     *
     * @param {Event} event
     * @returns {void}
     */
    #openRedirectFromEventTarget(event) {
        const button = event.currentTarget;
        if (!(button instanceof HTMLButtonElement)) {
            return;
        }

        const href = button.getAttribute('data-href');
        if (typeof href !== 'string' || href.trim().length === 0) {
            return;
        }

        const absolute = new URL(href, window.location.href).href;
        const target = new URL(window.Wexa.accessibility.setUrlWithParameters(absolute));

        // An application bringing its own theme is shown with it: the theme
        // of this page is left behind, while the color scheme and the
        // contrast follow -- they are choices of the reader, not of the app.
        if (button.hasAttribute('data-theme') === true) {
            target.searchParams.delete('wexa_theme');
        }

        window.location.href = target.href;
    }

    // ----------------------------------------------------------------------

    /**
     * Open (or reuse) the named tab of the Infos page, then hide the dialog.
     *
     * The named target reuses the single tab of the trace page. There is no
     * 'noopener': the window name lookup needs the opener relationship, and
     * the target is an internal page.
     *
     * @param {HTMLButtonElement} btn - The clicked button of the Infos dialog.
     * @returns {void}
     */
    #openTraceTabFromDialog(btn) {
        const href = btn.getAttribute('data-href');
        const name = btn.getAttribute('data-target');
        if (typeof href !== 'string' || href.trim().length === 0) {
            return;
        }

        const absolute = new URL(href, window.location.href).href;
        const finalUrl = window.Wexa.accessibility.setUrlWithParameters(absolute);
        window.open(finalUrl, name);

        this.#hideTraceDialog();
    }

    // ----------------------------------------------------------------------

    /**
     * Hide and close the Infos dialog, if it is baked in the page.
     *
     * @returns {void}
     */
    #hideTraceDialog() {
        const dlg = document.getElementById('trace_dialog');
        if (dlg != null) {
            dlg.classList.add("hidden-alert");
            dialogManager.close('trace_dialog');
        }
    }

    // ----------------------------------------------------------------------
    // Buttons event dispatch
    // ----------------------------------------------------------------------

    /**
     * Central handler for all dashboard buttons.
     *
     * @param {HTMLElement} btn - The clicked button element.
     * @returns {void}
     */
    #handleButtonClick(btn) {
        switch (btn.id) {
            case 'agree_button':
                this.#sendAgreement();
                break;
            case 'desktop_button':
                this.#sendDesktopLaunch(btn);
                break;
            case 'exit-menu':
                this.#submitExitForm()
                break;
            default:
                WexaLogger.debug(`Unhandled button: ${btn.id}`);
        }
    }

    // ----------------------------------------------------------------------
    // Actions
    // ----------------------------------------------------------------------

    /**
    * Send the licence agreement event to the server and close the dialog.
    *
    * This method sends an event notifying the server that the user has accepted
    * the licence agreement. If the server responds successfully, the associated
    * dialog is visually hidden and closed using the DialogManager API to ensure
    * proper cleanup of accessibility states and focus handling. If the dialog
    * element is not found or the server does not respond, a warning or info
    * message is logged for debugging purposes.
    *
    * @private
    * @async
    * @returns {Promise<void>} Resolves when the event has been sent and the
    * dialog is closed or when an error has been logged.
    */
    async #sendAgreement() {
        const events = {'event_bake': 'handle_licence_agreement'};
        const response = await this.postEvents(events);
        if (response) {
            let dlg = document.getElementById('agreement_dialog');
            if (dlg != null) {
                dlg.classList.add("hidden-alert");
                dialogManager.close('agreement_dialog');
            } else {
                WexaLogger.warn("No such dialog with ID 'agreement_dialog'.");
            }
        } else {
            WexaLogger.info("Can't close dialog: No server response. ")
        }
    }

    // ----------------------------------------------------------------------

    async #sendDesktopLaunch(btn) {
        // Disable the button so that the wx interface can be launched only once.
        btn.setAttribute("disabled", "")
        // Send the event to the server so that it can launch the app.
        const events = {'event_bake': 'handle_start_sppas'};
        // The response is arriving when the SPPAS process ended
        const response = await this.postEvents(events);
        // Restore enabling button
        btn.removeAttribute("disabled")
        if (response) {
            WexaLogger.info("Launched & terminated SPPAS app...")
        } else {
            WexaLogger.info("Can't launch SPPAS: No server response. ")
        }
    }

    // ----------------------------------------------------------------------

    /**
     * Trigger a clean exit by submitting a hidden POST form.
     *
     * This method allows the browser to perform a full HTTP POST navigation
     * handled entirely by the server before it stops.
     *
     * @returns {void}
     */
    #submitExitForm() {
        this.submitForm('event_bake', 'close');
    }

}
