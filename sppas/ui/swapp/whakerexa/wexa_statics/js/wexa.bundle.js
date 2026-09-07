// Bundle automatically generated on 2026-09-07 16:14:02

// ---------------- logger.js ---------------
class WexaLogger {
    static DEFAULT_LEVEL = 20;
    static #NAMES = {
        debug: 10,
        info: 20,
        warning: 30,
        error: 40,
        critical: 50
    };
    static #logLevel = WexaLogger.DEFAULT_LEVEL;
    // -----------------------------------------------------------------------
    static levelOf(said) {
        if (typeof said === 'number') {
            return (said >= 0 && said <= 50) ? said : null;
        }
        if (typeof said !== 'string') {
            return null;
        }
        const written = said.trim().toLowerCase();
        if (written === '') {
            return null;
        }
        if (Object.prototype.hasOwnProperty.call(WexaLogger.#NAMES, written) === true) {
            return WexaLogger.#NAMES[written];
        }
        if (/^[0-9]+$/.test(written) === false) {
            return null;
        }
        const counted = Number(written);
        return counted <= 50 ? counted : null;
    }
    // -----------------------------------------------------------------------
    static takeWhatThePageSaid() {
        const namespace = (typeof window !== 'undefined') ? window.Wexa : undefined;
        if (namespace === undefined || namespace === null) {
            return;
        }
        const level = WexaLogger.levelOf(namespace.logLevel);
        if (level !== null) {
            WexaLogger.#logLevel = level;
        }
    }
    static getLogLevel() {
        return this.#logLevel;
    }
    static setLogLevel(level) {
        const counted = WexaLogger.levelOf(level);
        if (counted === null) {
            console.warn('[WexaWarning] Invalid log level: ' + level
                + '. A name -- debug, info, warning, error, critical -- or a'
                + ' number between 0 and 50.');
            return;
        }
        WexaLogger.#logLevel = counted;
    }
    static debug(msg) {
        if (this.#logLevel <= 10) console.info(`[WexaDebug] ${msg}`);
    }
    static info(msg) {
        if (this.#logLevel <= 20) console.info(`[WexaInfo] ${msg}`);
    }
    static warn(msg) {
        if (this.#logLevel <= 30) console.warn(`[WexaWarning] ${msg}`);
    }
    static error(msg, err) {
        if (this.#logLevel <= 40) console.error(`[WexaError] ${msg}`, err || '');
    }
    static critical(msg, err) {
        console.error(`[WexaCritical] ${msg}`, err || '');
    }
}
// What the page said before the framework was there. This file is the first of
// the framework to be read, so nothing of it has spoken yet.
WexaLogger.takeWhatThePageSaid();
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.WexaLogger = WexaLogger;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- transport/request.js ---------------
class RequestManager {
    // FIELDS
    // The declaration outside the constructor and the '#' symbol notify a private attribute.
    #protocol;
    #port;
    #url;
    #status;
    maxFileSize;
    // CONSTRUCTOR
    constructor() {
        this.#protocol = window.location.protocol;
        this.#port = window.location.port;
        this.#url = this.#protocol + "//" + window.location.hostname + ":" + this.#port + "/";
        this.#status = null;
        this.maxFileSize = 0;  // No upload file size limit
    }
    // ----------------------------------------------------------------------
    // GETTERS
    // ----------------------------------------------------------------------
    get protocol() {
        return this.#protocol;
    }
    // ----------------------------------------------------------------------
    get port() {
        return this.#port;
    }
    // ----------------------------------------------------------------------
    get requestUrl() {
        return this.#url;
    }
    // ----------------------------------------------------------------------
    get status() {
        return this.#status;
    }
    // ----------------------------------------------------------------------
    // METHODS
    // ----------------------------------------------------------------------
    async sendGetRequest(uri = "", is_json_response = false) {
        const completeUrl = this.requestUrl + uri;
        let requestResponseData = null;
        // send request to the server
        await fetch(completeUrl)
            // then gets content of the server response
            .then(async response =>  {
                // get the status response and check if there is an error
                this.#status = response.status;
                // get the content of the server response and parse them if it's a json format
                if (is_json_response) {
                    const text = await response.text();
                    if (text.trim() === '') {
                        requestResponseData = {};   // JSON vide → objet vide
                    } else {
                        try {
                            requestResponseData = JSON.parse(text);
                        } catch (error) {
                            console.error('Failed to parse JSON response', error);
                            requestResponseData = {
                                status: response.status,
                                error: 'Failed to parse JSON.',
                                raw: text
                            };
                        }
                    }
                } else {
                    requestResponseData = await response.text();
                }
            })
            // handle error
            .catch(error => {
                this.#status = error.status;
                requestResponseData = error;
            });
        return requestResponseData;
    }
    // ----------------------------------------------------------------------
    async sendPostRequest(postParameters, accept_type = "application/json", uri = "") {
		const completeUrl = this.requestUrl + uri;
        let requestResponseData = null;
        // build request header and body depending on parameter passed to the method
        postParameters = JSON.stringify(postParameters);
        let requestHeader = {
            'Accept': accept_type,
            'Content-Type': "application/json; charset=utf-8",
            'Content-Length': postParameters.length.toString()
        }
        // send request to the server
        await fetch(completeUrl, {
            method: "POST",
            headers: requestHeader,
            body: postParameters
        })
            // then gets content of the server response
            .then(async response =>  {
                // get the status response and check if there is an error
                this.#status = response.status;
                if (accept_type.includes("application/json")) {
                    const text = await response.text();
                    if (text.trim() === '') {
                        requestResponseData = {};
                    } else {
                        try {
                            requestResponseData = JSON.parse(text);
                        } catch (error) {
                            if (!response.headers.get('Content-Type')?.includes('application/json')) {
                                // No backend available: ignore silently
                                return {};
                            } else {
                                console.error("Failed to parse JSON response: " + error);
                                requestResponseData = {
                                    status: response.status,
                                    error: "Failed to parse JSON. See error details in the newly opened tab.",
                                    html: text
                                };
                                this.openErrorTab(text);
                            }
                        }
                    }
                }
                // Handle HTML responses (e.g., error pages)
                else if (accept_type.includes("text/html")) {
                    // If response is HTML, treat it as a failed request (500 error or other)
                    const responseText = await response.text();
                    requestResponseData = {
                        status: response.status,
                        error: "Received HTML instead of JSON. See error details in the newly opened tab.",
                        html: responseText
                    };
                    // Open a new tab to display the HTML error content
                    this.openErrorTab(responseText);
                }
                else {
                    requestResponseData = await response.blob();
                }
            })
            // handle error
            .catch(error => {
                this.#status = error.status;
                requestResponseData = error;
            })
        ;
        return requestResponseData;
    }
    // ----------------------------------------------------------------------
    openErrorTab(responseText) {
        // Optionally open a new tab to display the HTML error content
        const errorTab = window.open();
        if (errorTab) {
            errorTab.document.open();
            errorTab.document.write(responseText);
            errorTab.document.close();
        } else {
            console.error("Failed to open a new tab for the error page.");
        }
    }
    // ----------------------------------------------------------------------
    async uploadFile(input, accept_type = "application/json", token = "", uri = "") {
        let responseData = null;
        const completeUrl = this.requestUrl + uri;
        this.#status = 400;
        // Exit the function if no file is selected
        if (!input || !input.files || !input.files[0]) {
            console.warn("No file selected for upload.");
            // Return a JSON object with status 400 and an error message
            return { error: "No file or empty file selected for upload." };
        }
        console.debug("Defined size limit: ", this.maxFileSize);
        console.debug("File size to upload: ", input.files[0].size);
        // Exit the function if size limit
        if (this.maxFileSize !== 0 && input.files[0].size > this.maxFileSize) {
            console.error(`File size exceeds maximum of ${this.maxFileSize} bytes.`);
            // Return a JSON object with status 400 and an error message
            return { error: "File size exceeds maximum allowed length." };
        }
        // Create a new File instance, with the sanitized filename (no diacritics)
        let sanitizedFileName = input.files[0].name.normalize('NFD').replace(/[\u0300-\u036f]/g, "");
        let sanitizedFile = new File([input.files[0]], sanitizedFileName, {
            type: input.files[0].type,
            lastModified: input.files[0].lastModified,
        });
        // Format file to upload to the server
        let data = new FormData();
        data.append('file', sanitizedFile);
        // Send request to the back-end and wait for the response (response in json)
        await fetch(completeUrl, {
            method: 'POST',
            headers: {
                'Accept': accept_type,
                'X-Auth-Token': 'Bearer ' + token
            },
            body: data
        })
        // get the response and update the current status code
        .then(async response => {
            console.debug(" ... server answer: ", response);
            this.#status = response.status;
            // Check if the status is not 200 and there is no error in the response
            if (response.status !== 200 && !response.error) {
                // Return a JSON object with statusText to indicate the error
                responseData = { "error": response.statusText };
            } else {
                // If status is 200 or there is an error, return the JSON response
                responseData = await response.json();
            }
        })
        // handle error
        .catch(error => {
            console.error(" ... server error: ", error);
            this.#status = error.status;
            responseData = error;
        })
        return responseData;
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.RequestManager = RequestManager;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- transport/base_manager.js ---------------
'use strict';
class BaseManager {
    // ----------------------------------------------------------------------
    // Private members shared by all classes
    // ----------------------------------------------------------------------
    // An instance of the RequestManager class responsible for managing HTTP requests.
    _requestManager;
    // A string representing the current URL path, extracted from the window location.
    _uri;
    // ----------------------------------------------------------------------
    // Constructor
    // ----------------------------------------------------------------------
    constructor() {
        this._requestManager = new RequestManager();
        let url = new URL(window.location.href);
        this._uri = url.pathname.substring(1);
        this._dialog = new DialogManager();
    }
    // ----------------------------------------------------------------------
    _showActionResult(error = "", info = "", reload = true) {
        if (this._requestManager.status !== 200) {
            WexaLogger.error(`HTTP error ${this._requestManager.status}: ${error}`);
            this._showDialog('error_dialog', `Erreur ${this._requestManager.status} : ${error}`);
        } else {
            if (info && !reload) {
                WexaLogger.info(info);
                this._showDialog('info_dialog', info);
            }
            if (reload) {
                window.location.reload();
            }
        }
    }
    // ----------------------------------------------------------------------
    submitForm(inputName, inputValue) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.style.display = 'none';
            const input = document.createElement('input');
            input.name = inputName;
            input.value = inputValue;
            input.type = 'hidden';
            form.appendChild(input);
            document.body.appendChild(form);
            form.submit();
            // Clean the DOM
            document.body.removeChild(form);
    }
    // ----------------------------------------------------------------------
    async postEvents(events) {
        let response;
        let respError= "";
        let respInfo = "";
        try {
            response = await this._requestManager.sendPostRequest(
                events,
                'application/json',
                this._uri
            );
            WexaLogger.debug(`HTTP status ${this._requestManager.status}`);
            // If there's a message in the response
            respError = response.error || "";
            respInfo = response.info || "";
        } catch (error) {
            // Do not handle any request or network error: it's probably a standard server, not a WhakerPy one!
            // respError = error.toString();
            // No backend available: ignore silently
            return;
        }
        // Server replied: process normally
        if (respError || respInfo) {
            this._showActionResult(respError, respInfo, true);
            return;
        }
        // No server response: ignore silently
        if (!response) {
            return;
        }
        // Return the response if no message sent
        return response;
    }
    // ----------------------------------------------------------------------
    _showDialog = (dialogId, message) => {
        let dlg = document.getElementById(dialogId);
        if (dlg != null) {
            dlg.innerHTML = `<p>${message}</p>`;
            this._dialog.open(dialogId);
        } else {
            alert(message);
        }
    }
    // ----------------------------------------------------------------------
    _hideDialog = (dialogId) => {
        let dlg = document.getElementById(dialogId);
        if (dlg != null) {
            dlg.innerHTML = ``;
            this._dialog.close(dialogId);
        } else {
            WexaLogger.warn(`No such dialog ${dialogId}`);
        }
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.BaseManager = BaseManager;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- keyboard.js ---------------
'use strict';
class KeyboardController {
    // CONSTANTS
    static RESERVED_KEYS = ['Enter', ' '];
    static INTERACTIVE_TAGS = ['input', 'select', 'textarea', 'button', 'summary'];
    // FIELDS
    #shortcuts;
    #boundHandler;
    #listening;
    // CONSTRUCTOR
    constructor() {
        this.#shortcuts = new Map();
        this.#boundHandler = this.#onKeyDown.bind(this);
        this.#listening = false;
    }
    // GETTERS
    get shortcuts() {
        const said = [];
        this.#shortcuts.forEach(shortcut => {
            if (said.includes(shortcut) === false) {
                said.push(shortcut);
            }
        });
        return said.map(shortcut => ({keys: [...shortcut.keys], label: shortcut.label}));
    }
    // PUBLIC METHODS
    register({keys, action, detail = {}, label = '', preventsDefault = false}) {
        if (Array.isArray(keys) === false || keys.length === 0) {
            console.warn('KeyboardController: a shortcut without a key is not declared.');
            return;
        }
        if (typeof action !== 'function' && typeof action !== 'string') {
            console.warn(`KeyboardController: the keys "${keys.join(', ')}" do nothing, and are not declared.`);
            return;
        }
        const answered = keys.filter(key => KeyboardController.RESERVED_KEYS.includes(key) === false);
        if (answered.length !== keys.length) {
            console.warn('KeyboardController: Enter and space operate what holds the focus, and are not declared.');
        }
        if (answered.length === 0) {
            return;
        }
        const shortcut = {keys: answered, action: action, detail: detail,
                          label: label, preventsDefault: preventsDefault};
        answered.forEach(key => {
            if (this.#shortcuts.has(key) === true) {
                console.warn(`KeyboardController: the key "${key}" was already answered, and its answer is replaced.`);
            }
            this.#shortcuts.set(key, shortcut);
        });
    }
    // -----------------------------------------------------------------------
    forget(keys) {
        keys.forEach(key => this.#shortcuts.delete(key));
    }
    // -----------------------------------------------------------------------
    init() {
        if (this.#listening === true) {
            return;
        }
        document.body.addEventListener('keydown', this.#boundHandler, false);
        this.#listening = true;
    }
    // -----------------------------------------------------------------------
    destroy() {
        document.body.removeEventListener('keydown', this.#boundHandler, false);
        this.#listening = false;
    }
    // -----------------------------------------------------------------------
    static isInteractiveTarget(target) {
        if (target instanceof HTMLElement === false) {
            return true;
        }
        const tag = target.tagName.toLowerCase();
        if (KeyboardController.INTERACTIVE_TAGS.includes(tag) === true) {
            return true;
        }
        if (tag === 'a' && target.hasAttribute('href') === true) {
            return true;
        }
        if ((tag === 'video' || tag === 'audio') && target.hasAttribute('controls') === true) {
            return true;
        }
        if (target.isContentEditable === true) {
            return true;
        }
        const reachable = target.getAttribute('tabindex');
        if (reachable !== null) {
            const rank = parseInt(reachable, 10);
            if (Number.isNaN(rank) === false && rank >= 0) {
                return true;
            }
        }
        return false;
    }
    // PRIVATE METHODS
    #onKeyDown(event) {
        const shortcut = this.#shortcuts.get(event.key);
        if (shortcut === undefined) {
            return;
        }
        if (KeyboardController.isInteractiveTarget(event.target) === true) {
            return;
        }
        if (shortcut.preventsDefault === true) {
            event.preventDefault();
        }
        if (typeof shortcut.action === 'function') {
            shortcut.action(event);
            return;
        }
        document.dispatchEvent(new CustomEvent(shortcut.action, {detail: shortcut.detail}));
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.KeyboardController = KeyboardController;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/slides_data.js ---------------
'use strict';
class SlidesData {
    constructor(slides) {
        this.slides = Array.isArray(slides) ? slides : [];
        this.currentIndex = 1;   // 1-based
        this.currentStep  = 0;
        this.previousIndex = 0;  // 0 = no previous (initial state)
        this.mode = 'presentation';
        this.autoPlay = false;
    }
    get count() {
        return this.slides.length;
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.SlidesData = SlidesData;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/navigation_logic.js ---------------
'use strict';
class NavigationLogic {
    constructor(data) {
        this._data = data;
        this._onNavigate = null;
    }
    set onNavigate(fn) {
        this._onNavigate = typeof fn === 'function' ? fn : null;
    }
    // -----------------------------------------------------------------------
    // Public API
    // -----------------------------------------------------------------------
    next() {
        const { currentIndex, currentStep } = this._data;
        const maxStep = this._incrementalCount(currentIndex);
        if (currentIndex === this._data.count && currentStep >= maxStep) {
            return;
        }
        if (currentStep >= maxStep) {
            this._navigateTo(currentIndex + 1, 0);
        } else {
            this._navigateTo(currentIndex, currentStep + 1);
        }
    }
    prev() {
        const { currentIndex, currentStep } = this._data;
        if (currentIndex === 1 && currentStep === 0) {
            return;
        }
        if (currentStep === 0) {
            const prevIdx = currentIndex - 1;
            this._navigateTo(prevIdx, this._incrementalCount(prevIdx));
        } else {
            this._navigateTo(currentIndex, currentStep - 1);
        }
    }
    goTo(index, step = 0) {
        this._navigateTo(index, step);
    }
    goStart() {
        this._navigateTo(1, 0);
    }
    goEnd() {
        const last = this._data.count;
        this._navigateTo(last, this._incrementalCount(last));
    }
    toggleContent() {
        const slide = this._data.slides[this._data.currentIndex - 1];
        if (!(slide instanceof HTMLElement)) {
            return;
        }
        const video = slide.querySelector('video');
        if (!(video instanceof HTMLVideoElement)) {
            return;
        }
        if (video.paused || video.ended) {
            video.play();
        } else {
            video.pause();
        }
    }
    updateFromHash(hash) {
        if (typeof hash !== 'string' || hash === '' || hash[0] !== '#') {
            this._setPosition(1, 0);
            return;
        }
        const parts = hash.substring(1).split('.');
        const idx = parseInt(parts[0], 10);
        const stp = parts.length > 1 ? parseInt(parts[1], 10) : 0;
        // The address holds the reading and nothing else. A fragment that is
        // not a position names a place in the document: it is an entry of the
        // treatment that reaches a place, and the reading does not move for it.
        if (Number.isNaN(idx) === true) {
            return;
        }
        this._setPosition(idx, Number.isNaN(stp) ? 0 : stp);
    }
    // -----------------------------------------------------------------------
    // Private
    // -----------------------------------------------------------------------
    _navigateTo(index, step) {
        const changed = this._setPosition(index, step);
        if (changed) {
            window.location.hash = `#${this._data.currentIndex}.${this._data.currentStep}`;
        }
    }
    _setPosition(index, step) {
        const clamped = this._clampIndex(index);
        const clampedStep = this._clampStep(clamped, step);
        const isInitial = this._data.previousIndex === 0;
        const unchanged = clamped === this._data.currentIndex
                       && clampedStep === this._data.currentStep;
        if (!isInitial && unchanged) {
            return false;
        }
        // Pause video on the slide we're leaving
        const prevSlide = this._data.slides[this._data.currentIndex - 1];
        if (prevSlide instanceof HTMLElement) {
            const v = prevSlide.querySelector('video');
            if (v instanceof HTMLVideoElement) {
                v.pause();
            }
        }
        this._data.previousIndex = this._data.currentIndex;
        this._data.currentIndex  = clamped;
        this._data.currentStep   = clampedStep;
        // Autoplay video on the slide we're entering
        if (this._data.autoPlay) {
            const currSlide = this._data.slides[clamped - 1];
            if (currSlide instanceof HTMLElement) {
                const v = currSlide.querySelector('video');
                if (v instanceof HTMLVideoElement) {
                    v.play();
                }
            }
        }
        if (this._onNavigate !== null) {
            this._onNavigate(this._data);
        }
        return true;
    }
    _incrementalCount(index) {
        const slide = this._data.slides[this._clampIndex(index) - 1];
        if (!(slide instanceof HTMLElement)) {
            return 0;
        }
        return slide.querySelectorAll('.incremental > *').length;
    }
    _clampIndex(index) {
        const n = this._data.count;
        if (n === 0) {
            return 1;
        }
        return Math.max(1, Math.min(index, n));
    }
    _clampStep(index, step) {
        return Math.max(0, Math.min(step, this._incrementalCount(index)));
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.NavigationLogic = NavigationLogic;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/viewmode_logic.js ---------------
'use strict';
class ViewModeLogic {
    static MODES = {
        PRESENTATION: 'presentation',
        OVERVIEW:     'overview',
        HANDOUT:      'handout',
        NOTE:         'note',
    };
    static DEFAULT = 'presentation';
    constructor(data) {
        this._data = data;
        this._onModeChange = null;
    }
    set onModeChange(fn) {
        this._onModeChange = typeof fn === 'function' ? fn : null;
    }
    get current() {
        return this._data.mode;
    }
    set(mode) {
        const valid = Object.values(ViewModeLogic.MODES);
        if (!valid.includes(mode)) {
            return;
        }
        this._data.mode = mode;
        if (this._onModeChange !== null) {
            this._onModeChange(this._data);
        }
    }
    toggle(mode = ViewModeLogic.MODES.OVERVIEW) {
        const next = this._data.mode === mode
            ? ViewModeLogic.MODES.PRESENTATION
            : mode;
        this._data.mode = next;
        if (this._onModeChange !== null) {
            this._onModeChange(this._data);
        }
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.ViewModeLogic = ViewModeLogic;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/visibility.js ---------------
'use strict';
class SlidesVisibilityController {
    constructor(element) {
        this._element = element instanceof HTMLElement ? element : null;
    }
    isVisible() {
        if (!(this._element instanceof HTMLElement)) {
            return false;
        }
        return window.getComputedStyle(this._element).display !== 'none';
    }
    show() {
        if (this._element instanceof HTMLElement) {
            this._element.classList.remove('controls-hidden');
            this._element.style.display = '';
        }
    }
    hide() {
        if (this._element instanceof HTMLElement) {
            this._element.style.display = 'none';
        }
    }
    toggle() {
        if (!(this._element instanceof HTMLElement)) {
            return;
        }
        // Use getComputedStyle to handle elements visible via CSS rules (not inline style).
        const computed = window.getComputedStyle(this._element).display;
        if (computed === 'none') {
            this.show();
        } else {
            this.hide();
        }
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.SlidesVisibilityController = SlidesVisibilityController;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/visibility_manager.js ---------------
'use strict';
class SlidesVisibilityManager {
    constructor(elementsMap = {}) {
        this._controllers = {};
        const names = Object.keys(elementsMap);
        for (const name of names) {
            const element = elementsMap[name];
            this._controllers[name] = new SlidesVisibilityController(element);
        }
    }
    isVisible(name) {
        const controller = this._controllers[name];
        if (controller instanceof SlidesVisibilityController) {
            return controller.isVisible();
        }
        return false;
    }
    show(name) {
        const controller = this._controllers[name];
        if (controller instanceof SlidesVisibilityController) {
            controller.show();
        }
    }
    hide(name) {
        const controller = this._controllers[name];
        if (controller instanceof SlidesVisibilityController) {
            controller.hide();
        }
    }
    toggle(name) {
        const controller = this._controllers[name];
        if (controller instanceof SlidesVisibilityController) {
            controller.toggle();
        }
    }
    showAll() {
        const names = Object.keys(this._controllers);
        for (const name of names) {
            this._controllers[name].show();
        }
    }
    hideAll() {
        const names = Object.keys(this._controllers);
        for (const name of names) {
            this._controllers[name].hide();
        }
    }
    getNames() {
        return Object.keys(this._controllers);
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.SlidesVisibilityManager = SlidesVisibilityManager;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/focus.js ---------------
'use strict';
class SlidesFocusController {
    constructor(options = {}) {
        const defaultSelector = [
            'a[href]',
            'button',
            'input',
            'select',
            'textarea',
            'details',
            'summary',
            '[tabindex]:not([tabindex="-1"])',
            '[contenteditable="true"]',
            'video[controls]',
            'audio[controls]'
        ].join(', ');
        this._focusableSelector = typeof options.focusableSelector === 'string'
            ? options.focusableSelector
            : defaultSelector;
    }
    updateFocus(slides, activeIndex) {
        if (!Array.isArray(slides) || slides.length === 0) {
            console.warn("Update focus not available. No slides found.");
            return;
        }
        let safeIndex = activeIndex;
        if (safeIndex < 1) {
            safeIndex = 1;
        }
        if (safeIndex > slides.length) {
            safeIndex = slides.length;
        }
        const activeSlide = slides[safeIndex - 1];
        slides.forEach((slide) => {
            const isActive = slide === activeSlide;
            const tabIndexValue = isActive === true ? 0 : -1;
            this._setTabIndexForSlide(slide, tabIndexValue);
        });
    }
    // -----------------------------------------------------------------------
    // Private utilities
    // -----------------------------------------------------------------------
    _setTabIndexForSlide(slide, tabIndexValue) {
        if (!(slide instanceof HTMLElement)) {
            return;
        }
        const elements = this._getFocusableElements(slide);
        const valueString = String(tabIndexValue);
        elements.forEach((element) => {
            const disabled = this._isDisabled(element);
            if (disabled === true) {
                return;
            }
            element.setAttribute('tabindex', valueString);
        });
    }
    _getFocusableElements(slide) {
        if (!(slide instanceof HTMLElement)) {
            return [];
        }
        const nodeList = slide.querySelectorAll(this._focusableSelector);
        return Array.from(nodeList);
    }
    _isDisabled(element) {
        if (!(element instanceof HTMLElement)) {
            return true;
        }
        const hasDisabledAttribute = element.hasAttribute('disabled');
        if (hasDisabledAttribute === true) {
            return true;
        }
        const ariaDisabled = element.getAttribute('aria-disabled');
        if (ariaDisabled !== null && ariaDisabled.toLowerCase() === 'true') {
            return true;
        }
        return false;
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.SlidesFocusController = SlidesFocusController;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/fullscreen.js ---------------
'use strict';
class SlidesFullscreenController {
    constructor(target = null) {
        const defaultTarget = typeof document !== 'undefined'
            ? document.documentElement
            : null;
        this._target = target instanceof HTMLElement ? target : defaultTarget;
    }
    enter() {
        if (this._target === null) {
            return;
        }
        const request = this._target.requestFullscreen
            || this._target.requestFullScreen
            || this._target.mozRequestFullScreen
            || this._target.webkitRequestFullScreen
            || null;
        if (typeof request === 'function') {
            request.call(this._target);
        }
    }
    exit() {
        if (typeof document === 'undefined') {
            return;
        }
        const exitMethod = document.exitFullscreen
            || document.cancelFullScreen
            || document.mozCancelFullScreen
            || document.webkitCancelFullScreen
            || null;
        if (typeof exitMethod === 'function') {
            exitMethod.call(document);
        }
    }
    toggle() {
        if (typeof document === 'undefined') {
            return;
        }
        const activeElement = document.fullscreenElement
            || document.mozFullScreenElement
            || document.webkitFullscreenElement
            || null;
        if (activeElement === null) {
            this.enter();
        } else {
            this.exit();
        }
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.SlidesFullscreenController = SlidesFullscreenController;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/presentation_view.js ---------------
'use strict';
class PresentationView {
    constructor(slides, progressBar = null, controlsElement = null, controlsViewElement = null) {
        this._slides       = Array.isArray(slides) ? slides : [];
        this._progressBar  = progressBar instanceof HTMLElement ? progressBar : null;
        this._controls     = controlsElement instanceof HTMLElement ? controlsElement : null;
        this._controlsView = controlsViewElement instanceof HTMLElement ? controlsViewElement : null;
        this._currentMode  = null;
    }
    // -----------------------------------------------------------------------
    // Called by SlidesAssembler via navLogic.onNavigate
    // -----------------------------------------------------------------------
    render(data) {
        this._renderSlide(data.currentIndex, data.previousIndex);
        this._renderIncremental(data.currentIndex, data.currentStep);
        this._renderProgress(data.currentIndex, data.count);
    }
    // -----------------------------------------------------------------------
    // Called by SlidesAssembler via modeLogic.onModeChange
    // -----------------------------------------------------------------------
    onModeChange(data) {
        // Sync body class
        if (this._currentMode !== null) {
            document.body.classList.remove(`${this._currentMode}-view`);
        }
        this._currentMode = data.mode;
        document.body.classList.add(`${data.mode}-view`);
        if (data.mode === 'presentation' || data.mode === 'handout' || data.mode === 'note') {
            this._showSlides();
        } else {
            this._hideSlides();
        }
        // The view-mode radio group: keep visible (shows current mode and allows switching back)
    }
    // -----------------------------------------------------------------------
    // Visibility of the controls panel (toggled via keyboard / buttons)
    // -----------------------------------------------------------------------
    renderControls(visible) {
        if (this._controls instanceof HTMLElement) {
            this._controls.classList.toggle('controls-hidden', visible === false);
        }
    }
    // -----------------------------------------------------------------------
    // Private rendering helpers
    // -----------------------------------------------------------------------
    _renderSlide(newIndex, oldIndex) {
        const total = this._slides.length;
        for (let index = 0; index < total; index++) {
            const slide = this._slides[index];
            if (slide instanceof HTMLElement && index + 1 !== newIndex) {
                slide.removeAttribute('aria-selected');
            }
        }
        if (newIndex >= 1 && newIndex <= total) {
            const curr = this._slides[newIndex - 1];
            if (curr instanceof HTMLElement) {
                curr.setAttribute('aria-selected', 'true');
            }
        }
    }
    _renderIncremental(index, step) {
        const slide = this._getSlide(index);
        if (slide === null) {
            return;
        }
        // Clear all incremental state on this slide
        slide.querySelectorAll('.incremental').forEach(container => {
            container.removeAttribute('active');
            container.querySelectorAll('*').forEach(item => item.removeAttribute('aria-selected'));
        });
        if (step === 0) {
            return;
        }
        const items = slide.querySelectorAll('.incremental > *');
        if (items.length === 0 || step > items.length) {
            return;
        }
        const target = items[step - 1];
        if (target.parentElement instanceof HTMLElement) {
            target.parentElement.setAttribute('active', 'true');
        }
        target.setAttribute('aria-selected', 'true');
    }
    _renderProgress(currentIndex, count) {
        if (!(this._progressBar instanceof HTMLElement)) {
            return;
        }
        const pct = count <= 1 ? 0 : (currentIndex - 1) * 100 / (count - 1);
        this._progressBar.style.width = `${pct}%`;
    }
    _showSlides() {
        for (const slide of this._slides) {
            slide.style.display = '';
        }
    }
    _hideSlides() {
        for (const slide of this._slides) {
            slide.style.display = 'none';
        }
    }
    _getSlide(index) {
        if (index < 1 || index > this._slides.length) {
            return null;
        }
        return this._slides[index - 1];
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.PresentationView = PresentationView;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/overview_view.js ---------------
'use strict';
class OverviewView {
    constructor(slides, panelElement) {
        this._slides = Array.isArray(slides) ? slides : [];
        this._panel  = panelElement instanceof HTMLElement ? panelElement : null;
    }
    // -----------------------------------------------------------------------
    // Called once during init
    // -----------------------------------------------------------------------
    build() {
        if (this._panel === null) {
            return;
        }
        this._panel.innerHTML = '';
        this._panel.setAttribute('role', 'radiogroup');
        this._panel.setAttribute('aria-label', 'Slides overview');
        this._slides.forEach((slide, i) => {
            const index = i + 1;
            const id    = `overview-slide-${index}`;
            const radio = document.createElement('input');
            radio.type  = 'radio';
            radio.name  = 'overview-slide';
            radio.id    = id;
            radio.value = String(index);
            radio.addEventListener('change', () => {
                document.dispatchEvent(new CustomEvent('slides:navigate', {
                    detail: { action: 'goTo', index, step: 0 }
                }));
                document.dispatchEvent(new CustomEvent('slides:viewmode', {
                    detail: { mode: 'presentation' }
                }));
            });
            const numEl = document.createElement('span');
            numEl.className   = 'overview-num';
            numEl.textContent = String(index);
            const titleEl = document.createElement('span');
            titleEl.className   = 'overview-title';
            titleEl.textContent = this._slideTitle(slide);
            const label = document.createElement('label');
            label.className  = 'overview-btn';
            label.htmlFor    = id;
            label.appendChild(radio);
            label.appendChild(numEl);
            label.appendChild(titleEl);
            this._panel.appendChild(label);
        });
    }
    // -----------------------------------------------------------------------
    // Called by SlidesAssembler via navLogic.onNavigate
    // -----------------------------------------------------------------------
    render(data) {
        if (this._panel === null) {
            return;
        }
        const radios = this._panel.querySelectorAll('input[type="radio"]');
        radios.forEach((radio, i) => {
            radio.checked = (i + 1) === data.currentIndex;
        });
    }
    // -----------------------------------------------------------------------
    // Called by SlidesAssembler via modeLogic.onModeChange
    // -----------------------------------------------------------------------
    onModeChange(data) {
        if (this._panel === null) {
            return;
        }
        this._panel.style.display = data.mode === 'overview' ? '' : 'none';
        if (data.mode === 'overview') {
            this.render(data);
        }
    }
    // -----------------------------------------------------------------------
    // Private
    // -----------------------------------------------------------------------
    _slideTitle(slide) {
        const heading = slide.querySelector('h1, h2, h3, h4, h5, h6');
        return heading ? heading.textContent.trim() : '';
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.OverviewView = OverviewView;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/keyboard_controller.js ---------------
'use strict';
class SlidesKeyboard {
    // CONSTANTS
    static SHORTCUTS = [
        { keys: ['ArrowRight', 'ArrowDown', 'PageDown'], label: 'Next slide',
          event: 'slides:navigate', detail: { action: 'next' }, scrolls: true },
        { keys: ['ArrowLeft', 'ArrowUp', 'PageUp'],      label: 'Previous slide',
          event: 'slides:navigate', detail: { action: 'prev' }, scrolls: true },
        { keys: ['Home'],                                 label: 'First slide',
          event: 'slides:navigate', detail: { action: 'goStart' }, scrolls: true },
        { keys: ['End'],                                  label: 'Last slide',
          event: 'slides:navigate', detail: { action: 'goEnd' }, scrolls: true },
        { keys: ['h', 'H', '?'],                          label: 'Help',
          event: 'slides:help', detail: { action: 'toggle' } },
        { keys: ['f', 'F'],                               label: 'Fullscreen',
          event: 'slides:fullscreen', detail: {} },
        { keys: ['o', 'O'],                               label: 'Overview mode',
          event: 'slides:viewmode', detail: { action: 'toggle', mode: 'overview' } },
        { keys: ['d', 'D'],                               label: 'Handout mode',
          event: 'slides:viewmode', detail: { action: 'toggle', mode: 'handout' } },
        { keys: ['m', 'M'],                               label: 'Memo mode',
          event: 'slides:viewmode', detail: { action: 'toggle', mode: 'note' } },
        { keys: ['Escape', 's', 'S'],                     label: 'Presentation mode',
          event: 'slides:viewmode', detail: { mode: 'presentation' } },
        { keys: ['a', 'A'],                               label: 'Accessibility controls',
          event: 'slides:visibility', detail: { name: 'accessibility', action: 'toggle' } },
        { keys: ['n', 'N'],                               label: 'Navigation controls',
          event: 'slides:visibility', detail: { name: 'controls', action: 'toggle' } },
        { keys: ['b', 'B'],                               label: 'Progress bar',
          event: 'slides:visibility', detail: { name: 'progress', action: 'toggle' } },
        { keys: ['l', 'L'],                               label: 'Logo',
          event: 'slides:visibility', detail: { name: 'logo', action: 'toggle' } },
    ];
    // FIELDS
    #keyboard;
    // CONSTRUCTOR
    constructor() {
        this.#keyboard = new KeyboardController();
        SlidesKeyboard.SHORTCUTS.forEach(shortcut => {
            this.#keyboard.register({
                keys: shortcut.keys,
                action: shortcut.event,
                detail: shortcut.detail,
                label: shortcut.label,
                preventsDefault: shortcut.scrolls === true
            });
        });
    }
    // PUBLIC METHODS
    init() {
        this.#keyboard.init();
    }
    // -----------------------------------------------------------------------
    destroy() {
        this.#keyboard.destroy();
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.SlidesKeyboard = SlidesKeyboard;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/touch_controller.js ---------------
'use strict';
class TouchController {
    constructor(options = {}) {
        const target = options.target;
        this._target = target instanceof HTMLElement ? target : document.body;
        const threshold = options.threshold;
        this._threshold = typeof threshold === 'number' && threshold > 0 ? threshold : 100;
        this._tracking = false;
        this._originX  = 0;
        this._onStart = this._touchStart.bind(this);
        this._onMove  = this._touchMove.bind(this);
    }
    init() {
        this._target.addEventListener('touchstart', this._onStart, { passive: false });
        this._target.addEventListener('touchmove',  this._onMove,  { passive: false });
    }
    destroy() {
        this._target.removeEventListener('touchstart', this._onStart, false);
        this._target.removeEventListener('touchmove',  this._onMove,  false);
    }
    // -----------------------------------------------------------------------
    // Private
    // -----------------------------------------------------------------------
    _touchStart(event) {
        if (event.changedTouches.length === 0) {
            return;
        }
        event.preventDefault();
        this._tracking = true;
        this._originX  = event.changedTouches[0].pageX;
    }
    _touchMove(event) {
        if (!this._tracking || event.changedTouches.length === 0) {
            return;
        }
        const delta = this._originX - event.changedTouches[0].pageX;
        if (delta > this._threshold) {
            this._tracking = false;
            document.dispatchEvent(new CustomEvent('slides:navigate', {
                detail: { action: 'next' }
            }));
        } else if (delta < -this._threshold) {
            this._tracking = false;
            document.dispatchEvent(new CustomEvent('slides:navigate', {
                detail: { action: 'prev' }
            }));
        }
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.TouchController = TouchController;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/buttons_controller.js ---------------
'use strict';
class ButtonsController {
    constructor({
        prevButton         = null,
        nextButton         = null,
        backButton         = null,
        lastButton         = null,
        overviewButton     = null,
        handoutButton      = null,
        noteButton         = null,
        presentationButton = null,
        fullscreenButton   = null,
        goToButton         = null,
    } = {}) {
        this._b = {
            prev:         this._el(prevButton),
            next:         this._el(nextButton),
            back:         this._el(backButton),
            last:         this._el(lastButton),
            overview:     this._el(overviewButton),
            handout:      this._el(handoutButton),
            note:         this._el(noteButton),
            presentation: this._el(presentationButton),
            fullscreen:   this._el(fullscreenButton),
            goto:         this._el(goToButton),
        };
        this._bindEvents();
    }
    // -----------------------------------------------------------------------
    // Called by SlidesAssembler via modeLogic.onModeChange
    // -----------------------------------------------------------------------
    onModeChange(data) {
        if (this._b.overview instanceof HTMLElement) {
            this._b.overview.checked = (data.mode === 'overview');
        }
        if (this._b.handout instanceof HTMLElement) {
            this._b.handout.checked = (data.mode === 'handout');
        }
        if (this._b.note instanceof HTMLElement) {
            this._b.note.checked = (data.mode === 'note');
        }
        if (this._b.presentation instanceof HTMLElement) {
            this._b.presentation.checked = (data.mode === 'presentation');
        }
    }
    // -----------------------------------------------------------------------
    // Private
    // -----------------------------------------------------------------------
    _bindEvents() {
        const b = this._b;
        const nav  = (action, index, step) =>
            document.dispatchEvent(new CustomEvent('slides:navigate', {
                detail: { action, index, step }
            }));
        const mode = (m) =>
            document.dispatchEvent(new CustomEvent('slides:viewmode', {
                detail: { mode: m }
            }));
        b.prev?.addEventListener('click',     () => nav('prev'));
        b.next?.addEventListener('click',     () => nav('next'));
        b.back?.addEventListener('click',     () => nav('goStart'));
        b.last?.addEventListener('click',     () => nav('goEnd'));
        b.overview?.addEventListener('change', () => mode('overview'));
        b.handout?.addEventListener('change',  () => mode('handout'));
        b.note?.addEventListener('change',     () => mode('note'));
        b.presentation?.addEventListener('change', () => mode('presentation'));
        b.fullscreen?.addEventListener('click', () =>
            document.dispatchEvent(new CustomEvent('slides:fullscreen', { detail: {} }))
        );
        b.goto?.addEventListener('click', () => {
            const input = window.prompt('Go to slide number:');
            if (input !== null) {
                nav('goTo', Number(input), 0);
                mode('presentation');
            }
        });
    }
    _el(e) {
        return e instanceof HTMLElement ? e : null;
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.ButtonsController = ButtonsController;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/note_view.js ---------------
'use strict';
class NoteView {
    constructor(slides) {
        this._slides     = Array.isArray(slides) ? slides : [];
        this._containers = [];
    }
    onModeChange(data) {
        if (data.mode === 'note') {
            this._build();
        } else {
            this._teardown();
        }
    }
    // -----------------------------------------------------------------------
    // Private
    // -----------------------------------------------------------------------
    _build() {
        if (this._containers.length > 0) {
            return;
        }
        for (const slide of this._slides) {
            const aside = slide.id
                ? document.querySelector(`aside[for="${slide.id}"]`)
                : null;
            const container = document.createElement('div');
            container.className = 'note-container';
            slide.parentNode.insertBefore(container, slide);
            container.appendChild(slide);
            if (aside instanceof HTMLElement) {
                container.appendChild(aside);
            }
            this._containers.push(container);
        }
    }
    _teardown() {
        if (this._containers.length === 0) {
            return;
        }
        for (const container of this._containers) {
            const parent = container.parentNode;
            if (!(parent instanceof HTMLElement)) {
                continue;
            }
            while (container.firstChild) {
                parent.insertBefore(container.firstChild, container);
            }
            parent.removeChild(container);
        }
        this._containers = [];
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.NoteView = NoteView;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/help_dialog.js ---------------
'use strict';
const DIALOG_ID = 'slides-help-dialog';
class HelpDialog {
    constructor() {
        this._manager = new DialogManager();
        this._inject();
    }
    toggle() {
        const dialog = document.getElementById(DIALOG_ID);
        if (dialog && dialog.open) {
            this._manager.close(DIALOG_ID);
        } else {
            this._manager.open(DIALOG_ID, true);
        }
    }
    // -----------------------------------------------------------------------
    // Private
    // -----------------------------------------------------------------------
    _inject() {
        if (document.getElementById(DIALOG_ID)) return;
        document.body.appendChild(this._build());
    }
    _build() {
        const dialog = document.createElement('dialog');
        dialog.id = DIALOG_ID;
        dialog.setAttribute('role', 'alertdialog');
        dialog.setAttribute('aria-label', 'Keyboard shortcuts');
        dialog.classList.add('tips', 'hidden-alert');
        const div = document.createElement('div');
        const h2 = document.createElement('h2');
        h2.textContent = 'Keyboard shortcuts';
        div.appendChild(h2);
        const table = document.createElement('table');
        table.setAttribute('role', 'presentation');
        for (const { keys, label } of SlidesKeyboard.SHORTCUTS) {
            const tr = document.createElement('tr');
            const tdKeys = document.createElement('td');
            tdKeys.textContent = keys.map(k => this._keyLabel(k)).join(' / ');
            const tdLabel = document.createElement('td');
            tdLabel.textContent = label;
            tr.appendChild(tdKeys);
            tr.appendChild(tdLabel);
            table.appendChild(tr);
        }
        div.appendChild(table);
        dialog.appendChild(div);
        return dialog;
    }
    _keyLabel(key) {
        const map = {
            ArrowRight: '→', ArrowLeft: '←', ArrowUp: '↑', ArrowDown: '↓',
            PageUp: 'PgUp', PageDown: 'PgDn',
            Home: 'Home', End: 'End', Escape: 'Esc',
        };
        return map[key] ?? key;
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.HelpDialog = HelpDialog;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/slide_reaching.js ---------------
'use strict';
class SlideReaching {
    // FIELDS
    _data
    _navigation
    // CONSTRUCTOR
    constructor(data, navigation) {
        this._data = data;
        this._navigation = navigation;
    }
    // ----------------------------------------------------------------------
    // PUBLIC
    // ----------------------------------------------------------------------
    supportOf(place) {
        if (typeof place !== 'string' || place === '') {
            return 0;
        }
        const element = document.getElementById(place);
        if (element === null) {
            return 0;
        }
        const supports = this._data.slides;
        for (let index = 0; index < supports.length; index++) {
            if (supports[index].contains(element) === true) {
                return index + 1;
            }
        }
        return 0;
    }
    // ----------------------------------------------------------------------
    reach(place) {
        const rank = this.supportOf(place);
        if (rank === 0) {
            return 0;
        }
        this._navigation.goTo(rank);
        return rank;
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.SlideReaching = SlideReaching;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/slides_assembler.js ---------------
'use strict';
class SlidesAssembler {
    constructor(config) {
        // ── 1. DATA ──────────────────────────────────────────────────────────
        this._data = new SlidesData(config.slides);
        this._data.autoPlay = Boolean(config.autoPlayEnabled);
        // ── 2. LOGIC ─────────────────────────────────────────────────────────
        this._navLogic  = new NavigationLogic(this._data);
        this._modeLogic = new ViewModeLogic(this._data);
        this._reaching  = new SlideReaching(this._data, this._navLogic);
        // ── 3. VIEWS ─────────────────────────────────────────────────────────
        this._presentationView = new PresentationView(
            config.slides,
            config.progressBar   instanceof HTMLElement ? config.progressBar   : null,
            config.controls      instanceof HTMLElement ? config.controls      : null,
            config.controlsView  instanceof HTMLElement ? config.controlsView  : null
        );
        this._overviewView = config.overviewContainer instanceof HTMLElement
            ? new OverviewView(config.slides, config.overviewContainer)
            : null;
        this._noteView = new NoteView(config.slides);
        // ── 4. UTILITIES ─────────────────────────────────────────────────────
        this._focus      = new SlidesFocusController();
        this._fullscreen = new SlidesFullscreenController();
        this._visibilityManager = new SlidesVisibilityManager({
            accessibility: config.accessibility       instanceof HTMLElement ? config.accessibility       : null,
            controls:      config.controls            instanceof HTMLElement ? config.controls            : null,
            progress:      config.progressBarContainer instanceof HTMLElement ? config.progressBarContainer : null,
            logo:          config.logo                instanceof HTMLElement ? config.logo                : null,
        });
        // ── 5. CONTROLLERS ───────────────────────────────────────────────────
        this._helpDialog = new HelpDialog();
        this._keyboard = new SlidesKeyboard();
        this._touch    = new TouchController();
        const c = config.controls;
        const v = config.controlsView;
        this._buttons = new ButtonsController({
            prevButton:         c?.querySelector('#btn-prev')         || null,
            nextButton:         c?.querySelector('#btn-next')         || null,
            backButton:         c?.querySelector('#btn-back')         || null,
            lastButton:         c?.querySelector('#btn-last')         || null,
            goToButton:         c?.querySelector('#btn-goto')         || null,
            overviewButton:     v?.querySelector('#btn-overview')     || null,
            handoutButton:      v?.querySelector('#btn-handout')      || null,
            noteButton:         v?.querySelector('#btn-note')         || null,
            presentationButton: v?.querySelector('#btn-presentation') || null,
            fullscreenButton:   c?.querySelector('#btn-fullscreen')   || null,
        });
        // ── 6. WIRE LOGIC → VIEWS (callbacks) ────────────────────────────────
        this._navLogic.onNavigate = (data) => {
            this._presentationView.render(data);
            this._focus.updateFocus(data.slides, data.currentIndex);
            if (this._overviewView !== null) {
                this._overviewView.render(data);
            }
        };
        this._modeLogic.onModeChange = (data) => {
            this._noteView.onModeChange(data);
            this._presentationView.onModeChange(data);
            if (this._overviewView !== null) {
                this._overviewView.onModeChange(data);
            }
            this._buttons.onModeChange(data);
        };
        // ── 7. WIRE CUSTOM EVENTS → LOGIC ────────────────────────────────────
        document.addEventListener('slides:navigate', (e) => {
            this._dispatch(e.detail);
        });
        document.addEventListener('slides:viewmode', (e) => {
            const { mode, action } = e.detail;
            if (action === 'toggle') { this._modeLogic.toggle(mode); }
            else { this._modeLogic.set(mode); }
        });
        document.addEventListener('slides:visibility', (e) => {
            const { name, action } = e.detail;
            if (action === 'toggle') { this._visibilityManager.toggle(name); }
            else if (action === 'show')   { this._visibilityManager.show(name);   }
            else if (action === 'hide')   { this._visibilityManager.hide(name);   }
        });
        document.addEventListener('slides:fullscreen', () => {
            this._fullscreen.toggle();
        });
        document.addEventListener('slides:help', () => {
            this._helpDialog.toggle();
        });
        // ── 8. HASH CHANGE ───────────────────────────────────────────────────
        window.addEventListener('hashchange', () => {
            this._navLogic.updateFromHash(window.location.hash);
        });
        // ── 8b. RENVOI FOLLOWED ──────────────────────────────────────────────
        // A renvoi names a place, never a position. The browser would write
        // that name in the address, where the reading stands: the request is
        // taken before it does, and the support carrying the place is asked
        // for instead.
        document.addEventListener('click', (event) => {
            const link = event.target.closest('a[href^="#"]');
            if (link === null) {
                return;
            }
            const place = link.getAttribute('href').substring(1);
            if (this._reaching.supportOf(place) === 0) {
                return;
            }
            event.preventDefault();
            this._reaching.reach(place);
        });
        // ── 9. INITIAL MODE ──────────────────────────────────────────────────
        this._initialMode = ViewModeLogic.DEFAULT;
        if (typeof config.mode === 'string') {
            const modes = Object.values(ViewModeLogic.MODES);
            if (modes.includes(config.mode)) {
                this._initialMode = config.mode;
            }
        }
    }
    // -----------------------------------------------------------------------
    // Public API
    // -----------------------------------------------------------------------
    init() {
        // Build overview panel (before any mode is applied)
        if (this._overviewView !== null) {
            this._overviewView.build();
        }
        // Apply initial mode (fires onModeChange → updates views + buttons)
        this._modeLogic.set(this._initialMode);
        // Navigate to position from URL hash (fires onNavigate → renders)
        this._navLogic.updateFromHash(window.location.hash);
        // Start input controllers
        this._keyboard.init();
        this._touch.init();
    }
    get fullscreen() {
        return this._fullscreen;
    }
    // -----------------------------------------------------------------------
    // Private
    // -----------------------------------------------------------------------
    _dispatch(detail) {
        const { action, index, step } = detail;
        switch (action) {
            case 'next':          this._navLogic.next();                           break;
            case 'prev':          this._navLogic.prev();                           break;
            case 'goStart':       this._navLogic.goStart();                        break;
            case 'goEnd':         this._navLogic.goEnd();                          break;
            case 'goTo':          this._navLogic.goTo(Number(index) || 1, Number(step) || 0); break;
            case 'toggleContent': this._navLogic.toggleContent();                  break;
        }
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.SlidesAssembler = SlidesAssembler;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/slides.js ---------------
'use strict';
class Slides {
    constructor(config = {}) {
        // --- Normalize configuration -----------------------------------------
        // We guarantee that "slides" is ALWAYS a true Array.
        // If user gives a NodeList, we convert it.
        // If user gives null/undefined, we use an empty Array.
        // Internal classes never need to question it.
        // ---------------------------------------------------------------------
        let slidesArray = [];
        if (Array.isArray(config.slides)) {
            slidesArray = config.slides;
        } else if (config.slides && typeof config.slides.length === 'number') {
            // NodeList or HTMLCollection
            slidesArray = Array.from(config.slides);
        } else {
            console.error('Slides: "slides" was not a valid list. Using [].');
            slidesArray = [];
        }
        const cleanedConfig = {
            ...config,
            slides: slidesArray
        };
        // --- Instantiate the internal application -----------------------------
        this._app = new SlidesAssembler(cleanedConfig);
    }
    init() {
        this._app.init();
    }
    get fullscreen() {
        return this._app.fullscreen;
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.Slides = Slides;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/slide_errors.js ---------------
'use strict';
class PaginationError extends Error {
}
class MissingSlide extends PaginationError {
}
class UnmeasurableSlide extends PaginationError {
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.PaginationError = PaginationError;
window.Wexa.MissingSlide = MissingSlide;
window.Wexa.UnmeasurableSlide = UnmeasurableSlide;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/slide_block.js ---------------
'use strict';
class SlideBlock {
    // FIELDS
    #element;
    #place;
    #height;
    // CONSTRUCTOR
    constructor(element, place) {
        this.#element = element;
        this.#place = place;
        this.#height = 0;
    }
    // GETTERS
    get element() {
        return this.#element;
    }
    get place() {
        return this.#place;
    }
    get height() {
        return this.#height;
    }
    // SETTERS
    set height(value) {
        this.#height = value;
    }
    // PUBLIC METHODS
    fitsIn(room) {
        return this.#height <= room;
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.SlideBlock = SlideBlock;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/slide_layout.js ---------------
'use strict';
class SlideLayout {
    // FIELDS
    #parts;
    // CONSTRUCTOR
    constructor(parts) {
        this.#parts = parts.map(part => [...part]);
    }
    // GETTERS
    get parts() {
        return this.#parts.map(part => [...part]);
    }
    // PUBLIC METHODS
    count() {
        return this.#parts.length;
    }
    oversized(room) {
        const found = [];
        this.#parts.forEach(part => {
            part.forEach(block => {
                if (block.fitsIn(room) === false) {
                    found.push(block);
                }
            });
        });
        return found;
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.SlideLayout = SlideLayout;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/slide_block_reader.js ---------------
'use strict';
class SlideBlockReader {
    // CONSTANTS
    static KEPT_APART = 'h1, h2, h3, h4, h5, h6, [role="note"]';
    static READ_AS_ROWS = 'TABLE';
    static READ_AS_ITEMS = ['UL', 'OL'];
    // PUBLIC METHODS
    blocks(slide) {
        const found = [];
        Array.from(slide.children).forEach(child => {
            this.#readChild(child).forEach(element => {
                found.push(new SlideBlock(element, found.length + 1));
            });
        });
        return found;
    }
    // PRIVATE METHODS
    #readChild(child) {
        if (child.matches(SlideBlockReader.KEPT_APART) === true) {
            return [];
        }
        if (child.tagName === SlideBlockReader.READ_AS_ROWS) {
            return this.#rowsOf(child);
        }
        if (SlideBlockReader.READ_AS_ITEMS.includes(child.tagName) === true) {
            return Array.from(child.children);
        }
        if (this.#holdsParts(child) === true) {
            const parts = [];
            Array.from(child.children).forEach(held => {
                this.#readChild(held).forEach(element => parts.push(element));
            });
            return parts;
        }
        return [child];
    }
    #holdsParts(child) {
        return Array.from(child.children).some(held => {
            return held.tagName === SlideBlockReader.READ_AS_ROWS
                || SlideBlockReader.READ_AS_ITEMS.includes(held.tagName) === true;
        });
    }
    #rowsOf(table) {
        const bodies = Array.from(table.tBodies);
        if (bodies.length === 0) {
            return Array.from(table.rows);
        }
        const rows = [];
        bodies.forEach(body => {
            Array.from(body.rows).forEach(row => rows.push(row));
        });
        return rows;
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.SlideBlockReader = SlideBlockReader;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/slide_measure.js ---------------
'use strict';
class SlideMeasure {
    // CONSTANTS
    static TITLE = 'h1, h2, h3, h4, h5, h6';
    static SLIDE = 'section.slide';
    // PUBLIC METHODS
    room(slide, blocks) {
        if (slide === null || slide === undefined || typeof slide.matches !== 'function') {
            throw new MissingSlide('The element to measure is not an element of the document.');
        }
        if (slide.matches(SlideMeasure.SLIDE) === false) {
            throw new MissingSlide('The element to measure is not a slide.');
        }
        const box = slide.getBoundingClientRect();
        if (box.height === 0) {
            throw new UnmeasurableSlide('The slide has no height: it is not rendered.');
        }
        const style = window.getComputedStyle(slide);
        const inside = box.height
            - parseFloat(style.paddingTop)
            - parseFloat(style.paddingBottom)
            - parseFloat(style.borderTopWidth)
            - parseFloat(style.borderBottomWidth);
        return inside - this.#counterHeight(slide) - this.#aroundHeight(slide, blocks);
    }
    measure(blocks, slide) {
        blocks.forEach(block => {
            block.height = this.#heightOf(block.element);
        });
    }
    // PRIVATE METHODS
    #aroundHeight(slide, blocks) {
        let held = 0;
        Array.from(slide.children).forEach(child => {
            held = held + this.#heightOf(child);
        });
        let laid = 0;
        blocks.forEach(block => {
            laid = laid + block.height;
        });
        return Math.max(0, held - laid);
    }
    #counterHeight(slide) {
        const counter = window.getComputedStyle(slide, ':before');
        const height = parseFloat(counter.height);
        if (isNaN(height) === true) {
            return 0;
        }
        return height;
    }
    #heightOf(element) {
        const box = element.getBoundingClientRect();
        const style = window.getComputedStyle(element);
        return box.height + parseFloat(style.marginTop) + parseFloat(style.marginBottom);
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.SlideMeasure = SlideMeasure;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/slide_paginator.js ---------------
'use strict';
class SlidePaginator {
    // PUBLIC METHODS
    paginate(blocks, room) {
        if (blocks.length === 0) {
            return new SlideLayout([[]]);
        }
        const parts = [];
        let current = [];
        let left = room;
        blocks.forEach(block => {
            const opensASlide = (current.length > 0 && block.fitsIn(left) === false);
            if (opensASlide === true) {
                parts.push(current);
                current = [];
                left = room;
            }
            current.push(block);
            left = left - block.height;
        });
        parts.push(current);
        return new SlideLayout(parts);
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.SlidePaginator = SlidePaginator;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/slide_composer.js ---------------
'use strict';
class SlideComposer {
    // PUBLIC METHODS
    compose(slide, layout) {
        const parts = layout.parts;
        const slides = [slide];
        for (let rank = 1; rank < parts.length; rank++) {
            const next = this.#buildSlide(slide);
            this.#lay(next, parts[rank]);
            slides[slides.length - 1].after(next);
            slides.push(next);
        }
        return slides;
    }
    // PRIVATE METHODS
    #buildSlide(source) {
        const next = document.createElement(source.tagName);
        next.className = source.className;
        return next;
    }
    #lay(next, blocks) {
        let group = [];
        let parent = null;
        blocks.forEach(block => {
            const holder = block.element.parentElement;
            if (holder !== parent && group.length > 0) {
                this.#layGroup(next, parent, group);
                group = [];
            }
            parent = holder;
            group.push(block.element);
        });
        if (group.length > 0) {
            this.#layGroup(next, parent, group);
        }
    }
    #layGroup(next, parent, elements) {
        if (parent === null) {
            elements.forEach(element => next.appendChild(element));
            return;
        }
        if (parent.tagName === 'TBODY') {
            next.appendChild(this.#rebuildTable(parent, elements));
            return;
        }
        if (parent.tagName === 'UL' || parent.tagName === 'OL') {
            next.appendChild(this.#rebuildList(parent, elements));
            return;
        }
        elements.forEach(element => next.appendChild(element));
    }
    #rebuildTable(body, rows) {
        const source = body.closest('table');
        const table = source.cloneNode(false);
        const head = source.querySelector('thead');
        if (head !== null) {
            table.appendChild(head.cloneNode(true));
        }
        const next = document.createElement('tbody');
        rows.forEach(row => next.appendChild(row));
        table.appendChild(next);
        return table;
    }
    #rebuildList(source, items) {
        const list = source.cloneNode(false);
        items.forEach(item => list.appendChild(item));
        return list;
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.SlideComposer = SlideComposer;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/slides/slides_pagination.js ---------------
'use strict';
class SlidesPagination {
    // CONSTANTS
    static SLIDES = 'section.slide';
    // FIELDS
    #reader;
    #measure;
    #paginator;
    #composer;
    // CONSTRUCTOR
    constructor() {
        this.#reader = new SlideBlockReader();
        this.#measure = new SlideMeasure();
        this.#paginator = new SlidePaginator();
        this.#composer = new SlideComposer();
    }
    // PUBLIC METHODS
    async run() {
        try {
            const written = Array.from(document.querySelectorAll(SlidesPagination.SLIDES));
            written.forEach(slide => this.#layOut(slide));
        } catch (error) {
            if (error instanceof PaginationError) {
                console.error('SlidesPagination: ' + error.message);
                return;
            }
            throw error;
        }
    }
    // PRIVATE METHODS
    #layOut(slide) {
        const blocks = this.#reader.blocks(slide);
        if (blocks.length === 0) {
            return;
        }
        this.#measure.measure(blocks, slide);
        const room = this.#measure.room(slide, blocks);
        const layout = this.#paginator.paginate(blocks, room);
        this.#report(layout.oversized(room));
        if (layout.count() === 1) {
            return;
        }
        // The blocks are laid down once, in the order they were written. What
        // was measured is what is shown, so what was decided holds: laying a
        // slide out a second time would cut again on a difference of a pixel,
        // and leave a slide holding one block.
        this.#composer.compose(slide, layout);
    }
    #report(blocks) {
        blocks.forEach(block => {
            console.warn('SlidesPagination: a block is taller than the slide, and overflows.',
                block.element);
        });
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.SlidesPagination = SlidesPagination;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- dom-loader.js ---------------
'use strict';
class OnLoadManager {
    static #functions = [];
    static #listening = false;
    // -----------------------------------------------------------------------
    static addLoadFunction(func) {
        if (typeof func !== 'function') {
            return;
        }
        if (document.readyState === 'complete') {
            func();
            return;
        }
        OnLoadManager.#functions.push(func);
        OnLoadManager.#listen();
    }
    // -----------------------------------------------------------------------
    static runLoadFunctions() {
        for (const func of OnLoadManager.#functions) {
            func();
        }
    }
    // -----------------------------------------------------------------------
    // PRIVATE
    // -----------------------------------------------------------------------
    static #listen() {
        if (OnLoadManager.#listening === true) {
            return;
        }
        OnLoadManager.#listening = true;
        window.addEventListener('load', OnLoadManager.runLoadFunctions);
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.OnLoadManager = OnLoadManager;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- accessibility.js ---------------
class AccessibilityManager extends BaseManager {
    // -----------------------------------------------------------------------
    // FIELDS
    // -----------------------------------------------------------------------
    #activatedColor;
    #activatedContrast;
    #colorModeSuspendedForPaper;
    // -----------------------------------------------------------------------
    // CONSTRUCTOR
    // -----------------------------------------------------------------------
    constructor() {
        super();
        this.#activatedColor = "";
        this.#activatedContrast = "";
        this.#colorModeSuspendedForPaper = false;
        OnLoadManager.addLoadFunction(this.#loadBodyClasses.bind(this));
        OnLoadManager.addLoadFunction(this.#setAllLinksCustom.bind(this));
        OnLoadManager.addLoadFunction(this.#setSubmitCustom.bind(this));
        OnLoadManager.addLoadFunction(this.#injectButtonIcons.bind(this));
        // Paper is light. Held here rather than in every stylesheet, so that a
        // theme never has to know that printing exists.
        window.addEventListener('beforeprint', this.#leaveColorModeForPaper.bind(this));
        window.addEventListener('afterprint', this.#restoreColorModeAfterPaper.bind(this));
    }
    // -----------------------------------------------------------------------
    // STATIC CONSTANTS
    // -----------------------------------------------------------------------
    static get COLOR_MODE()              { return "dark"; }
    static get CONTRAST_MODE()           { return "contrast"; }
    static get COLOR_PARAMETER_NAME()    { return "wexa_color"; }
    static get CONTRAST_PARAMETER_NAME() { return "wexa_contrast"; }
    // -----------------------------------------------------------------------
    // GETTERS
    // -----------------------------------------------------------------------
    get activatedColorMode() {
        return this.#activatedColor;
    }
    // -----------------------------------------------------------------------
    get activatedContrastMode() {
        return this.#activatedContrast;
    }
    // -----------------------------------------------------------------------
    // PUBLIC METHODS
    // -----------------------------------------------------------------------
    async switchColorScheme() {
        if (this.#activatedColor === "") {
            this.#activatedColor = AccessibilityManager.COLOR_MODE;
            document.documentElement.classList.add(AccessibilityManager.COLOR_MODE);
        } else {
            this.#activatedColor = "";
            document.documentElement.classList.remove(AccessibilityManager.COLOR_MODE);
        }
        this.#updateButtonState('btn-color');
        this.#updateUrl();
        await this.postEvents({"accessibility_color": this.#activatedColor});
    }
    // -----------------------------------------------------------------------
    async switchContrastScheme() {
        if (this.#activatedContrast === "") {
            this.#activatedContrast = AccessibilityManager.CONTRAST_MODE;
            document.documentElement.classList.add(AccessibilityManager.CONTRAST_MODE);
        } else {
            this.#activatedContrast = "";
            document.documentElement.classList.remove(AccessibilityManager.CONTRAST_MODE);
        }
        this.#updateButtonState('btn-contrast');
        this.#updateUrl();
        await this.postEvents({"accessibility_contrast": this.#activatedContrast});
    }
    // -----------------------------------------------------------------------
    goToLink(element, openInNewTab = false) {
        const rawHref = element.getAttribute('href');
        if (rawHref === null || rawHref === '') {
            return;
        }
        const url = new URL(element.href, window.location.href);
        let targetUrl;
        if (window.location.protocol !== 'file:' && (window.location.hostname === 'localhost' || url.host === window.location.host)) {
            targetUrl = this.setUrlWithParameters(url.href);
        } else {
            targetUrl = url.href;
        }
        if (openInNewTab === true) {
            window.open(targetUrl, '_blank', 'noopener');
            return;
        }
        document.location.href = targetUrl;
    }
    // -----------------------------------------------------------------------
    setUrlWithParameters(url) {
        if (url === null || url === '') {
            return '';
        }
        const customUrl = new URL(url, window.location.href);
        // Forward only the parameters this framework owns ("wexa_" prefix,
        // e.g. wexa_theme) so that they survive cross-page navigation.
        // Application parameters are not forwarded, and a parameter already
        // present in the target URL is never overwritten: the caller's
        // explicit intent wins over the ambient state.
        const currentParams = new URLSearchParams(window.location.search);
        for (const [key, value] of currentParams) {
            if (key.startsWith('wexa_') === false) {
                continue;
            }
            if (customUrl.searchParams.has(key) === true) {
                continue;
            }
            customUrl.searchParams.set(key, value);
        }
        if (this.#activatedColor !== '') {
            customUrl.searchParams.set(AccessibilityManager.COLOR_PARAMETER_NAME, this.#activatedColor);
        } else {
            customUrl.searchParams.delete(AccessibilityManager.COLOR_PARAMETER_NAME);
        }
        if (this.#activatedContrast !== '') {
            customUrl.searchParams.set(AccessibilityManager.CONTRAST_PARAMETER_NAME, this.#activatedContrast);
        } else {
            customUrl.searchParams.delete(AccessibilityManager.CONTRAST_PARAMETER_NAME);
        }
        return customUrl.href;
    }
    // -----------------------------------------------------------------------
    // PRIVATE METHODS
    // -----------------------------------------------------------------------
    #leaveColorModeForPaper() {
        if (this.#activatedColor === "") {
            return;
        }
        document.documentElement.classList.remove(AccessibilityManager.COLOR_MODE);
        this.#colorModeSuspendedForPaper = true;
    }
    // -----------------------------------------------------------------------
    #restoreColorModeAfterPaper() {
        if (this.#colorModeSuspendedForPaper === false) {
            return;
        }
        document.documentElement.classList.add(AccessibilityManager.COLOR_MODE);
        this.#colorModeSuspendedForPaper = false;
    }
    // -----------------------------------------------------------------------
    async #loadBodyClasses() {
        const params = new URLSearchParams(window.location.search);
        const events = {};
        if (params.has(AccessibilityManager.COLOR_PARAMETER_NAME)) {
            const colorParam = params.get(AccessibilityManager.COLOR_PARAMETER_NAME).toLowerCase();
            if (colorParam === AccessibilityManager.COLOR_MODE) {
                this.#activatedColor = colorParam;
                document.documentElement.classList.add(colorParam);
                events.accessibility_color = this.#activatedColor;
            } else {
                console.log(AccessibilityManager.COLOR_PARAMETER_NAME + " unknown value: " + colorParam);
            }
        }
        if (params.has(AccessibilityManager.CONTRAST_PARAMETER_NAME)) {
            const contrastParam = params.get(AccessibilityManager.CONTRAST_PARAMETER_NAME).toLowerCase();
            if (contrastParam === AccessibilityManager.CONTRAST_MODE) {
                this.#activatedContrast = contrastParam;
                document.documentElement.classList.add(contrastParam);
                events.accessibility_contrast = this.#activatedContrast;
            } else {
                console.log(AccessibilityManager.CONTRAST_PARAMETER_NAME + " unknown value: " + contrastParam);
            }
        }
        if (Object.keys(events).length > 0) {
            await this.postEvents(events);
        }
    }
    // -----------------------------------------------------------------------
    #setAllLinksCustom() {
        let linkElements = Array.from(document.querySelectorAll("a"));
        linkElements = linkElements.filter(el => el.href !== null && el.href !== '');
        linkElements.forEach(element => {
            element.addEventListener("click", event => {
                event.preventDefault();
                const namedTarget = element.dataset.namedTarget;
                if (typeof namedTarget === 'string' && namedTarget.length > 0) {
                    this.#goToNamedTab(element, namedTarget);
                    return;
                }
                this.goToLink(element, element.target === '_blank');
            });
        });
    }
    // -----------------------------------------------------------------------
    #goToNamedTab(element, name) {
        const rawHref = element.getAttribute('href');
        if (rawHref === null || rawHref === '') {
            return;
        }
        const url = new URL(element.href, window.location.href);
        let targetUrl;
        if (window.location.protocol !== 'file:' && (window.location.hostname === 'localhost' || url.host === window.location.host)) {
            targetUrl = this.setUrlWithParameters(url.href);
        } else {
            targetUrl = url.href;
        }
        window.open(targetUrl, name);
    }
    // -----------------------------------------------------------------------
    #setSubmitCustom() {
        const submitButton = document.querySelector('button[type="submit"]');
        if (!submitButton) return;
        submitButton.addEventListener('click', () => {
            const form = document.querySelector('form');
            if (form) {
                form.action = this.setUrlWithParameters(form.action);
            }
        });
    }
    // -----------------------------------------------------------------------
    async #injectButtonIcons() {
        await icons.inject(document.getElementById('btn-contrast'), 'contrast');
        await icons.inject(document.getElementById('btn-color'), 'color');
    }
    // -----------------------------------------------------------------------
    #updateUrl() {
        history.replaceState(null, '', this.setUrlWithParameters(window.location.href));
    }
    // -----------------------------------------------------------------------
    #updateButtonState(buttonId) {
        const btn = document.getElementById(buttonId);
        if (btn === null) { console.error(`Button not found: ${buttonId}.`); return; }
        let pressed = false;
        if (buttonId === 'btn-contrast') { pressed = this.#activatedContrast !== ''; }
        else if (buttonId === 'btn-color') { pressed = this.#activatedColor !== ''; }
        else { console.error(`Unknown button id: ${buttonId}.`); return; }
        btn.setAttribute('aria-pressed', String(pressed));
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.AccessibilityManager = AccessibilityManager;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- accessibility_nav.js ---------------
'use strict';
const NAV_WORDING = {
    theme: { label: 'Switch theme', title: 'Switch theme' },
    contrast: { label: 'Switch contrast', title: 'Switch contrast' },
    color: { label: 'Switch light and dark', title: 'Switch light and dark' }
};
class AccessibilityNav {
    #shown;
    constructor(shown = {}) {
        this.#shown = {
            theme: shown.theme !== false,
            contrast: shown.contrast !== false,
            color: shown.color !== false
        };
    }
    // -----------------------------------------------------------------------
    async build(options = {}) {
        const nav = document.createElement('nav');
        nav.id = options.id !== undefined ? options.id : 'accessibility-controls';
        nav.className = options.className !== undefined
            ? options.className
            : 'nav-wexa';
        nav.setAttribute('aria-label', options.label !== undefined
            ? options.label
            : 'Accessibility controls');
        if (this.#shown.theme === true) {
            const wording = this.#wordingOf(options, 'theme');
            nav.appendChild(await this.#button(
                'btn-css-theme', 'menuitem', 'theme', wording.label,
                () => {
                    if (window.themes !== null && window.themes !== undefined) {
                        window.themes.next();
                    }
                },
                { title: wording.title }));
        }
        if (this.#shown.contrast === true) {
            const wording = this.#wordingOf(options, 'contrast');
            nav.appendChild(await this.#button(
                'btn-contrast', 'menuitem accessibility', 'contrast', wording.label,
                () => this.#accessibility('switchContrastScheme'),
                { ariaPressed: 'false', title: wording.title }));
        }
        if (this.#shown.color === true) {
            const wording = this.#wordingOf(options, 'color');
            nav.appendChild(await this.#button(
                'btn-color', 'menuitem accessibility', 'color', wording.label,
                () => this.#accessibility('switchColorScheme'),
                { ariaPressed: 'false', title: wording.title }));
        }
        return nav;
    }
    // -----------------------------------------------------------------------
    // PRIVATE
    // -----------------------------------------------------------------------
    #wordingOf(options, which) {
        const proposed = NAV_WORDING[which];
        const said = options.wording !== undefined ? options.wording[which] : undefined;
        if (said === undefined || said === null) {
            return { label: proposed.label, title: proposed.title };
        }
        const label = said.label !== undefined ? said.label : proposed.label;
        const title = said.title !== undefined ? said.title : proposed.title;
        return { label: label, title: title };
    }
    // -----------------------------------------------------------------------
    async #button(id, className, iconName, ariaLabel, onClick, extras = {}) {
        const button = document.createElement('button');
        button.type = 'button';
        button.id = id;
        button.className = className;
        button.setAttribute('aria-label', ariaLabel);
        if (extras.ariaPressed !== undefined) {
            button.setAttribute('aria-pressed', extras.ariaPressed);
        }
        if (extras.title !== undefined) {
            button.title = extras.title;
        }
        button.innerHTML = await icons.get(iconName);
        button.addEventListener('click', onClick);
        return button;
    }
    // -----------------------------------------------------------------------
    #accessibility(what) {
        const manager = window.Wexa !== undefined && window.Wexa !== null
            ? window.Wexa.accessibility
            : null;
        if (manager !== null && manager !== undefined) {
            manager[what]();
        }
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.AccessibilityNav = AccessibilityNav;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- menu.js ---------------
'use strict';
// --------------------------------------------------------------------------
// Class: SubMenuManager
// --------------------------------------------------------------------------
class SubMenuManager {
    // --------------------------------------------------------------------
    // Protected members
    // --------------------------------------------------------------------
    #asideElement;
    #menuLinks;
    _focusTrapHandler;
    // --------------------------------------------------------------------
    // Constructor
    // --------------------------------------------------------------------
    constructor(asideId = 'appmenu') {
        this.#asideElement = document.getElementById(asideId);
        // Include both <a> and <button> elements as focusable links.
        this.#menuLinks = this.#asideElement
            ? this.#asideElement.querySelectorAll('a, button')
            : [];
        // Bind the focus trap handler to preserve context when used as an event listener.
        this._focusTrapHandler = this.#trapFocus.bind(this);
    }
    // --------------------------------------------------------------------
    // Public methods
    // --------------------------------------------------------------------
    openSubmenu() {
        this.#setOpenState(true);
    }
    // --------------------------------------------------------------------
    closeSubmenu() {
        this.#setOpenState(false);
    }
    // --------------------------------------------------------------------
    // Private methods
    // --------------------------------------------------------------------
    #setOpenState(open) {
        if (this.#asideElement === null) return;
        const opened = open === true;
        // Toggle CSS class to open or close the submenu.
        this.#asideElement.classList.toggle('open', opened);
        // Update tab index of contained links.
        this.#setLinksTabIndex(opened ? 0 : -1);
        // Manage focus trapping when opened.
        if (opened === true) {
            document.addEventListener('keydown', this._focusTrapHandler, true);
            const onTransitionEnd = (ev) => {
                if (['left', 'right', 'top', 'bottom'].includes(ev.propertyName)) {
                    this.#menuLinks[0]?.focus();
                    this.#asideElement.removeEventListener('transitionend', onTransitionEnd);
                }
            };
            this.#asideElement.addEventListener('transitionend', onTransitionEnd);
        } else {
            document.removeEventListener('keydown', this._focusTrapHandler, true);
        }
        // Apply CSS-based positioning and alignment.
        this.#adjustSubmenuPosition();
        this.#adjustSubmenuAlignment();
    }
    // --------------------------------------------------------------------
    #adjustSubmenuPosition() {
        const position = getComputedStyle(this.#asideElement)
            .getPropertyValue('--appmenu-position')
            .trim();
        // Default to 'left' if no value found.
        this.#asideElement.setAttribute('data-submenu-position', position || 'left');
        // Force a reflow to ensure visual update.
        this.#asideElement.offsetHeight;
    }
    // --------------------------------------------------------------------
    #adjustSubmenuAlignment() {
        const align = getComputedStyle(this.#asideElement)
            .getPropertyValue('--appmenu-align')
            .trim();
        const [horizontal = 'center', vertical = 'center'] = align.split(' ');
        this.#asideElement.setAttribute('data-submenu-align-horizontal', horizontal);
        this.#asideElement.setAttribute('data-submenu-align-vertical', vertical);
        // Force reflow to apply updated alignment.
        this.#asideElement.offsetHeight;
    }
    // --------------------------------------------------------------------
    #trapFocus(e) {
        if (e.key !== 'Tab') return;
        const focusable = Array.from(this.#menuLinks);
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey) {
            // Shift + Tab: move from first to last
            if (document.activeElement === first) {
                e.preventDefault();
                last.focus();
            }
        } else {
            // Tab: move from last to first
            if (document.activeElement === last) {
                e.preventDefault();
                first.focus();
            }
        }
    }
    // --------------------------------------------------------------------
    #setLinksTabIndex(value) {
        for (const link of this.#menuLinks) {
            link.tabIndex = value;
        }
    }
}
// --------------------------------------------------------------------------
// Manager for an accessible menu
// --------------------------------------------------------------------------
class MenuManager {
    // --------------------------------------------------------------------
    // Protected members
    // --------------------------------------------------------------------
    // The '<nav>' element this class is managing
    #navElement;
    // A dictionary of registered submenus: each key is the submenu
    // identifier, and the value is its associated toggle button element.
    #submenus = new Map();
    // --------------------------------------------------------------------
    // Public members
    // --------------------------------------------------------------------
    static DEFAULT_NAV_ID = 'nav-content';
    // ----------------------------------------------------------------------
    constructor(navId = MenuManager.DEFAULT_NAV_ID) {
        this.#navElement = document.getElementById(navId);
        if (!this.#navElement) {
            throw new Error(`MenuManager: nav with id '${navId}' not found.`);
        }
        // Dictionary of registered submenus.
        this.#submenus = new Map();
        document.addEventListener('click', (e) => this.#handleBodyClick(e), true);
    }
    // ----------------------------------------------------------------------
    registerSubmenu(asideId, toggleButtonId) {
        const aside = document.getElementById(asideId);
        const toggle = document.getElementById(toggleButtonId);
        // Validate required elements.
        if (aside === null || toggle === null) {
            WexaLogger.warn(`MenuManager: Invalid submenu registration: '${asideId}'.`);
            return;
        }
        // Create submenu instance and store association.
        const submenu = new SubMenuManager(asideId);
        this.#submenus.set(submenu, toggle);
        this.#initToggleAttributes(toggle, asideId);
        this.#bindToggleEvents(submenu, toggle);
    }
    // ----------------------------------------------------------------------
    initSideMenu(navSelector = 'nav#nav-content.side.collapsible', pinButtonId = 'pin-menu') {
        const nav = document.querySelector(navSelector);
        const pinBtn = document.getElementById(pinButtonId);
        if (!nav) {
            WexaLogger.warn(`MenuManager: Side menu not found with selector '${navSelector}'.`);
            return;
        }
        if (!pinBtn) {
            WexaLogger.warn(`MenuManager: Pin button not found with id '${pinButtonId}'.`);
            return;
        }
        pinBtn.addEventListener('click', () => {
            const isPinned = nav.classList.toggle('expanded');
            nav.setAttribute('aria-pinned', isPinned ? 'true' : 'false');
            pinBtn.setAttribute('aria-pressed', String(isPinned));
            pinBtn.setAttribute('aria-label', isPinned ? 'Unpin menu' : 'Pin menu');
        });
    }
    // ----------------------------------------------------------------------
    initMobileToggle(checkboxId = 'mobile', buttonId = 'menu-button') {
        const checkbox = document.getElementById(checkboxId);
        const button = document.getElementById(buttonId);
        // Validate required elements.
        if (checkbox === null || button === null) {
            WexaLogger.warn('MenuManager: Missing elements for mobile toggle.');
            return;
        }
        // Bind state synchronization.
        checkbox.addEventListener('change', () => {
            this.#updateMobileState(checkbox, button);
        });
        // Bind button activation.
        button.addEventListener('click', () => {
            checkbox.checked = !checkbox.checked;
            this.#updateMobileState(checkbox, button);
        });
        // Initialize current state.
        this.#updateMobileState(checkbox, button);
    }
    // ----------------------------------------------------------------------
    // Private
    // ----------------------------------------------------------------------
    #initToggleAttributes(toggle, asideId) {
        toggle.setAttribute('aria-controls', asideId);
        toggle.setAttribute('aria-haspopup', 'menu');
        toggle.setAttribute('aria-expanded', 'false');
    }
    // ----------------------------------------------------------------------
    #bindToggleEvents(submenu, toggle) {
        const activate = (event) => {
            event.preventDefault();
            event.stopPropagation();
            // Collapse main menu if not pinned.
            const pin = document.getElementById('pin-menu');
            const isPinned = pin !== null && pin.getAttribute('aria-pressed') === 'true';
            if (isPinned === false) {
                this.#navElement.classList.remove('expanded');
                this.#navElement.setAttribute('aria-expanded', 'false');
            }
            this.#closeOtherSubmenus(submenu);
            submenu.openSubmenu();
            toggle.setAttribute('aria-expanded', 'true');
        };
        toggle.addEventListener('click', activate);
        toggle.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') activate(e);
        });
    }
    // ----------------------------------------------------------------------
    #closeOtherSubmenus(current) {
        for (const [submenu, toggle] of this.#submenus) {
            if (submenu !== current) {
                submenu.closeSubmenu();
                toggle.setAttribute('aria-expanded', 'false');
            }
        }
    }
    // ----------------------------------------------------------------------
    #handleBodyClick(event) {
        const target = event.target;
        // Ignore clicks inside the main nav or any open aside
        const insideNav   = this.#navElement.contains(target);
        const insideAside = target.closest('aside.appmenu.open') !== null;
        if (insideNav || insideAside) return;
        // Otherwise close all submenus
        for (const [submenu, toggle] of this.#submenus) {
            submenu.closeSubmenu();
            toggle.setAttribute('aria-expanded', 'false');
        }
        // Remove transient state flags
        this.#navElement.classList.remove('submenu-active');
    }
    // ----------------------------------------------------------------------
    #updateMobileState(checkbox, button) {
        const expanded = checkbox.checked === true;
        this.#navElement.classList.toggle('expanded', expanded);
        this.#navElement.setAttribute('aria-expanded', String(expanded));
        button.setAttribute('aria-expanded', String(expanded));
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.SubMenuManager = SubMenuManager;
window.Wexa.MenuManager = MenuManager;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- dialog.js ---------------
'use strict';
class DialogManager {
    // --------------------------------------------------------------------
    // Members
    // --------------------------------------------------------------------
    #dialogs;
    #closeButtonName;
    #videoPrefix;
    #dialogPrefix;
    // --------------------------------------------------------------------
    // Constructor
    // --------------------------------------------------------------------
    constructor() {
        this.#dialogs = new Map();
        this.#closeButtonName = 'popup-close-btn';
        this.#videoPrefix = 'popup-video-';
        this.#dialogPrefix = 'popup-';
    }
    // --------------------------------------------------------------------
    // Public methods
    // --------------------------------------------------------------------
    open(id, isModal = false) {
        const dialog = this.#getDialog(id);
        if (dialog === null) return;
        // Replace hidden class to make the dialog visible.
        dialog.classList.replace('hidden-alert', 'hidden-alert-open');
        // Ensure a single close button is available.
        this.#createCloseButton(dialog);
        // Open the dialog, preferring modal mode if requested and supported.
        if (isModal === true && typeof dialog.showModal === 'function') {
            dialog.showModal();
        } else if (typeof dialog.show === 'function') {
            dialog.show();
        } else {
            dialog.setAttribute('open', '');
        }
    }
    // --------------------------------------------------------------------
    close(id) {
        const dialog = this.#getDialog(id);
        if (dialog === null) return;
        // Restore the hidden class to hide the dialog.
        dialog.classList.replace('hidden-alert-open', 'hidden-alert');
        // Remove the close button if present.
        Array.from(dialog.children).forEach(child => {
            if (child.name === this.#closeButtonName) {
                child.remove();
            }
        });
        // Close the dialog (prefer the native method if supported).
        if (typeof dialog.close === 'function') {
            dialog.close();
        } else {
            dialog.removeAttribute('open');
        }
    }
    // --------------------------------------------------------------------
    async playVideo(id) {
        const popupId = this.#dialogPrefix + id;
        this.open(popupId, true);
        const video = document.getElementById(this.#videoPrefix + id);
        if (video === null) {
            WexaLogger.error(`DialogManager: video not found for '${id}'.`);
            return;
        }
        // Trigger quick playback to preload video data.
        await video.play();
        video.pause();
    }
    // --------------------------------------------------------------------
    closeVideo(id) {
        const popupId = this.#dialogPrefix + id;
        this.close(popupId);
        const video = document.getElementById(this.#videoPrefix + id);
        if (video !== null) {
            // Pause playback to release resources.
            video.pause();
        } else {
            WexaLogger.warn(`DialogManager: video not found for '${id}'.`);
        }
    }
    // --------------------------------------------------------------------
    // Private methods
    // --------------------------------------------------------------------
    #getDialog(id) {
        if (this.#dialogs.has(id)) {
            return this.#dialogs.get(id);
        }
        const dialog = document.getElementById(id);
        if (dialog === null) {
            WexaLogger.error(`DialogManager: dialog not found: '${id}'.`);
            return null;
        }
        this.#dialogs.set(id, dialog);
        return dialog;
    }
    #createCloseButton(dialog) {
        if (dialog.querySelector(`button[name="${this.#closeButtonName}"]`) !== null) {
            return;
        }
        const btn = document.createElement('button');
        btn.name = this.#closeButtonName;
        btn.type = 'button';
        btn.innerHTML = '&#10060;';
        btn.addEventListener('click', () => this.close(dialog.id));
        dialog.appendChild(btn);
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.DialogManager = DialogManager;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- progressbar.js ---------------
class ProgressBar extends BaseManager {
    // ------------------------------------------------------------------------
    // Constructor
    // ------------------------------------------------------------------------
    constructor(options = {}) {
        super();
        this._updateCallback = options.updateCallback || null;
        this._completeCallback = options.completeCallback || null;
        this._requestManager = options.requestManager || null;
        this._targetUrl = options.targetUrl || '';
        this._intervalMs = options.intervalMs || 1500;
        this._domIds = options.domIds || {
            percent: 'percent_progress',
            text: 'progress_text',
            header: 'progress_header'
        };
        this._intervalId = null;
        this._percent = 0;
        this._text = '';
        this._header = '';
    }
    // -----------------------------------------------------------------------
    // Public API
    // -----------------------------------------------------------------------
    start() {
        this.stop();
        WexaLogger.debug("Progress start:")
        this._intervalId = setInterval(async () => {
            const response = await this._fetchProgressData();
            if (response === null) {
                WexaLogger.warn(" == Empty response == ")
                await this._fetchComplete();
                return;
            }
            // Stop updates when installation is completed.
            if ((this._requestManager && this._requestManager.status === 200) || response.status === 200) {
                WexaLogger.debug(" == STATUS 200 RECEIVED ==")
                await this._fetchComplete();
                return
            }
            // The progress is updated
            this._updateDisplay(response.percent, response.text, response.header);
            if (this._percent >= 100) {
                WexaLogger.debug(" == PERCENT COMPLETED ==")
                await this._fetchComplete();
            }
        }, this._intervalMs);
    }
    // -----------------------------------------------------------------------
    stop() {
        WexaLogger.debug("Progress stop:")
        if (this._intervalId !== null) {
            clearInterval(this._intervalId);
            this._intervalId = null;
        }
    }
    // -----------------------------------------------------------------------
    update(percent, text, header) {
        WexaLogger.debug("Progress update:")
        this._updateDisplay(percent, text, header);
    }
    // -----------------------------------------------------------------------
    setRequestManager(requestManager, targetUrl) {
        this._requestManager = requestManager;
        this._targetUrl = targetUrl;
    }
    // -----------------------------------------------------------------------
    // Private helpers
    // -----------------------------------------------------------------------
    async _fetchComplete() {
        this.stop();
        if (this._completeCallback !== null) {
            this._completeCallback();
        } else {
            this.submitForm('event_bake', 'complete');
        }
    }
    // -----------------------------------------------------------------------
    async _fetchProgressData() {
        if (this._updateCallback !== null) {
            return await this._updateCallback();
        }
        if (this._requestManager === null || this._targetUrl === '') {
            WexaLogger.error('ProgressBar: No update callback or RequestManager available.');
            return null;
        }
        const response = await this.postEvents({event_name: 'update'});
        return response
    }
    // -----------------------------------------------------------------------
    _updateDisplay(percent, text, header) {
        if (typeof percent === 'number') {
            this._percent = percent;
        }
        if (typeof text === 'string') {
            this._text = text;
        }
        if (typeof header === 'string') {
            this._header = header;
        }
        this._render();
    }
    // -----------------------------------------------------------------------
    _render() {
        const percentEl = document.getElementById(this._domIds.percent);
        const textEl = document.getElementById(this._domIds.text);
        const headerEl = document.getElementById(this._domIds.header);
        if (percentEl !== null) {
            percentEl.value = this._percent;
        }
        if (textEl !== null) {
            textEl.textContent = this._text;
        }
        if (headerEl !== null) {
            headerEl.textContent = this._header;
        }
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.ProgressBar = ProgressBar;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- toggleselect.js ---------------
// --------------------------------------------------------------------------
class ToggleSelector {
    // Define base path and icon names as member variables
    static ICONS = {
        CHECKED: "checked",
        UNCHECKED: "unchecked",
        HALF: "half-checked"
    };
    // Define CSS selectors for buttons and checkboxes
    static BUTTON_SELECTOR = 'button.accordion-action';
    static CHECKBOX_SELECTOR = 'input[type="checkbox"]';
    // Fields
    _detailsElt;
    // Constructor
    constructor(detailsId) {
        // The <details> element which is manipulated in this class
        this._detailsElt = document.getElementById(detailsId);
        if (!this._detailsElt) {
            throw new Error(`ToggleSelector instantiation failed: No details element found with id: ${detailsId}.`);
        }
        // Call handleInputsOnLoad() to initialize any inputs or settings
        this.handleInputsOnLoad();
    }
    // ----------------------------------------------------------------------
    getCheckboxes() {
        return this._detailsElt.querySelectorAll('input[type="checkbox"][data-toggle]');
    }
    // ----------------------------------------------------------------------
    handleInputsOnLoad() {
        // Setup listeners for checkboxes
        this.setupCheckboxListeners();
        // The icons are drawn once the framework knows where to read them: a
        // page may instantiate this class before wexa.js has said so.
        OnLoadManager.addLoadFunction(() => {
            this.drawBoxes();
            this.updateAllToggleButtons();
        });
        // Attach event listener for click events on checkboxes
        document.addEventListener('click', (event) => {
            const target = event.target;
            if (target.type === 'checkbox') {
                this.updateAllToggleButtons();
            }
        });
    }
    // ----------------------------------------------------------------------
    drawBoxes() {
        this.getCheckboxes().forEach(checkbox => {
            const label = this._detailsElt.querySelector('label[for="' + checkbox.id + '"]');
            if (label === null) {
                console.warn(`ToggleSelector: the checkbox "${checkbox.id}" has no label, its box is not drawn.`);
                return;
            }
            let holder = label.querySelector('span.check-box');
            if (holder === null) {
                holder = document.createElement('span');
                holder.className = 'check-box';
                label.insertBefore(holder, label.firstChild);
            }
            holder.replaceChildren();
            icons.inject(holder,
                checkbox.checked === true ? ToggleSelector.ICONS.CHECKED : ToggleSelector.ICONS.UNCHECKED);
        });
    }
    // ----------------------------------------------------------------------
    toggleSelection(event) {
        // A key that is not the one acting on this button belongs to the page:
        // preventing it would keep the focus from ever leaving.
        if (event.type === 'keydown' && event.key !== 'Enter' && event.key !== ' ') {
            return;
        }
        // A click inside a summary opens or closes the disclosure: this button
        // acts on the boxes, and on nothing else.
        event.preventDefault();
        event.stopPropagation();
        const checkboxes = this.getCheckboxes();
        const button = event.currentTarget;
        // Check if any of the checkboxes are already checked
        const anyChecked = Array.from(checkboxes).some(checkbox => checkbox.checked);
        // Toggle the checked state of all checkboxes
        checkboxes.forEach(checkbox => {
            checkbox.checked = !anyChecked;
        });
        // Update the button image and every box with the new state
        this.updateToggleButton(button, !anyChecked);
        this.drawBoxes();
    }
    // ----------------------------------------------------------------------
    updateToggleButton(button, anyChecked, oneChecked = false) {
        let name = ToggleSelector.ICONS.UNCHECKED;
        if (oneChecked === true) {
            name = ToggleSelector.ICONS.HALF;
        } else if (anyChecked === true) {
            name = ToggleSelector.ICONS.CHECKED;
        }
        // inject() leaves an element that already holds an SVG untouched: what
        // is drawn has to go before the new state can be drawn.
        button.replaceChildren();
        icons.inject(button, name);
    }
    // ----------------------------------------------------------------------
    setupCheckboxListeners() {
        const checkboxes = this.getCheckboxes();
        const button = this._detailsElt.querySelector('button.accordion-action[data-toggle]');
        // Add a 'change' event listener to each checkbox
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                // At least one is checked
                const anyChecked = Array.from(checkboxes).some(checkbox => checkbox.checked);
                // All are checked
                const allChecked = Array.from(checkboxes).every(checkbox => checkbox.checked);
                // Update button and boxes based on the state
                this.updateButtonState(button, anyChecked, allChecked);
                this.drawBoxes();
            });
        });
    }
    // ----------------------------------------------------------------------
    updateButtonState(button, anyChecked, allChecked) {
        if (allChecked) {
            this.updateToggleButton(button, anyChecked);
        } else if (anyChecked) {
            this.updateToggleButton(button, anyChecked, true);
        } else {
            this.updateToggleButton(button, anyChecked, false);
        }
    }
    // ----------------------------------------------------------------------
    updateAllToggleButtons() {
        const buttons = this._detailsElt.querySelectorAll(ToggleSelector.BUTTON_SELECTOR);
        buttons.forEach(button => {
            const checkboxes = button.closest('details').querySelectorAll(ToggleSelector.CHECKBOX_SELECTOR);
            const anyChecked = Array.from(checkboxes).some(checkbox => checkbox.checked);
            const allChecked = Array.from(checkboxes).every(checkbox => checkbox.checked);
            // Update button based on the state of checkboxes
            this.updateButtonState(button, anyChecked, allChecked);
        });
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.ToggleSelector = ToggleSelector;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- links.js ---------------
'use strict';
class LinkController {
    constructor() {
        // Nothing to initialize; listeners are attached explicitly via handleLinks().
    }
    // ----------------------------------------------------------------------
    handleLinks(selectors) {
        this._bindLinks(selectors, false);
    }
    handleLinksWithParameters(selectors) {
        this._bindLinks(selectors, true);
    }
    static initFocusable() {
        document.querySelectorAll('[data-href]:not([href]):not([tabindex])').forEach(el => {
            el.setAttribute('tabindex', '0');
        });
    }
    // ----------------------------------------------------------------------
    // Private
    // ----------------------------------------------------------------------
    _bindLinks(selectors, withParameters) {
        if (!Array.isArray(selectors)) {
            console.error('LinkController: Expected a list of element ids.');
            return;
        }
        for (const id of selectors) {
            const element = document.getElementById(id);
            if (element === null) {
                console.warn(`LinkController: No element found with id "${id}".`);
                continue;
            }
            // Avoid multiple bindings on the same element
            if (element.dataset.linkBound) continue;
            element.dataset.linkBound = '1';
            element.addEventListener('click', (event) => this._handleActivation(event, element, withParameters));
            element.addEventListener('keydown', (event) => this._handleActivation(event, element, withParameters));
        }
    }
    // ----------------------------------------------------------------------
    _handleActivation(event, element, withParameters) {
        const isClick = (event.type === 'click');
        const isEnter = (event.type === 'keydown' && event.key === 'Enter');
        if (isClick === false && isEnter === false) {
            return;
        }
        event.preventDefault();
        event.stopPropagation();
        const url = element.getAttribute('href') || element.dataset.href;
        if (!url) {
            console.warn(`LinkController: No URL defined for element id="${element.id}".`);
            return;
        }
        const target = element.dataset.target || '_blank';
        this._openUrl(url, target, withParameters);
    }
    // ----------------------------------------------------------------------
    _openUrl(url, target, withParameters) {
        let finalUrl = url;
        if (withParameters === true) {
            const absoluteUrl = new URL(url, window.location.href).href;
            finalUrl = window.Wexa.accessibility.setUrlWithParameters(absoluteUrl);
        }
        if (target === '_blank' || target === '_self') {
            window.open(finalUrl, target, 'noopener');
            return;
        }
        const iframe = document.getElementById(target);
        if (iframe && iframe.tagName.toLowerCase() === 'iframe') {
            iframe.src = finalUrl;
        } else {
            // A named window: open the tab of this name, or reuse it.
            // No 'noopener' here: the window name lookup needs the opener
            // relationship, and a named target is an internal page.
            window.open(finalUrl, target);
        }
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.LinkController = LinkController;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- customize/theme_manager.js ---------------
class ThemeManager extends BaseManager {
    // -----------------------------------------------------------------------
    // FIELDS
    // -----------------------------------------------------------------------
    #themes;        // Map<name, path>
    #activeTheme;   // "" or a registered name
    #defaultTheme;  // "" or a registered name applied when no URL param is present
    static get THEME_PARAMETER_NAME() { return "wexa_theme"; }
    static get LINK_ID()              { return "wexa-theme"; }
    // -----------------------------------------------------------------------
    // CONSTRUCTOR
    // -----------------------------------------------------------------------
    constructor() {
        super();
        this.#themes = new Map();
        this.#activeTheme = "";
        this.#defaultTheme = "";
        OnLoadManager.addLoadFunction(this.#loadFromUrl.bind(this));
        OnLoadManager.addLoadFunction(this.#injectButtonIcon.bind(this));
    }
    // -----------------------------------------------------------------------
    // GETTERS
    // -----------------------------------------------------------------------
    get themeNames() {
        return [...this.#themes.keys()];
    }
    // -----------------------------------------------------------------------
    get activeTheme() {
        return this.#activeTheme;
    }
    // -----------------------------------------------------------------------
    // PUBLIC METHODS
    // -----------------------------------------------------------------------
    register(name, path) {
        if (typeof name !== 'string' || typeof path !== 'string') {
            console.error("ThemeManager.register: name and path must be strings.");
            return;
        }
        this.#themes.set(name, path);
    }
    // -----------------------------------------------------------------------
    setDefault(name) {
        if (!this.#themes.has(name)) {
            console.error(`ThemeManager.setDefault: unknown theme "${name}".`);
            return;
        }
        this.#defaultTheme = name;
        const params = new URLSearchParams(window.location.search);
        if (params.has(ThemeManager.THEME_PARAMETER_NAME)) {
            const urlTheme = params.get(ThemeManager.THEME_PARAMETER_NAME);
            if (this.#themes.has(urlTheme)) {
                this.activate(urlTheme);
            }
        } else if (this.#activeTheme === "") {
            this.activate(name);
        }
    }
    // -----------------------------------------------------------------------
    async activate(name) {
        if (name !== "" && !this.#themes.has(name)) {
            console.error(`ThemeManager.activate: unknown theme "${name}".`);
            return;
        }
        this.#activeTheme = name;
        this.#applyLink(name === "" ? "" : this.#themes.get(name));
        history.replaceState(null, '', this.setUrlWithParameters(window.location.href));
        await this.postEvents({"theme": name});
    }
    // -----------------------------------------------------------------------
    async next() {
        const names = this.themeNames;
        if (names.length === 0) {
            return;
        }
        if (this.#activeTheme === "") {
            const defaultIdx = names.indexOf(this.#defaultTheme);
            const nextIdx = defaultIdx + 1;
            await this.activate(nextIdx >= names.length ? "" : names[nextIdx]);
            return;
        }
        const idx = names.indexOf(this.#activeTheme);
        const nextIdx = idx + 1;
        await this.activate(nextIdx >= names.length ? this.#defaultTheme : names[nextIdx]);
    }
    // -----------------------------------------------------------------------
    setUrlWithParameters(url) {
        if (url === null || url === '') {
            return '';
        }
        const customUrl = new URL(url, window.location.href);
        if (this.#activeTheme !== '') {
            customUrl.searchParams.set(ThemeManager.THEME_PARAMETER_NAME, this.#activeTheme);
        } else {
            customUrl.searchParams.delete(ThemeManager.THEME_PARAMETER_NAME);
        }
        return customUrl.href;
    }
    // -----------------------------------------------------------------------
    // PRIVATE METHODS
    // -----------------------------------------------------------------------
    async #injectButtonIcon() {
        await icons.inject(document.getElementById('btn-css-theme'), 'theme');
    }
    // -----------------------------------------------------------------------
    #applyLink(path) {
        let link = document.getElementById(ThemeManager.LINK_ID);
        if (path === "") {
            if (link !== null) {
                link.remove();
            }
            return;
        }
        if (link === null) {
            link = document.createElement('link');
            link.id = ThemeManager.LINK_ID;
            link.rel = 'stylesheet';
            document.head.appendChild(link);
        }
        link.href = path;
    }
    // -----------------------------------------------------------------------
    async #loadFromUrl() {
        const params = new URLSearchParams(window.location.search);
        if (params.has(ThemeManager.THEME_PARAMETER_NAME)) {
            const name = params.get(ThemeManager.THEME_PARAMETER_NAME);
            if (this.#themes.has(name)) {
                await this.activate(name);
            } else {
                console.log(ThemeManager.THEME_PARAMETER_NAME + " unknown value: " + name);
            }
        } else if (this.#defaultTheme !== "" && this.#activeTheme === "") {
            await this.activate(this.#defaultTheme);
        }
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.ThemeManager = ThemeManager;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- customize/icon_set.js ---------------
'use strict';
const IconForm = {
    LINE: 'line',
    IMAGE: 'image'
};
class IconSet {
    #name;
    #base;
    #files = new Map();
    constructor(name, base, files) {
        this.#name = name;
        this.#base = base;
        const given = Array.isArray(files) === true ? files : [];
        for (const file of given) {
            this.#files.set(IconSet.nameOf(file), file);
        }
    }
    // -----------------------------------------------------------------------
    static nameOf(file) {
        const dot = file.lastIndexOf('.');
        return dot === -1 ? file : file.substring(0, dot);
    }
    // -----------------------------------------------------------------------
    get name() {
        return this.#name;
    }
    get base() {
        return this.#base;
    }
    get names() {
        return Array.from(this.#files.keys());
    }
    // -----------------------------------------------------------------------
    carries(name) {
        if (typeof name !== 'string' || name === '') {
            return false;
        }
        return this.#files.has(name);
    }
    // -----------------------------------------------------------------------
    addressOf(name) {
        return this.#base + this.#files.get(name);
    }
    // -----------------------------------------------------------------------
    formOf(name) {
        const file = this.#files.get(name);
        if (file === undefined) {
            return IconForm.IMAGE;
        }
        return file.toLowerCase().endsWith('.svg') === true
            ? IconForm.LINE
            : IconForm.IMAGE;
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.IconSet = IconSet;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- customize/icon_sets.js ---------------
'use strict';
class IconSets {
    #declared = new Map();
    #reference = null;
    #fallback = '';
    // -----------------------------------------------------------------------
    declare(set) {
        if (set === null || set === undefined) {
            return;
        }
        if (this.#declared.has(set.name) === true) {
            WexaLogger.warn('IconSets: the set "' + set.name
                + '" is declared twice. The first one is kept.');
            return;
        }
        this.#declared.set(set.name, set);
    }
    // -----------------------------------------------------------------------
    reference(set) {
        if (set === null || set === undefined) {
            return;
        }
        this.#reference = set;
    }
    // -----------------------------------------------------------------------
    fallback(name) {
        if (this.#declared.has(name) === false) {
            WexaLogger.warn('IconSets: the set "' + name
                + '" answers for the others, and was never declared.');
            return;
        }
        this.#fallback = name;
    }
    // -----------------------------------------------------------------------
    setFor(name, inForce) {
        const chosen = this.#declared.get(inForce);
        if (chosen !== undefined && chosen.carries(name) === true) {
            return chosen;
        }
        if (this.#fallback !== '' && this.#fallback !== inForce) {
            const answering = this.#declared.get(this.#fallback);
            if (answering !== undefined && answering.carries(name) === true) {
                return answering;
            }
        }
        if (this.#reference !== null && this.#reference.carries(name) === true) {
            return this.#reference;
        }
        return null;
    }
    // -----------------------------------------------------------------------
    namesFor(inForce) {
        const names = [];
        const chain = [
            this.#declared.get(inForce),
            this.#declared.get(this.#fallback),
            this.#reference
        ];
        for (const set of chain) {
            if (set === undefined || set === null) {
                continue;
            }
            for (const name of set.names) {
                if (names.includes(name) === false) {
                    names.push(name);
                }
            }
        }
        return names;
    }
    // -----------------------------------------------------------------------
    names() {
        const names = Array.from(this.#declared.keys());
        if (this.#reference !== null) {
            names.push(this.#reference.name);
        }
        return names;
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.IconSets = IconSets;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- customize/icon_choice.js ---------------
'use strict';
class IconChoice {
    static get PARAMETER_NAME() {
        return 'wexa_icons';
    }
    #sets;
    #inForce;
    constructor(sets, named = '', search = null) {
        this.#sets = sets;
        this.#inForce = this.#firstDeclared([
            this.#inAddress(search),
            named
        ]);
    }
    // -----------------------------------------------------------------------
    inForce() {
        return this.#inForce;
    }
    // -----------------------------------------------------------------------
    put(name) {
        if (this.#isDeclared(name) === false) {
            return false;
        }
        if (name === this.#inForce) {
            return false;
        }
        this.#inForce = name;
        this.#sayInAddress(name);
        return true;
    }
    // -----------------------------------------------------------------------
    // PRIVATE
    // -----------------------------------------------------------------------
    #isDeclared(name) {
        if (typeof name !== 'string' || name === '') {
            return false;
        }
        return this.#sets.names().includes(name);
    }
    // -----------------------------------------------------------------------
    #firstDeclared(names) {
        for (const name of names) {
            if (this.#isDeclared(name) === true) {
                return name;
            }
        }
        const declared = this.#sets.names();
        return declared.length === 0 ? '' : declared[declared.length - 1];
    }
    // -----------------------------------------------------------------------
    #inAddress(search) {
        const query = search !== null ? search : window.location.search;
        const asked = new URLSearchParams(query.substring(query.indexOf('?') + 1));
        return asked.get(IconChoice.PARAMETER_NAME) || '';
    }
    // -----------------------------------------------------------------------
    #sayInAddress(name) {
        if (typeof window === 'undefined' || window.history === undefined) {
            return;
        }
        const address = new URL(window.location.href);
        address.searchParams.set(IconChoice.PARAMETER_NAME, name);
        window.history.replaceState(null, '', address.href);
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.IconChoice = IconChoice;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- customize/icon_errors.js ---------------
'use strict';
class IconError extends Error {
    constructor(message) {
        super(message);
        this.name = 'IconError';
    }
}
class NoSetAtAll extends IconError {
    constructor() {
        super('No set of icons was declared, not even the reference one.');
        this.name = 'NoSetAtAll';
    }
}
class UnreadableContent extends IconError {
    constructor(address) {
        super('The content at "' + address + '" cannot be read.');
        this.name = 'UnreadableContent';
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.IconError = IconError;
window.Wexa.NoSetAtAll = NoSetAtAll;
window.Wexa.UnreadableContent = UnreadableContent;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- customize/icon_content.js ---------------
'use strict';
class IconContent {
    #name;
    #form;
    #source;
    constructor(name, form, source) {
        this.#name = name;
        this.#form = form;
        this.#source = source;
    }
    get name() {
        return this.#name;
    }
    get form() {
        return this.#form;
    }
    get source() {
        return this.#source;
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.IconContent = IconContent;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- customize/icon_reader.js ---------------
'use strict';
class IconReader {
    static #gathered = new Map();
    #read = new Map();
    // -----------------------------------------------------------------------
    static gather(setName, name, markup) {
        IconReader.#gathered.set(setName + '/' + name, markup);
    }
    // -----------------------------------------------------------------------
    gather(setName, name, markup) {
        this.#read.set(setName + '/' + name, markup);
    }
    // -----------------------------------------------------------------------
    address(set, name) {
        return new IconContent(name, IconForm.IMAGE, set.addressOf(name));
    }
    // -----------------------------------------------------------------------
    async read(set, name) {
        const form = set.formOf(name);
        const address = set.addressOf(name);
        if (form === IconForm.IMAGE) {
            return new IconContent(name, form, address);
        }
        const key = set.name + '/' + name;
        if (this.#read.has(key) === true) {
            return new IconContent(name, form, this.#read.get(key));
        }
        if (IconReader.#gathered.has(key) === true) {
            return new IconContent(name, form, IconReader.#gathered.get(key));
        }
        const markup = await this.#markupAt(address);
        this.#read.set(key, markup);
        return new IconContent(name, form, markup);
    }
    // -----------------------------------------------------------------------
    // PRIVATE
    // -----------------------------------------------------------------------
    async #markupAt(address) {
        let answer = null;
        try {
            answer = await fetch(address);
        } catch (error) {
            throw new UnreadableContent(address);
        }
        if (answer.ok === false) {
            throw new UnreadableContent(address);
        }
        return await answer.text();
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.IconReader = IconReader;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- customize/icon_demand.js ---------------
'use strict';
const DemandKind = {
    PLACE: 'place',
    SURFACE: 'surface'
};
const ATTRIBUTE = {
    place: 'data-icon',
    surface: 'data-ground'
};
class IconDemand {
    #element;
    #name;
    #kind;
    constructor(element, name, kind) {
        this.#element = element;
        this.#name = name;
        this.#kind = kind;
    }
    // -----------------------------------------------------------------------
    static of(element) {
        if (element === null || element === undefined) {
            return null;
        }
        for (const kind of Object.keys(ATTRIBUTE)) {
            const name = element.getAttribute(ATTRIBUTE[kind]);
            if (name !== null && name !== '') {
                return new IconDemand(element, name, kind);
            }
        }
        return null;
    }
    // -----------------------------------------------------------------------
    static get SELECTOR() {
        return '[' + ATTRIBUTE.place + '], [' + ATTRIBUTE.surface + ']';
    }
    // -----------------------------------------------------------------------
    get element() {
        return this.#element;
    }
    get name() {
        return this.#name;
    }
    get kind() {
        return this.#kind;
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.IconDemand = IconDemand;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- customize/icon_placer.js ---------------
'use strict';
const MARK = 'data-icon-placed';
class IconPlacer {
    place(demand, content) {
        if (demand === null || content === null) {
            return;
        }
        this.clear(demand);
        if (demand.kind === DemandKind.SURFACE) {
            this.#cover(demand, content);
            return;
        }
        if (content.form === IconForm.LINE) {
            this.#writeIn(demand, content);
        } else {
            this.#putImageIn(demand, content);
        }
    }
    // -----------------------------------------------------------------------
    clear(demand) {
        if (demand === null) {
            return;
        }
        const element = demand.element;
        if (demand.kind === DemandKind.SURFACE) {
            element.style.removeProperty('background-image');
            element.style.removeProperty('background-repeat');
            element.style.removeProperty('background-position');
            return;
        }
        const placed = element.querySelector('[' + MARK + ']');
        if (placed !== null) {
            placed.remove();
        }
    }
    // -----------------------------------------------------------------------
    // PRIVATE
    // -----------------------------------------------------------------------
    #writeIn(demand, content) {
        const holder = document.createElement('span');
        holder.setAttribute(MARK, content.name);
        holder.setAttribute('aria-hidden', 'true');
        holder.innerHTML = content.source;
        const drawing = holder.querySelector('svg');
        if (drawing !== null) {
            drawing.setAttribute(MARK, content.name);
            drawing.setAttribute('aria-hidden', 'true');
            demand.element.insertAdjacentElement('afterbegin', drawing);
            return;
        }
        demand.element.insertAdjacentElement('afterbegin', holder);
    }
    // -----------------------------------------------------------------------
    #putImageIn(demand, content) {
        const image = document.createElement('img');
        image.setAttribute(MARK, content.name);
        image.setAttribute('src', content.source);
        image.setAttribute('alt', '');
        image.setAttribute('loading', 'lazy');
        image.setAttribute('decoding', 'async');
        const room = this.#roomOf(demand.element);
        image.setAttribute('width', room.width);
        image.setAttribute('height', room.height);
        demand.element.insertAdjacentElement('afterbegin', image);
    }
    // -----------------------------------------------------------------------
    #cover(demand, content) {
        const element = demand.element;
        element.style.backgroundImage = 'url("' + content.source + '")';
        // A ground covers: it is laid from the corner and repeated. The
        // framework asks for no repetition on every element, which would leave
        // one drawing at the top of the surface.
        element.style.backgroundRepeat = 'repeat';
        element.style.backgroundPosition = '0 0';
    }
    // -----------------------------------------------------------------------
    #roomOf(element) {
        const style = window.getComputedStyle(element);
        const width = parseInt(style.getPropertyValue('--icon-width'), 10);
        const height = parseInt(style.getPropertyValue('--icon-height'), 10);
        const size = parseInt(style.fontSize, 10) || 16;
        return {
            width: String(Number.isNaN(width) === true ? size : width),
            height: String(Number.isNaN(height) === true ? size : height)
        };
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.IconPlacer = IconPlacer;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- customize/icon_watcher.js ---------------
'use strict';
class IconWatcher {
    #observer = null;
    #watched = new Map();
    #onView = null;
    watch(demands, onView) {
        this.#onView = typeof onView === 'function' ? onView : null;
        if (this.#onView === null || Array.isArray(demands) === false) {
            return;
        }
        if (typeof IntersectionObserver === 'undefined') {
            demands.forEach(demand => this.#onView(demand));
            return;
        }
        if (this.#observer === null) {
            this.#observer = new IntersectionObserver(
                entries => this.#seen(entries),
                { rootMargin: '200px' });
        }
        for (const demand of demands) {
            this.#watched.set(demand.element, demand);
            this.#observer.observe(demand.element);
        }
    }
    // -----------------------------------------------------------------------
    stop() {
        if (this.#observer !== null) {
            this.#observer.disconnect();
        }
        this.#watched.clear();
    }
    // -----------------------------------------------------------------------
    // PRIVATE
    // -----------------------------------------------------------------------
    #seen(entries) {
        for (const entry of entries) {
            if (entry.isIntersecting === false) {
                continue;
            }
            const demand = this.#watched.get(entry.target);
            if (demand === undefined) {
                continue;
            }
            this.#observer.unobserve(entry.target);
            this.#watched.delete(entry.target);
            this.#onView(demand);
        }
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.IconWatcher = IconWatcher;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- customize/icon_register.js ---------------
'use strict';
class IconRegister {
    #held = new Set();
    hold(demand) {
        if (demand === null || demand === undefined) {
            return;
        }
        this.#held.add(demand);
    }
    // -----------------------------------------------------------------------
    held() {
        const standing = [];
        for (const demand of this.#held) {
            if (demand.element.isConnected === true) {
                standing.push(demand);
            } else {
                this.#held.delete(demand);
            }
        }
        return standing;
    }
    // -----------------------------------------------------------------------
    clear() {
        this.#held.clear();
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.IconRegister = IconRegister;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- customize/theme_reference.js ---------------
'use strict';
const THEMES_BASE = 'css/themes/';
const REFERENCE_THEMES = [
    ['wexa_theme', 'wexa_theme.css'],
    ['aurora', 'wexa_theme_aurora.css'],
    ['highcontrast', 'wexa_theme_highcontrast.css'],
];
// ---------------- customize/icon_reference.js ---------------
'use strict';
const REFERENCE_BASE = 'icons/mono-svg/';
const REFERENCE_FILES = [
    'accessibility.svg',
    'add.svg',
    'anonymous.svg',
    'arrow-down.svg',
    'arrow-left.svg',
    'arrow-right.svg',
    'arrow-up.svg',
    'audio.svg',
    'back.svg',
    'backward.svg',
    'bell-off.svg',
    'bell.svg',
    'book-open.svg',
    'book.svg',
    'box.svg',
    'broom.svg',
    'cadenas-open.svg',
    'cadenas.svg',
    'calendar.svg',
    'cancel.svg',
    'checked.svg',
    'chevron-down.svg',
    'chevron-left.svg',
    'chevron-right.svg',
    'chevron-up.svg',
    'clip.svg',
    'clipboard.svg',
    'clock.svg',
    'close.svg',
    'cloud-off.svg',
    'cloud.svg',
    'color.svg',
    'compas.svg',
    'compress.svg',
    'congrats.svg',
    'content.svg',
    'contrast.svg',
    'copy.svg',
    'cursor-hand.svg',
    'cursor-text.svg',
    'cursor.svg',
    'dashboard.svg',
    'delete.svg',
    'discovery.svg',
    'dislike.svg',
    'download.svg',
    'edit.svg',
    'error.svg',
    'export.svg',
    'external-link.svg',
    'eye-off.svg',
    'eye.svg',
    'faq.svg',
    'favorite.svg',
    'feedback.svg',
    'file.svg',
    'filter.svg',
    'first.svg',
    'folder-off.svg',
    'folder.svg',
    'forward.svg',
    'fullscreen.svg',
    'gallery.svg',
    'games.svg',
    'goto.svg',
    'grid-view.svg',
    'half-checked.svg',
    'heart.svg',
    'help.svg',
    'house.svg',
    'image.svg',
    'import.svg',
    'info-square.svg',
    'install.svg',
    'lang.svg',
    'last.svg',
    'layers.svg',
    'light-bulb.svg',
    'like.svg',
    'link-off.svg',
    'link.svg',
    'list-view.svg',
    'logout.svg',
    'mail-in.svg',
    'mail-open.svg',
    'mail-out.svg',
    'mail.svg',
    'menu.svg',
    'microphone-off.svg',
    'microphone.svg',
    'misty-moon.svg',
    'moon.svg',
    'move.svg',
    'next.svg',
    'no.svg',
    'open.svg',
    'page.svg',
    'parameters.svg',
    'pathway.svg',
    'pause.svg',
    'pin.svg',
    'play.svg',
    'plugin.svg',
    'position.svg',
    'post-it.svg',
    'power.svg',
    'print.svg',
    'radio-checked.svg',
    'radio-unchecked.svg',
    'readings.svg',
    'redo.svg',
    'refresh.svg',
    'remove.svg',
    'rename.svg',
    'researchinfo.svg',
    'rewind.svg',
    'root.svg',
    'ruler.svg',
    'save.svg',
    'screen.svg',
    'scrolltop.svg',
    'search.svg',
    'settings.svg',
    'share.svg',
    'smiley-neutral.svg',
    'smiley-sad.svg',
    'smiley-smile.svg',
    'sort.svg',
    'stop.svg',
    'sun.svg',
    'sunrise.svg',
    'tag.svg',
    'target.svg',
    'text.svg',
    'theme.svg',
    'unchecked.svg',
    'undo.svg',
    'upload.svg',
    'user.svg',
    'valid.svg',
    'video-off.svg',
    'video.svg',
    'volume-high.svg',
    'volume-low.svg',
    'volume-medium.svg',
    'volume-mute.svg',
    'warning.svg',
    'wifi-off.svg',
    'wifi.svg',
    'yes.svg',
    'zoom-in.svg',
    'zoom-out.svg',
];
// ---------------- customize/icon_manager.js ---------------
'use strict';
class IconManager {
    #sets;
    #choice;
    #reader = new IconReader();
    #placer = new IconPlacer();
    #watcher;
    #register = new IconRegister();
    constructor(sets, named = '', watcher = null) {
        this.#sets = sets;
        this.#choice = new IconChoice(sets, named);
        this.#watcher = watcher !== null ? watcher : new IconWatcher();
    }
    // -----------------------------------------------------------------------
    inForce() {
        return this.#choice.inForce();
    }
    names() {
        return this.#sets.names();
    }
    // -----------------------------------------------------------------------
    carried(named = '') {
        const asked = named !== '' ? named : this.#choice.inForce();
        return this.#sets.namesFor(asked);
    }
    // -----------------------------------------------------------------------
    declare(set) {
        this.#sets.declare(set);
    }
    gather(setName, name, markup) {
        this.#reader.gather(setName, name, markup);
    }
    // -----------------------------------------------------------------------
    reference(set) {
        this.#sets.reference(set);
    }
    fallback(name) {
        this.#sets.fallback(name);
    }
    // -----------------------------------------------------------------------
    async get(name) {
        const set = this.#sets.setFor(name, this.#choice.inForce());
        if (set === null) {
            WexaLogger.warn('IconManager: no set carries the name "' + name + '".');
            return '';
        }
        try {
            const content = await this.#reader.read(set, name);
            return content.source;
        } catch (error) {
            this.#say(error);
            return '';
        }
    }
    // -----------------------------------------------------------------------
    async inject(element, name) {
        if (element === null || element === undefined) {
            return;
        }
        if (element.querySelector('svg') !== null) {
            return;
        }
        const markup = await this.get(name);
        if (markup === '') {
            return;
        }
        element.insertAdjacentHTML('afterbegin', markup);
    }
    // -----------------------------------------------------------------------
    async run(root = document) {
        try {
            const demands = [];
            for (const element of root.querySelectorAll(IconDemand.SELECTOR)) {
                const demand = IconDemand.of(element);
                if (demand !== null) {
                    demands.push(demand);
                }
            }
            this.#watcher.watch(demands, demand => this.#answer(demand));
        } catch (error) {
            this.#say(error);
        }
    }
    // -----------------------------------------------------------------------
    async show(name) {
        try {
            if (this.#choice.put(name) === false) {
                return;
            }
            for (const demand of this.#register.held()) {
                await this.#answer(demand);
            }
        } catch (error) {
            this.#say(error);
        }
    }
    // -----------------------------------------------------------------------
    // PRIVATE
    // -----------------------------------------------------------------------
    async #answer(demand) {
        const set = this.#sets.setFor(demand.name, this.#choice.inForce());
        if (set === null) {
            this.#placer.clear(demand);
            this.#register.hold(demand);
            WexaLogger.warn('IconManager: no set carries the name "'
                + demand.name + '".');
            return;
        }
        try {
            // A ground is laid on a surface: it is never written into the page,
            // so it is never read. Its address is what answers.
            const content = demand.kind === DemandKind.SURFACE
                ? this.#reader.address(set, demand.name)
                : await this.#reader.read(set, demand.name);
            this.#placer.place(demand, content);
        } catch (error) {
            this.#placer.clear(demand);
            this.#say(error);
        }
        this.#register.hold(demand);
    }
    // -----------------------------------------------------------------------
    #say(error) {
        if (error instanceof IconError) {
            WexaLogger.error('IconManager: ' + error.message);
            return;
        }
        WexaLogger.error('IconManager: ', error);
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.IconManager = IconManager;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- customize/icons.js ---------------
'use strict';
// Where this file stands, so that a document finds the icons wherever it is
// read from. The build writes null here, the bundle being a classic script:
// there the drawings are gathered in, and no address is ever asked for.
const here = null;
const referenceBase = here === null
    ? 'icons/mono-svg/'
    : new URL('../../icons/mono-svg/', here).href;
const sets = new IconSets();
sets.reference(new IconSet('mono-svg', referenceBase, REFERENCE_FILES));
const icons = new IconManager(sets);
// ---------------- extras/book.js ---------------
'use strict';
class Book {
    // FIELDS
    #tocElement;
    #headingsContainer;
    #htmlTags;
    #toggleButton;
    // CONSTRUCTOR
    constructor(id_headings, id_toc = "toc") {
        this.#tocElement = document.getElementById(id_toc);
        this.#headingsContainer = document.getElementById(id_headings);
        this.#htmlTags = "h1, h2, h3, h4";
        const container = this.#tocElement?.closest('nav, aside');
        if (container instanceof HTMLElement) {
            if (container.classList.contains('book-toc-aside')) {
                this.#setupAside(container);
            } else {
                container.setAttribute('tabindex', '-1');
            }
        }
    }
    // GETTERS
    get domToc() {
        return this.#tocElement;
    }
    get headings() {
        return this.#headingsContainer;
    }
    get htmlTags() {
        return this.#htmlTags;
    }
    // PUBLIC METHODS
    setHeadings(id_headings) {
        this.#headingsContainer =  document.getElementById(id_headings);
    }
    addHtmlTags(...tags) {
        tags.forEach(current => {
            this.#htmlTags += ", " + current
        });
    }
    deleteHtmlTags(...tags) {
        tags.forEach(current => {
            this.#htmlTags = this.#htmlTags.replace(", " + current, "");
        });
    }
    fillTable(only_numerate_headings = true) {
        if (!(this.#tocElement instanceof HTMLElement)) return;
        const headings = this.#getHeadings(only_numerate_headings);
        headings.forEach((heading, index) => {
            /* Add the anchor right before the heading */
            let anchor = document.createElement('a');
            anchor.setAttribute("id", 'toc' + index);
            anchor.setAttribute("name", 'toc' + index);
            /* Add an entry into the table of content */
            let link = document.createElement('a');
            link.setAttribute('href', '#toc' + index);
            link.textContent = heading.textContent;
            let item = document.createElement('li');
            item.setAttribute('class', this.#classOf(heading));
            item.appendChild(link);
            this.#tocElement.appendChild(item);
            heading.parentNode.insertBefore(anchor, heading);
        });
    }
    // PRIVATE METHODS
    #classOf(heading) {
        const level = heading.tagName.toLowerCase();
        if (heading.closest('.chapter.nonumber') === null) {
            return level;
        }
        return level + ' nonumber';
    }
    #setupAside(aside) {
        if (!aside.id) aside.id = 'book-toc-aside';
        // A panel that is set aside is out of reach: 'inert' says it once, for
        // the keyboard as for a screen reader. 'aria-hidden' would say it to
        // the reader alone, and leave the links it holds declared as reachable.
        aside.inert = true;
        const titleEl = aside.querySelector('h1, h2');
        const label = titleEl?.textContent?.trim() || 'Table of contents';
        this.#toggleButton = document.createElement('button');
        this.#toggleButton.className = 'book-toc-toggle';
        this.#toggleButton.setAttribute('aria-controls', aside.id);
        this.#toggleButton.setAttribute('aria-expanded', 'false');
        this.#toggleButton.setAttribute('aria-label', label);
        this.#toggleButton.textContent = label;
        this.#toggleButton.addEventListener('click', () => {
            const isOpen = aside.classList.toggle('open');
            this.#toggleButton.setAttribute('aria-expanded', String(isOpen));
            aside.inert = !isOpen;
            if (isOpen) {
                aside.querySelector('a[href], button')?.focus();
            } else {
                this.#toggleButton.focus();
            }
        });
        this.#placeToggleButton();
        // Browsers do not honour page-break on <aside> elements when printing.
        // Inserting a <section class="blank-page"> immediately after the aside
        // acts as the page-break carrier (print.css targets .blank-page).
        // The empty <p> that follows prevents the section from being collapsed
        // by certain layout engines before the break is applied.
        const blankPage = document.createElement('section');
        blankPage.className = 'blank-page';
        aside.after(blankPage);
        const spacer = document.createElement('p');
        blankPage.after(spacer);
    }
    #placeToggleButton() {
        const bar = document.querySelector('nav');
        if (bar !== null) {
            bar.appendChild(this.#toggleButton);
            return;
        }
        const header = document.querySelector('header');
        if (header !== null) {
            header.appendChild(this.#toggleButton);
            return;
        }
        const main = document.querySelector('main');
        if (main !== null) {
            main.prepend(this.#toggleButton);
            return;
        }
        document.body.prepend(this.#toggleButton);
    }
    #getHeadings(only_numerate_headings) {
        if (!(this.#headingsContainer instanceof HTMLElement)) return [];
        const titles = Array.from(this.#headingsContainer.querySelectorAll(this.#htmlTags));
        let headings = [];
        titles.forEach(current => {
            if (only_numerate_headings) {
                // check if the heading begin by a number
                const c = window.getComputedStyle(current, '::before')['content'];
                if (c && c !== 'none' && c !== '""' && c !== "''") {
                    headings.push(current);
                }
            } else {
                headings.push(current);
            }
        });
        return headings;
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.Book = Book;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/poster.js ---------------
'use strict';
class Poster {
    // CONSTANTS
    static SHORTCUT_KEYS = ['a', 'A'];
    static HIDDEN_CLASS = 'controls-hidden';
    // FIELDS
    #shown;
    #nav;
    #keyboard;
    // CONSTRUCTOR
    constructor(shown = {}) {
        this.#shown = {
            theme: shown.theme !== false,
            contrast: shown.contrast !== false,
            color: shown.color !== false
        };
        this.#nav = null;
        this.#keyboard = null;
    }
    // GETTERS
    get nav() {
        return this.#nav;
    }
    // -----------------------------------------------------------------------
    get visible() {
        if (this.#nav === null) {
            return false;
        }
        return this.#nav.classList.contains(Poster.HIDDEN_CLASS) === false;
    }
    // PUBLIC METHODS
    async init(options = {}) {
        const id = options.id || 'accessibility-controls';
        if (document.getElementById(id) !== null) {
            return null;
        }
        const bar = new AccessibilityNav(this.#shown);
        this.#nav = await bar.build({
            id: id,
            className: options.className || `nav-wexa ${Poster.HIDDEN_CLASS}`,
            label: options.label || 'Accessibility controls'
        });
        document.body.prepend(this.#nav);
        this.#answerKey();
        return this.#nav;
    }
    // -----------------------------------------------------------------------
    show() {
        if (this.#nav !== null) {
            this.#nav.classList.remove(Poster.HIDDEN_CLASS);
        }
    }
    // -----------------------------------------------------------------------
    hide() {
        if (this.#nav !== null) {
            this.#nav.classList.add(Poster.HIDDEN_CLASS);
        }
    }
    // -----------------------------------------------------------------------
    toggle() {
        if (this.visible === true) {
            this.hide();
            return;
        }
        this.show();
    }
    // -----------------------------------------------------------------------
    destroy() {
        if (this.#keyboard !== null) {
            this.#keyboard.destroy();
            this.#keyboard = null;
        }
    }
    // PRIVATE METHODS
    #answerKey() {
        this.#keyboard = new KeyboardController();
        this.#keyboard.register({
            keys: Poster.SHORTCUT_KEYS,
            action: () => this.toggle(),
            label: 'Accessibility controls'
        });
        this.#keyboard.init();
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.Poster = Poster;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/sortatable.js ---------------
class SortaTable {
    // FIELDS
    _tableElt
    _className
    // CONSTRUCTOR
    constructor(tableId) {
        // Name of the CSS class used by the button in the <th> element
        this._className = ".sortatable";
        console.debug("Sortatable is instantiated for table element: ", tableId);
        // The <table> element which is manipulated in this class
        this._tableElt = document.getElementById(tableId);
        if (!this._tableElt) {
            // Table element is not found, log a warning and prevent further execution
            console.warn(`No table element found with id: ${tableId}. SortaTable instantiation is skipped.`);
            return;
        }
        // Store original rows order
        const tbody = this._tableElt.querySelector('tbody');
        const rows = Array.from(tbody.getElementsByTagName('tr'));
        rows.forEach((row, index) => {
            row.setAttribute('data-original-index', index);
        });
    }
    // ----------------------------------------------------------------------
    // PUBLIC
    // ----------------------------------------------------------------------
    getTableId() {
        return this._tableElt.getAttribute("id");
    }
    // ----------------------------------------------------------------------
    attachSortListeners() {
        if (!this._tableElt) {
            return;
        }
        console.debug("Attach sort listeners for table " + this._tableElt);
        // Add event listeners to all headers with class 'sortatable'
        const sortButtons = this._tableElt.querySelectorAll(this._className);
        console.debug("Found " + sortButtons.length + " sort buttons in headers");
        sortButtons.forEach(button => {
            button.addEventListener('click', (event) => {
                console.debug(" ... button: ", `[${button}]`);
                // Retrieve the data-sort attribute from the clicked header
                const sortAttribute = button.getAttribute('data-sort');
                const isAsc = button.classList.contains('sort-asc');
                const isDesc = button.classList.contains('sort-desc');
                // Remove sort classes from all headers to reset the state
                this._tableElt.querySelectorAll(this._className).forEach(h => {
                    h.classList.remove('sort-asc', 'sort-desc');
                });
                // Call the sortTable function to sort the table rows and update button
                // Toggle between 3 states: no sort -> ascending -> descending
                if (isAsc) {
                    button.classList.remove('sort-asc');
                    button.classList.add('sort-desc');
                    this.#sortTable(sortAttribute, false);
                } else if (isDesc) {
                    button.classList.remove('sort-desc');
                    // No sort applied, reset table
                    this.#noSortTable();
                } else {
                    button.classList.add('sort-asc');
                    this.#sortTable(sortAttribute, true);
                }
                event.stopPropagation();
            });
        });
    }
    // ----------------------------------------------------------------------
    sort(column, isAsc = true) {
        // Sort the table based on the specified column
        this.#sortTable(column, isAsc);
        // Optionally, update the class on the header to reflect the current sort direction
        const headerButton = this._tableElt.querySelector(`button[data-sort="${column}"]`);
        if (headerButton) {
            this._tableElt.querySelectorAll(this._className).forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
            });
            headerButton.classList.add(isAsc ? 'sort-asc' : 'sort-desc');
        }
    }
    // ----------------------------------------------------------------------
    toggleColumnVisibility(checkBoxes) {
        // Iterate over each checkbox in checkBoxes
        checkBoxes.forEach(checkbox => {
            // Check if the checkbox has a data-toggle attribute
            const columnName = checkbox.getAttribute('data-toggle');
            if (!columnName) {
                console.warn("Checkbox does not have a data-toggle attribute. Skipping...");
                return; // Skip this checkbox if it doesn't have a data-toggle attribute
            }
            // Initialize column index
            let columnIndex = -1;
            // Iterate through the header cells to find the index
            const headerCells = this._tableElt.querySelectorAll('thead th');
            for (let index = 0; index < headerCells.length; index++) {
                const cell = headerCells[index];
                // Check if the cell has the data-sort attribute matching columnName
                if (cell.getAttribute('data-sort') === columnName) {
                    columnIndex = index; // Store the column index
                    break; // Exit the loop early since we've found the column
                }
                // Find the button with class "sortatable"
                const button = cell.querySelector(this._className);
                // Check if the button exists and matches the column name
                if (button && button.getAttribute('data-sort') === columnName) {
                    columnIndex = index; // Store the column index
                    break; // Exit the loop early since we've found the column
                }
            }
            // If columnIndex is found, toggle its visibility
            if (columnIndex !== -1) {
                // Get the checkbox state (checked or not)
                const checkboxState = checkbox.checked;
                // Use the columnVisibility method to update the visibility
                this.columnVisibility(columnIndex, checkboxState);
                // Optionally recalculate table width after updating visibility
                this._tableElt.style.width = '100%';
            } else {
                console.warn(`Column with name "${columnName}" not found.`);
            }
        });
    }
    // ----------------------------------------------------------------------
    columnVisibility(columnIndex, show) {
        // Get all table rows
        const rows = this._tableElt.rows;
        // Iterate over each row (including header)
        for (let i = 0; i < rows.length; i++) {
            const cell = rows[i].cells[columnIndex];
            if (cell === undefined) {
                continue;
            }
            // A cell spanning several columns belongs to none of them: a row
            // holding one single cell across the whole table says something
            // about the row above it, not about a column. Hiding a column
            // takes away a column, and never that content. Requirement B25.
            if (cell.colSpan > 1) {
                continue;
            }
            // Toggle the 'hidden' class based on the show flag
            if (show) {
                cell.classList.remove('hidden');
            } else {
                cell.classList.add('hidden');
            }
        }
    }
    // ----------------------------------------------------------------------
    // PRIVATE
    // ----------------------------------------------------------------------
    #noSortTable() {
        const tbody = this._tableElt.querySelector('tbody');
        const rows = Array.from(tbody.getElementsByTagName('tr'));
        // Re-organize lines by their original order
        rows.sort((a, b) => a.getAttribute('data-original-index') - b.getAttribute('data-original-index'));
        rows.forEach(row => tbody.appendChild(row));
    }
    // ----------------------------------------------------------------------
    #sortTable(sortAttribute, isAsc) {
        // Get the index of the column to sort by
        const columnIndex = this._tableElt.querySelector(`button[data-sort="${sortAttribute}"]`).closest('th').cellIndex;
        // Get the tbody element from the table
        const tableBody = this._tableElt.querySelector('tbody');
        // Convert the HTMLCollection of rows into an array for sorting
        const rows = Array.from(tableBody.getElementsByTagName('tr'));
        // Check if the attribute to sort by is 'date'
        const isDate = sortAttribute === 'date';
        // Compare according to the language of the page: comparing character
        // by character puts accented words after every other one, which is
        // wrong in every language that uses them.
        const collator = new Intl.Collator(this.#language(), {numeric: true, sensitivity: 'base'});
        // Sort the rows array using a custom comparator
        rows.sort((a, b) => {
            // Fetch the value to sort on for the cells in the current column
            const aValue = SortaTable.#cellValue(a.cells[columnIndex]);
            const bValue = SortaTable.#cellValue(b.cells[columnIndex]);
            // If the attribute is 'date', convert string to Date object
            if (isDate) {
                const aDate = new Date(aValue);
                const bDate = new Date(bValue);
                if (aDate < bDate) return isAsc ? -1 : 1;
                if (aDate > bDate) return isAsc ? 1 : -1;
                return 0;
            }
            const order = collator.compare(aValue, bValue);
            return isAsc ? order : -order;
        });
        // Re-append sorted rows back to the table body
        rows.forEach(row => tableBody.appendChild(row));
    }
    // ----------------------------------------------------------------------
    static #cellValue(cell) {
        // A row may not reach that far: one holding a content that spans the
        // whole table has a single cell. It is sorted as an empty value, and
        // whoever put it there is the one who knows where it belongs.
        if (!cell) {
            return '';
        }
        const declared = cell.getAttribute('data-sort-value');
        if (declared !== null) {
            return declared.trim();
        }
        return cell.textContent.trim();
    }
    // ----------------------------------------------------------------------
    #language() {
        const declaring = this._tableElt.closest('[lang]');
        if (!declaring) {
            return undefined;
        }
        return declaring.getAttribute('lang');
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.SortaTable = SortaTable;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/book/biberrors.js ---------------
'use strict';
class BibliographyError extends Error {
    constructor(message) {
        super(message);
        this.name = 'BibliographyError';
    }
}
class MissingBibtexData extends BibliographyError {
    constructor(message) {
        super(message);
        this.name = 'MissingBibtexData';
    }
}
class MissingBibliographyPlace extends BibliographyError {
    constructor(message) {
        super(message);
        this.name = 'MissingBibliographyPlace';
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.BibliographyError = BibliographyError;
window.Wexa.MissingBibtexData = MissingBibtexData;
window.Wexa.MissingBibliographyPlace = MissingBibliographyPlace;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/book/labels.js ---------------
'use strict';
class Labels {
    // CONSTANTS
    static FALLBACK = 'en';
    // FIELDS
    #labels;
    // CONSTRUCTOR
    constructor(labels) {
        this.#labels = labels;
    }
    // GETTERS
    get language() {
        const declared = document.documentElement.getAttribute('lang');
        if (declared === null) {
            return Labels.FALLBACK;
        }
        const spoken = declared.split('-')[0].toLowerCase();
        if (this.#labels.has(spoken) === false) {
            return Labels.FALLBACK;
        }
        return spoken;
    }
    get isKnown() {
        const declared = document.documentElement.getAttribute('lang');
        if (declared === null) {
            return false;
        }
        return this.#labels.has(declared.split('-')[0].toLowerCase());
    }
    // PUBLIC METHODS
    text(name) {
        return this.#labels.get(this.language)[name];
    }
    write(element, name) {
        element.textContent = this.text(name);
        this.declare(element);
    }
    declare(element) {
        if (this.isKnown === false) {
            element.setAttribute('lang', Labels.FALLBACK);
        }
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.Labels = Labels;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/book/bibauthor.js ---------------
'use strict';
class Author {
    // FIELDS
    #place;
    #firstName;
    #particle;
    #lastName;
    #suffix;
    // CONSTRUCTOR
    constructor(place, firstName, particle, lastName, suffix) {
        this.#place = place;
        this.#firstName = firstName;
        this.#particle = particle;
        this.#lastName = lastName;
        this.#suffix = suffix;
    }
    // GETTERS
    get place() {
        return this.#place;
    }
    get firstName() {
        return this.#firstName;
    }
    get particle() {
        return this.#particle;
    }
    get lastName() {
        return this.#lastName;
    }
    get suffix() {
        return this.#suffix;
    }
    // PUBLIC METHODS
    text() {
        const parts = [this.#firstName, this.#particle, this.#lastName, this.#suffix];
        const written = parts.filter(part => part.length > 0);
        return written.join(' ');
    }
    sortValue() {
        if (this.#lastName.length === 0) {
            return this.text();
        }
        const parts = [this.#firstName, this.#particle];
        const given = parts.filter(part => part.length > 0);
        if (given.length === 0) {
            return this.#lastName;
        }
        return this.#lastName + ', ' + given.join(' ');
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.Author = Author;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/book/biblink.js ---------------
'use strict';
const LinkKind = Object.freeze({
    PDF: 'pdf',
    REPOSITORY: 'repository',
    PUBLISHER: 'publisher',
    OTHER: 'other'
});
class Link {
    // CONSTANTS
    static DEFAULT_REPOSITORY_HOSTS = ['hal.science', 'archives-ouvertes.fr', 'arxiv.org', 'zenodo.org'];
    static PUBLISHER_MARKS = ['doi.org', '/doi/'];
    // FIELDS
    static #repositoryHosts = [...Link.DEFAULT_REPOSITORY_HOSTS];
    #address;
    // PUBLIC STATIC METHODS
    static get repositoryHosts() {
        return [...Link.#repositoryHosts];
    }
    static addRepositoryHosts(...hosts) {
        hosts.forEach(host => {
            if (typeof host !== 'string' || host.length === 0) {
                console.error('Link.addRepositoryHosts: a host must be a string that is not empty.');
                return;
            }
            const known = Link.#repositoryHosts.includes(host);
            if (known === false) {
                Link.#repositoryHosts.push(host);
            }
        });
    }
    static deleteRepositoryHosts(...hosts) {
        hosts.forEach(host => {
            const place = Link.#repositoryHosts.indexOf(host);
            if (place === -1) {
                console.warn(`Link.deleteRepositoryHosts: "${host}" was not known as an archive.`);
                return;
            }
            Link.#repositoryHosts.splice(place, 1);
        });
    }
    static resetRepositoryHosts() {
        Link.#repositoryHosts = [...Link.DEFAULT_REPOSITORY_HOSTS];
    }
    // CONSTRUCTOR
    constructor(address) {
        this.#address = address;
    }
    // GETTERS
    get address() {
        return this.#address;
    }
    // PUBLIC METHODS
    kind() {
        const address = this.#address.toLowerCase();
        if (address.endsWith('.pdf') === true) {
            return LinkKind.PDF;
        }
        if (Link.#containsOneOf(address, Link.#repositoryHosts) === true) {
            return LinkKind.REPOSITORY;
        }
        if (Link.#containsOneOf(address, Link.PUBLISHER_MARKS) === true) {
            return LinkKind.PUBLISHER;
        }
        return LinkKind.OTHER;
    }
    // PRIVATE STATIC METHODS
    static #containsOneOf(address, marks) {
        return marks.some(mark => address.includes(mark));
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.Link = Link;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/book/bibreference.js ---------------
'use strict';
class Reference {
    // FIELDS
    #key;
    #type;
    #fields;
    #authors;
    #links;
    #source;
    // CONSTRUCTOR
    constructor(key, type, fields, authors, links, source) {
        this.#key = key;
        this.#type = type;
        this.#fields = new Map();
        this.#authors = [...authors];
        this.#links = [...links];
        this.#source = source;
        fields.forEach((value, name) => {
            this.#fields.set(name.toLowerCase(), value);
        });
    }
    // GETTERS
    get key() {
        return this.#key;
    }
    get type() {
        return this.#type;
    }
    get authors() {
        return [...this.#authors];
    }
    get links() {
        return [...this.#links];
    }
    get source() {
        return this.#source;
    }
    get sourceWithoutAbstract() {
        return Reference.#withoutField(this.#source, 'abstract');
    }
    get abstract() {
        return this.field('abstract');
    }
    // PUBLIC METHODS
    field(name) {
        const wanted = name.toLowerCase();
        if (this.#fields.has(wanted) === false) {
            return '';
        }
        return this.#fields.get(wanted);
    }
    // PRIVATE STATIC METHODS
    static #withoutField(source, name) {
        const start = source.search(new RegExp('[,{]\\s*' + name + '\\s*=', 'i'));
        if (start === -1) {
            return source;
        }
        // The comma or brace that opens the field is kept: it belongs to what
        // comes before, and taking it away would join two fields into one.
        let position = source.indexOf('=', start) + 1;
        while (position < source.length && /\s/.test(source[position]) === true) {
            position++;
        }
        const end = Reference.#endOfValue(source, position);
        const before = source.substring(0, start + 1);
        const after = source.substring(end);
        // A field written last leaves the comma of the one before it hanging
        // in front of the brace that closes the entry.
        if (after.trim().startsWith('}') === true && before.trimEnd().endsWith(',') === true) {
            return before.trimEnd().slice(0, -1) + after;
        }
        return before + after;
    }
    static #endOfValue(source, start) {
        const opening = source[start];
        let position = start;
        let depth = 0;
        while (position < source.length) {
            const character = source[position];
            if (character === '{') {
                depth++;
            } else if (character === '}') {
                depth--;
                if (depth === 0) {
                    position++;
                    break;
                }
            } else if (character === '"' && opening === '"' && position > start) {
                position++;
                break;
            }
            position++;
        }
        // The comma that follows goes too: the field before it already has one.
        while (position < source.length && /[\s,]/.test(source[position]) === true) {
            position++;
        }
        return position;
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.Reference = Reference;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/book/bibcitedref.js ---------------
'use strict';
class CitedReference {
    // FIELDS
    #number;
    #places;
    // CONSTRUCTOR
    constructor(number, places) {
        this.#number = number;
        this.#places = [...places];
    }
    // GETTERS
    get number() {
        return this.#number;
    }
    get places() {
        return [...this.#places];
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.CitedReference = CitedReference;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/book/bibparser.js ---------------
'use strict';
class BibtexParser {
    // CONSTANTS
    static ACCENTS = new Map([
        ["'", '́'],    // acute
        ['`', '̀'],    // grave
        ['^', '̂'],    // circumflex
        ['"', '̈'],    // diaeresis
        ['~', '̃'],    // tilde
        ['=', '̄'],    // macron
        ['.', '̇'],    // dot above
        ['c', '̧'],    // cedilla
        ['v', '̌'],    // caron
        ['u', '̆'],    // breve
        ['H', '̋'],    // double acute
        ['r', '̊'],    // ring above
        ['k', '̨']     // ogonek
    ]);
    static LETTERS = new Map([
        ['\\AA', 'Å'], ['\\aa', 'å'], ['\\AE', 'Æ'], ['\\ae', 'æ'],
        ['\\OE', 'Œ'], ['\\oe', 'œ'], ['\\ss', 'ß'],
        ['\\O', 'Ø'], ['\\o', 'ø'], ['\\L', 'Ł'], ['\\l', 'ł'],
        ['\\i', 'ı'], ['\\j', 'ȷ']
    ]);
    static ESCAPED = ['&', '%', '$', '#', '_'];
    static LINK_FIELDS = ['url', 'note'];
    // PUBLIC METHODS
    parse(content) {
        const references = new Map();
        let inEntry = false;
        let open = 0;
        let buffer = '';
        let previous = '';
        for (let i = 0; i < content.length; i++) {
            let character = content[i];
            if (open !== 0 && character === '@' && BibtexParser.#startsALine(content, i) === true) {
                console.warn('BibtexParser: a closing brace is missing, the entry is closed by force.');
                character = '}';
                i--;
            }
            if (open === 0 && character === '@') {
                inEntry = true;
            } else if (inEntry === true && character === '{' && previous !== '\\') {
                open++;
            } else if (inEntry === true && character === '}' && previous !== '\\') {
                open--;
                if (open === 0) {
                    inEntry = false;
                    this.#keepEntry(references, buffer);
                    buffer = '';
                }
            }
            if (inEntry === true) {
                buffer += character;
            }
            previous = character;
        }
        // The last entry may have lost its closing brace at the end of the file.
        if (open > 0) {
            console.warn('BibtexParser: the last entry has no closing brace.');
            this.#keepEntry(references, buffer);
        }
        return references;
    }
    // PRIVATE METHODS
    #keepEntry(references, buffer) {
        const reference = this.#parseEntry(buffer + '}');
        if (reference === null) {
            return;
        }
        if (references.has(reference.key) === true) {
            console.warn(`BibtexParser: the key "${reference.key}" is used twice, the second entry wins.`);
        }
        references.set(reference.key, reference);
    }
    #parseEntry(source) {
        const fields = new Map();
        let entry = source.substring(0, source.length - 1);
        while (entry.includes('=') === true) {
            let position = entry.lastIndexOf('=');
            while (position !== -1 && BibtexParser.#isSeparator(entry, position) === false) {
                position = entry.lastIndexOf('=', position - 1);
            }
            if (position === -1) {
                break;
            }
            const value = entry.substring(position + 1);
            entry = entry.substring(0, position);
            const comma = entry.lastIndexOf(',');
            if (comma === -1) {
                break;
            }
            const name = entry.substring(comma + 1).trim().toLowerCase();
            entry = entry.substring(0, comma);
            if (name.length > 0) {
                fields.set(name, this.#cleanValue(value));
            }
        }
        const brace = entry.indexOf('{');
        if (brace === -1) {
            console.warn('BibtexParser: an entry has no opening brace, it is left aside.');
            return null;
        }
        const type = entry.substring(0, brace).trim().replace('@', '');
        const key = entry.substring(brace + 1).trim();
        if (key.length === 0) {
            console.warn('BibtexParser: an entry has no key, it is left aside.');
            return null;
        }
        let authors = [];
        if (fields.has('author') === true) {
            authors = this.#parseAuthors(fields.get('author'));
        }
        return new Reference(key, type, fields, authors, this.#readLinks(fields), source);
    }
    #cleanValue(value) {
        let cleaned = value.trim();
        if (cleaned.endsWith(',') === true) {
            cleaned = cleaned.substring(0, cleaned.length - 1).trim();
        }
        cleaned = BibtexParser.#stripDelimiters(cleaned);
        cleaned = cleaned.replace(/\s+/g, ' ').trim();
        cleaned = this.#decodeLatex(cleaned);
        // Braces that protected a case have done their work; what they
        // protected is left untouched.
        return cleaned.replace(/(^|[^\\])[{}]/g, '$1');
    }
    #decodeLatex(text) {
        let converted = text;
        BibtexParser.LETTERS.forEach((letter, command) => {
            converted = converted.split(command + '{}').join(letter);
            converted = converted.split(command + ' ').join(letter);
            converted = converted.split(command).join(letter);
        });
        const accents = Array.from(BibtexParser.ACCENTS.keys()).map(BibtexParser.#escapeForRegExp).join('');
        const pattern = new RegExp('\\\\([' + accents + '])\\s*\\{?([A-Za-z])\\}?', 'g');
        converted = converted.replace(pattern, (whole, accent, letter) => {
            return letter + BibtexParser.ACCENTS.get(accent);
        });
        BibtexParser.ESCAPED.forEach(character => {
            converted = converted.split('\\' + character).join(character);
        });
        // Two hyphens are how LaTeX writes a range; one hyphen reads better.
        converted = converted.split('--').join('-');
        return converted.normalize('NFC');
    }
    #parseAuthors(value) {
        const written = value.split(' and ');
        const authors = [];
        written.forEach((name, index) => {
            const parts = BibtexParser.#splitName(name.trim());
            authors.push(new Author(index + 1, parts.first, parts.particle, parts.last, parts.suffix));
        });
        return authors;
    }
    #readLinks(fields) {
        const links = [];
        BibtexParser.LINK_FIELDS.forEach(name => {
            if (fields.has(name) === false) {
                return;
            }
            const value = fields.get(name).trim();
            if (value.startsWith('http') === true) {
                links.push(new Link(value));
            }
        });
        return links;
    }
    // PRIVATE STATIC METHODS
    static #isSeparator(entry, position) {
        if (position > 0 && entry[position - 1] === '\\') {
            return false;
        }
        let open = 0;
        for (let i = entry.length - 1; i >= position; i--) {
            if (entry[i] === '{' && entry[i - 1] !== '\\') {
                open++;
            }
            if (entry[i] === '}' && entry[i - 1] !== '\\') {
                open--;
            }
        }
        if (open !== 0) {
            return false;
        }
        let tail = entry.trimEnd();
        if (tail.endsWith(',') === true) {
            tail = tail.substring(0, tail.length - 1).trimEnd();
        }
        if (tail.endsWith('"') === false) {
            return true;
        }
        let found = 0;
        for (let i = entry.length - 1; i >= position; i--) {
            if (entry[i] === '"' && entry[i - 1] !== '\\') {
                found++;
            }
            if (found === 2) {
                return true;
            }
        }
        return false;
    }
    static #stripDelimiters(value) {
        if (value.startsWith('{') === true && value.endsWith('}') === true) {
            return value.substring(1, value.length - 1);
        }
        if (value.startsWith('"') === true && value.endsWith('"') === true) {
            return value.substring(1, value.length - 1);
        }
        return value;
    }
    static #splitName(name) {
        const parts = name.split(',');
        if (parts.length === 1) {
            return BibtexParser.#splitFirstVonLast(name);
        }
        const vonLast = BibtexParser.#splitVonLast(parts[0].trim());
        let suffix = '';
        if (parts.length > 2) {
            suffix = parts[1].trim();
        }
        return {
            first: parts[parts.length - 1].trim(),
            particle: vonLast.particle,
            last: vonLast.last,
            suffix: suffix
        };
    }
    static #splitFirstVonLast(name) {
        const words = name.split(/\s+/).filter(word => word.length > 0);
        if (words.length === 1) {
            return {first: '', particle: '', last: words[0], suffix: ''};
        }
        const lastLower = BibtexParser.#lastLowerCaseWord(words, words.length - 1);
        if (lastLower === -1) {
            return {
                first: words.slice(0, words.length - 1).join(' '),
                particle: '',
                last: words[words.length - 1],
                suffix: ''
            };
        }
        const firstLower = BibtexParser.#firstLowerCaseWord(words, lastLower);
        return {
            first: words.slice(0, firstLower).join(' '),
            particle: words.slice(firstLower, lastLower + 1).join(' '),
            last: words.slice(lastLower + 1).join(' '),
            suffix: ''
        };
    }
    static #splitVonLast(text) {
        const words = text.split(/\s+/).filter(word => word.length > 0);
        if (words.length === 1) {
            return {particle: '', last: words[0]};
        }
        const lastLower = BibtexParser.#lastLowerCaseWord(words, words.length - 1);
        if (lastLower === -1) {
            return {particle: '', last: words.join(' ')};
        }
        const firstLower = BibtexParser.#firstLowerCaseWord(words, lastLower);
        return {
            particle: words.slice(firstLower, lastLower + 1).join(' '),
            last: words.slice(lastLower + 1).join(' ')
        };
    }
    static #lastLowerCaseWord(words, limit) {
        for (let i = limit - 1; i >= 0; i--) {
            if (BibtexParser.#isLowerCase(words[i]) === true) {
                return i;
            }
        }
        return -1;
    }
    static #firstLowerCaseWord(words, lastLower) {
        let start = lastLower;
        while (start > 0 && BibtexParser.#isLowerCase(words[start - 1]) === true) {
            start--;
        }
        return start;
    }
    static #isLowerCase(word) {
        let depth = 0;
        for (const character of word) {
            if (character === '{') {
                depth++;
            } else if (character === '}') {
                depth--;
            } else if (depth === 0 && /[A-Za-zÀ-ÖØ-öø-ÿ]/.test(character) === true) {
                return character === character.toLowerCase();
            }
        }
        return false;
    }
    static #startsALine(content, position) {
        for (let i = position - 1; i >= 0; i--) {
            const character = content[i];
            if (character === '\n') {
                return true;
            }
            if (character !== ' ' && character !== '\t' && character !== '\r') {
                return false;
            }
        }
        return true;
    }
    static #escapeForRegExp(character) {
        return character.replace(/[.*+?^${}()|[\]\\-]/g, '\\$&');
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.BibtexParser = BibtexParser;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/book/bibformatter.js ---------------
'use strict';
class ReferenceFormatter {
    // CONSTANTS
    static TEMPLATES = new Map([
        ['article', [['author', 'year'], ['title'], ['journal', 'volume', 'number', 'pages']]],
        ['inproceedings', [['author', 'year'], ['title'], ['booktitle', 'address', 'publisher', 'pages']]],
        ['conference', [['author', 'year'], ['title'], ['booktitle', 'address', 'publisher', 'pages']]],
        ['incollection', [['author', 'year'], ['title'], ['booktitle', 'editor', 'publisher', 'pages']]],
        ['inbook', [['author', 'year'], ['chapter'], ['title', 'editor', 'publisher', 'pages']]],
        ['book', [['author', 'year'], ['title'], ['editor', 'publisher', 'address']]],
        ['techreport', [['author', 'year'], ['title'], ['institution', 'address']]],
        ['phdthesis', [['author', 'year'], ['title'], ['type', 'school', 'address']]],
        ['mastersthesis', [['author', 'year'], ['title'], ['type', 'school', 'address']]],
        ['unpublished', [['author', 'year'], ['title'], ['note']]],
        ['misc', [['author', 'year'], ['title'], ['howpublished']]]
    ]);
    static FALLBACK_TEMPLATE = [['author', 'year'], ['title'], ['howpublished']];
    static REQUIRED = new Map([
        ['article', ['author', 'title', 'journal', 'year']],
        ['inproceedings', ['author', 'title', 'booktitle', 'year']],
        ['conference', ['author', 'title', 'booktitle', 'year']],
        ['incollection', ['author', 'title', 'booktitle', 'publisher', 'year']],
        ['inbook', ['author', 'title', 'publisher', 'year']],
        ['book', ['title', 'publisher', 'year']],
        ['techreport', ['author', 'title', 'institution', 'year']],
        ['phdthesis', ['author', 'title', 'school', 'year']],
        ['mastersthesis', ['author', 'title', 'school', 'year']],
        ['unpublished', ['author', 'title']],
        ['misc', []]
    ]);
    static FALLBACK_REQUIRED = ['title'];
    static SEPARATOR = ', ';
    static TERMINATOR = '.';
    static YEAR_OPENING = ' (';
    static YEAR_CLOSING = ')';
    static LINE_NAMES = ['authors', 'title', 'source'];
    // PUBLIC METHODS
    format(reference) {
        const fragment = document.createDocumentFragment();
        const required = this.#requiredFor(reference.type);
        let written = 0;
        this.#templateFor(reference.type).forEach((fields, order) => {
            const line = this.#formatLine(reference, fields, required, order);
            if (line === null) {
                return;
            }
            fragment.appendChild(line);
            written++;
        });
        if (written === 0) {
            const line = document.createElement('span');
            line.className = 'bib-line';
            line.appendChild(this.#formatMissing('title'));
            fragment.appendChild(line);
        }
        return fragment;
    }
    // PRIVATE METHODS
    #formatLine(reference, fields, required, order) {
        const line = document.createElement('span');
        line.className = 'bib-line bib-line-' + ReferenceFormatter.LINE_NAMES[order];
        let written = 0;
        fields.forEach(name => {
            const element = this.#formatField(reference, name, required.includes(name));
            if (element === null) {
                return;
            }
            // The year follows the authors in parentheses; every other field
            // follows the one before it after a comma.
            if (name === 'year' && written > 0) {
                line.appendChild(document.createTextNode(ReferenceFormatter.YEAR_OPENING));
                line.appendChild(element);
                line.appendChild(document.createTextNode(ReferenceFormatter.YEAR_CLOSING));
                written++;
                return;
            }
            if (written > 0) {
                line.appendChild(document.createTextNode(ReferenceFormatter.SEPARATOR));
            }
            line.appendChild(element);
            written++;
        });
        if (written === 0) {
            return null;
        }
        line.appendChild(document.createTextNode(ReferenceFormatter.TERMINATOR));
        return line;
    }
    #formatField(reference, name, isRequired) {
        let value = reference.field(name);
        if (name === 'author') {
            value = reference.authors.map(author => author.text()).join(ReferenceFormatter.SEPARATOR);
        }
        if (value.length > 0) {
            const element = document.createElement('span');
            element.className = 'bib-' + name;
            element.textContent = value;
            return element;
        }
        if (isRequired === true) {
            return this.#formatMissing(name);
        }
        return null;
    }
    #formatMissing(name) {
        const element = document.createElement('span');
        element.className = 'bib-missing';
        element.textContent = '[' + name + ']';
        element.setAttribute('title', 'This reference has no ' + name + '.');
        return element;
    }
    #templateFor(type) {
        const wanted = type.toLowerCase();
        if (ReferenceFormatter.TEMPLATES.has(wanted) === false) {
            return ReferenceFormatter.FALLBACK_TEMPLATE;
        }
        return ReferenceFormatter.TEMPLATES.get(wanted);
    }
    #requiredFor(type) {
        const wanted = type.toLowerCase();
        if (ReferenceFormatter.REQUIRED.has(wanted) === false) {
            return ReferenceFormatter.FALLBACK_REQUIRED;
        }
        return ReferenceFormatter.REQUIRED.get(wanted);
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.ReferenceFormatter = ReferenceFormatter;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/book/bibcitedkey.js ---------------
'use strict';
class CitedKey {
    // FIELDS
    #place;
    #writtenKey;
    #reference;
    #targetPage;
    // CONSTRUCTOR
    constructor(place, writtenKey, reference, targetPage) {
        this.#place = place;
        this.#writtenKey = writtenKey;
        this.#reference = reference;
        this.#targetPage = targetPage;
    }
    // GETTERS
    get place() {
        return this.#place;
    }
    get writtenKey() {
        return this.#writtenKey;
    }
    get reference() {
        return this.#reference;
    }
    get targetPage() {
        return this.#targetPage;
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.CitedKey = CitedKey;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/book/bibcitation.js ---------------
'use strict';
class Citation {
    // CONSTANTS
    static ID_PREFIX = 'cite-';
    static OPENING = '[';
    static CLOSING = ']';
    static UNKNOWN = '?';
    static UNBREAKABLE_SPACE = '\u00A0';
    static CONTENT_SUFFIX = '-reference';
    static LABELS = new Map([
        ['en', {reference: 'Reference', missing: 'missing reference'}],
        ['fr', {reference: 'Référence', missing: 'référence absente'}]
    ]);
    // FIELDS
    #element;
    #place;
    #citedKeys;
    #texts;
    // CONSTRUCTOR
    constructor(element, place, citedKeys) {
        this.#element = element;
        this.#place = place;
        this.#citedKeys = [...citedKeys];
        this.#texts = new Labels(Citation.LABELS);
    }
    // GETTERS
    get element() {
        return this.#element;
    }
    get place() {
        return this.#place;
    }
    get citedKeys() {
        return [...this.#citedKeys];
    }
    // PUBLIC METHODS
    showNumber(number) {
        this.#show(Citation.OPENING + String(number) + Citation.CLOSING,
            this.#texts.text('reference') + ' ' + String(number));
    }
    showReference(number, content, target) {
        this.showNumber(number);
        const control = document.createElement('button');
        control.type = 'button';
        control.className = 'bib-disclosure-control bib-citation-control';
        control.setAttribute('aria-expanded', 'false');
        control.setAttribute('aria-controls', this.#element.id + Citation.CONTENT_SUFFIX);
        control.setAttribute('aria-label', this.#element.getAttribute('aria-label'));
        control.textContent = this.#element.textContent;
        this.#texts.declare(control);
        // On paper nothing opens, and a button is neither a link nor
        // clickable in a PDF. The same number is written a second time, as a
        // link to the bibliography, and each of the two shows where it serves.
        const anchor = document.createElement('a');
        anchor.className = 'bib-citation-anchor';
        anchor.setAttribute('href', '#' + target);
        anchor.textContent = control.textContent;
        anchor.setAttribute('aria-label', control.getAttribute('aria-label'));
        this.#texts.declare(anchor);
        this.#element.textContent = '';
        this.#element.removeAttribute('aria-label');
        this.#element.appendChild(control);
        this.#element.appendChild(anchor);
        const opened = document.createElement('span');
        opened.className = 'bib-citation-content';
        opened.id = this.#element.id + Citation.CONTENT_SUFFIX;
        opened.hidden = true;
        opened.appendChild(content);
        this.#element.after(opened);
        return opened;
    }
    showMissing() {
        this.#show(Citation.OPENING + Citation.UNKNOWN + Citation.CLOSING,
            this.#texts.text('missing'));
    }
    // PRIVATE METHODS
    #show(seen, spoken) {
        if (this.#element.id === '') {
            this.#element.id = Citation.ID_PREFIX + String(this.#place);
        }
        this.#element.textContent = seen;
        this.#element.setAttribute('aria-label', spoken);
        this.#texts.declare(this.#element);
        this.#keepWithPreviousWord();
    }
    #keepWithPreviousWord() {
        const before = this.#element.previousSibling;
        if (before === null || before.nodeType !== Node.TEXT_NODE) {
            return;
        }
        before.textContent = before.textContent.replace(/\s+$/, Citation.UNBREAKABLE_SPACE);
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.Citation = Citation;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/book/bibtable.js ---------------
'use strict';
class BibliographyTable {
    // CONSTANTS
    static TABLE_ID = 'bibliography-table';
    static ROW_PREFIX = 'bib-';
    static UNCITED_SORT_VALUE = String(Number.MAX_SAFE_INTEGER);
    static BACK_SEPARATOR = '-';
    static LABELS = new Map([
        ['en', {
            number: 'No.', year: 'Year', reference: 'Reference',
            abstract: 'Abstract', source: 'BibTeX', backTo: 'Back to citation',
            pdf: 'PDF', repository: 'Open archive', publisher: 'Publisher', other: 'Link',
            of: 'of'
        }],
        ['fr', {
            number: 'N°', year: 'Année', reference: 'Référence',
            abstract: 'Résumé', source: 'BibTeX', backTo: 'Retour à la citation',
            pdf: 'PDF', repository: 'Archive ouverte', publisher: 'Éditeur', other: 'Lien',
            of: 'de'
        }]
    ]);
    // FIELDS
    #formatter;
    #texts;
    // CONSTRUCTOR
    constructor(formatter = new ReferenceFormatter()) {
        this.#formatter = formatter;
        this.#texts = new Labels(BibliographyTable.LABELS);
    }
    // PUBLIC METHODS
    build(references, cited) {
        const hasNumbers = cited.size > 0;
        const columns = BibliographyTable.#columnCount(hasNumbers);
        const table = document.createElement('table');
        table.id = BibliographyTable.TABLE_ID;
        table.className = 'bib-table';
        table.appendChild(this.#buildHead(hasNumbers));
        const body = document.createElement('tbody');
        BibliographyTable.#inReadingOrder(references, cited).forEach(reference => {
            const row = this.#buildRow(reference, cited.get(reference.key), hasNumbers);
            body.appendChild(row);
            this.#buildOpenedRows(reference, columns).forEach(opened => body.appendChild(opened));
        });
        table.appendChild(body);
        BibliographyTable.stripe(table);
        return table;
    }
    static stripe(table) {
        let seen = 0;
        table.querySelectorAll('tbody tr.bib-row').forEach(row => {
            if (row.hidden === false) {
                seen++;
            }
            const striped = row.hidden === false && seen % 2 === 0;
            row.classList.toggle('bib-striped', striped);
            const opened = table.querySelectorAll(`tr.bib-opened-row[data-opens="${row.id}"]`);
            opened.forEach(content => content.classList.toggle('bib-striped', striped));
        });
    }
    // PRIVATE METHODS
    #buildHead(hasNumbers) {
        const head = document.createElement('thead');
        const row = document.createElement('tr');
        if (hasNumbers === true) {
            row.appendChild(this.#buildHeader('number', true));
        }
        row.appendChild(this.#buildHeader('year', true));
        row.appendChild(this.#buildHeader('reference', true, 'author'));
        head.appendChild(row);
        return head;
    }
    #buildHeader(name, isSortable, sortName = name) {
        const header = document.createElement('th');
        header.setAttribute('scope', 'col');
        header.className = 'bib-header bib-header-' + name;
        if (isSortable === false) {
            this.#texts.write(header, name);
            return header;
        }
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'sortatable';
        button.setAttribute('data-sort', sortName);
        this.#texts.write(button, name);
        header.appendChild(button);
        return header;
    }
    #buildRow(reference, cited, hasNumbers) {
        const row = document.createElement('tr');
        row.id = BibliographyTable.ROW_PREFIX + reference.key;
        row.className = 'bib-row';
        if (hasNumbers === true) {
            const number = document.createElement('td');
            number.className = 'bib-number';
            number.setAttribute('data-sort-value', BibliographyTable.UNCITED_SORT_VALUE);
            if (cited !== undefined) {
                number.textContent = String(cited.number);
                number.setAttribute('data-sort-value', String(cited.number));
            }
            row.appendChild(number);
        }
        const year = document.createElement('td');
        year.className = 'bib-year';
        year.textContent = reference.field('year');
        row.appendChild(year);
        row.appendChild(this.#buildReferenceCell(reference, cited));
        return row;
    }
    #buildReferenceCell(reference, cited) {
        const cell = document.createElement('td');
        cell.className = 'bib-reference';
        cell.setAttribute('data-sort-value', this.#sortValueOf(reference));
        cell.appendChild(this.#formatter.format(reference));
        cell.appendChild(this.#buildActions(reference, cited));
        return cell;
    }
    #buildActions(reference, cited) {
        const actions = document.createElement('div');
        actions.className = 'bib-actions';
        if (cited !== undefined) {
            actions.appendChild(this.#backLinks(cited.places, cited.number));
        }
        reference.links.forEach(link => {
            actions.appendChild(this.#buildLink(link, reference));
        });
        this.#openableOf(reference).forEach(opened => {
            actions.appendChild(this.#buildControl(reference.key, opened.name));
        });
        return actions;
    }
    #sortValueOf(reference) {
        const authors = reference.authors;
        if (authors.length === 0) {
            return reference.field('title');
        }
        return authors[0].sortValue();
    }
    #backLinks(places, number) {
        const fragment = document.createDocumentFragment();
        places.forEach((place, order) => {
            if (place.id === '') {
                return;
            }
            const mark = Citation.OPENING + String(number) + Citation.CLOSING;
            const suffix = BibliographyTable.#suffixOf(order, places.length);
            const link = document.createElement('a');
            link.className = 'bib-backlink';
            link.setAttribute('href', '#' + place.id);
            link.textContent = mark + suffix;
            link.setAttribute('aria-label', this.#texts.text('backTo') + ' ' + String(number) + suffix);
            this.#texts.declare(link);
            fragment.appendChild(link);
        });
        return fragment;
    }
    #openableOf(reference) {
        const openable = [];
        if (reference.abstract.length > 0) {
            openable.push({name: 'abstract', text: reference.abstract});
        }
        openable.push({name: 'source', text: reference.sourceWithoutAbstract});
        return openable;
    }
    #buildLink(link, reference) {
        const element = document.createElement('a');
        // Every address of a reference leaves the document: the reader is told
        // so before following it, the way Whakerexa marks any outward link.
        element.className = 'bib-link external-link';
        element.setAttribute('href', link.address);
        // A page holding twenty links all named "PDF" is a page where a name
        // says nothing, so each one names its reference.
        const label = BibliographyTable.#labelOf(link.kind());
        element.setAttribute('aria-label', this.#nameOf(label, reference));
        // On screen a reader needs to know what the link leads to; on paper
        // they need the address, and the link is still one in a PDF. Both are
        // written inside the link, and each shows where it serves.
        const shown = document.createElement('span');
        shown.className = 'bib-link-label';
        this.#texts.write(shown, label);
        const address = document.createElement('span');
        address.className = 'bib-link-address';
        address.textContent = link.address;
        this.#texts.declare(address);
        element.appendChild(shown);
        element.appendChild(address);
        return element;
    }
    #nameOf(label, reference) {
        const title = reference.field('title');
        if (title.length === 0) {
            return this.#texts.text(label);
        }
        return this.#texts.text(label) + ' ' + this.#texts.text('of') + ' ' + title;
    }
    #buildControl(key, name) {
        const control = document.createElement('button');
        control.type = 'button';
        control.className = 'bib-disclosure-control';
        control.setAttribute('aria-expanded', 'false');
        control.setAttribute('aria-controls', BibliographyTable.#contentId(key, name));
        this.#texts.write(control, name);
        return control;
    }
    #buildOpenedRows(reference, columns) {
        return this.#openableOf(reference).map(opened => {
            const row = document.createElement('tr');
            row.id = BibliographyTable.#contentId(reference.key, opened.name);
            row.className = 'bib-opened-row';
            row.setAttribute('data-opens', BibliographyTable.ROW_PREFIX + reference.key);
            row.hidden = true;
            const cell = document.createElement('td');
            cell.colSpan = columns;
            cell.className = 'bib-disclosure-content bib-disclosure-' + opened.name;
            cell.textContent = opened.text;
            row.appendChild(cell);
            return row;
        });
    }
    // PRIVATE STATIC METHODS
    static #inReadingOrder(references, cited) {
        const ordered = Array.from(references.values());
        ordered.sort((one, other) => {
            const first = BibliographyTable.#numberOf(one, cited);
            const second = BibliographyTable.#numberOf(other, cited);
            if (first !== second) {
                return first - second;
            }
            return Number(one.field('year')) - Number(other.field('year'));
        });
        return ordered;
    }
    static #numberOf(reference, cited) {
        const owed = cited.get(reference.key);
        if (owed === undefined) {
            return Number.MAX_SAFE_INTEGER;
        }
        return owed.number;
    }
    static #suffixOf(order, total) {
        if (total < 2) {
            return '';
        }
        let letters = '';
        let left = order;
        while (left >= 0) {
            letters = String.fromCharCode(97 + (left % 26)) + letters;
            left = Math.floor(left / 26) - 1;
        }
        return BibliographyTable.BACK_SEPARATOR + letters;
    }
    static #columnCount(hasNumbers) {
        if (hasNumbers === true) {
            return 3;
        }
        return 2;
    }
    static #contentId(key, name) {
        return BibliographyTable.ROW_PREFIX + key + '-' + name;
    }
    static #labelOf(kind) {
        if (kind === LinkKind.PDF) {
            return 'pdf';
        }
        if (kind === LinkKind.REPOSITORY) {
            return 'repository';
        }
        if (kind === LinkKind.PUBLISHER) {
            return 'publisher';
        }
        return 'other';
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.BibliographyTable = BibliographyTable;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/book/bibcite.js ---------------
'use strict';
class CitationIndex {
    // CONSTANTS
    static CITATION_SELECTOR = '[data-bibtex]';
    static KEY_ATTRIBUTE = 'data-bibtex';
    static LABELS = new Map([
        ['en', {inBibliography: 'In the bibliography', abstract: 'Abstract'}],
        ['fr', {inBibliography: 'Dans la bibliographie', abstract: 'Résumé'}]
    ]);
    // FIELDS
    #citations;
    #numbersByKey;
    #placesByKey;
    #formatter;
    #texts;
    // CONSTRUCTOR
    constructor(formatter = new ReferenceFormatter()) {
        this.#citations = [];
        this.#numbersByKey = new Map();
        this.#placesByKey = new Map();
        this.#formatter = formatter;
        this.#texts = new Labels(CitationIndex.LABELS);
    }
    // GETTERS
    get citations() {
        return [...this.#citations];
    }
    // PUBLIC METHODS
    index(root, references) {
        this.#citations = [];
        this.#numbersByKey = new Map();
        this.#placesByKey = new Map();
        if (root === null) {
            console.warn('CitationIndex: no text to read, the citations are not numbered.');
            return;
        }
        const written = root.querySelectorAll(CitationIndex.CITATION_SELECTOR);
        written.forEach((element, order) => {
            const key = element.getAttribute(CitationIndex.KEY_ATTRIBUTE).trim();
            const reference = references.get(key);
            const cited = new CitedKey(1, key, this.#found(reference), '');
            const citation = new Citation(element, order + 1, [cited]);
            this.#citations.push(citation);
            if (cited.reference === null) {
                console.warn(`CitationIndex: the key "${key}" names no reference.`);
                citation.showMissing();
                return;
            }
            citation.showReference(this.#numberOf(key), this.#buildContent(cited.reference),
                BibliographyTable.ROW_PREFIX + key);
            this.#rememberPlace(key, element);
        });
    }
    citedReferences() {
        const cited = new Map();
        this.#numbersByKey.forEach((number, key) => {
            cited.set(key, new CitedReference(number, this.#placesOf(key)));
        });
        return cited;
    }
    // PRIVATE METHODS
    #buildContent(reference) {
        const content = document.createDocumentFragment();
        content.appendChild(this.#formatter.format(reference));
        content.appendChild(this.#buildBibliographyLink(reference.key));
        reference.links.forEach(link => {
            const address = document.createElement('a');
            address.className = 'bib-link external-link';
            address.setAttribute('href', link.address);
            address.textContent = link.address;
            content.appendChild(address);
        });
        if (reference.abstract.length > 0) {
            content.appendChild(this.#buildPart('abstract', reference.abstract));
        }
        return content;
    }
    #buildBibliographyLink(key) {
        const link = document.createElement('a');
        link.className = 'bib-citation-link';
        link.setAttribute('href', '#' + BibliographyTable.ROW_PREFIX + key);
        this.#texts.write(link, 'inBibliography');
        return link;
    }
    #buildPart(name, text) {
        const part = document.createElement('span');
        part.className = 'bib-citation-part bib-citation-' + name;
        const title = document.createElement('b');
        this.#texts.write(title, name);
        part.appendChild(title);
        const written = document.createElement('span');
        written.className = 'bib-citation-text';
        written.textContent = text;
        part.appendChild(written);
        return part;
    }
    #found(reference) {
        if (reference === undefined) {
            return null;
        }
        return reference;
    }
    #numberOf(key) {
        if (this.#numbersByKey.has(key) === false) {
            this.#numbersByKey.set(key, this.#numbersByKey.size + 1);
        }
        return this.#numbersByKey.get(key);
    }
    #rememberPlace(key, element) {
        if (this.#placesByKey.has(key) === false) {
            this.#placesByKey.set(key, []);
        }
        this.#placesByKey.get(key).push(element);
    }
    #placesOf(key) {
        if (this.#placesByKey.has(key) === false) {
            return [];
        }
        return [...this.#placesByKey.get(key)];
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.CitationIndex = CitationIndex;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/book/bibsource.js ---------------
'use strict';
class BibtexSource {
    // FIELDS
    #element;
    #address;
    // CONSTRUCTOR
    constructor(elementId, address = '') {
        this.#element = document.getElementById(elementId);
        this.#address = address;
    }
    // GETTERS
    get element() {
        return this.#element;
    }
    get address() {
        return this.#address;
    }
    // PUBLIC METHODS
    async read() {
        const written = this.#readFromPage();
        if (written.trim().length > 0) {
            return written;
        }
        const fetched = await this.#readFromAddress();
        if (fetched.trim().length > 0) {
            return fetched;
        }
        throw new MissingBibtexData('No BibTeX data, neither in the page nor at an address.');
    }
    // PRIVATE METHODS
    #readFromPage() {
        if (this.#element === null) {
            return '';
        }
        return this.#element.textContent;
    }
    async #readFromAddress() {
        if (this.#address.length === 0) {
            return '';
        }
        const wanted = new URL(this.#address, window.location.href);
        if (wanted.origin !== window.location.origin) {
            console.error(`BibtexSource: "${this.#address}" is on another server, it is not read.`);
            return '';
        }
        const manager = new RequestManager();
        const answer = await manager.sendGetRequest(wanted.pathname.substring(1) + wanted.search);
        if (manager.status !== 200) {
            console.error(`BibtexSource: "${this.#address}" answered ${manager.status}.`);
            return '';
        }
        return answer;
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.BibtexSource = BibtexSource;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/book/bibdisclosure.js ---------------
'use strict';
class ReferenceDisclosure {
    // CONSTANTS
    static CLOSING_CONTROL = '.bib-disclosure-close';
    // FIELDS
    #control;
    #content;
    // CONSTRUCTOR
    constructor(control, content) {
        this.#control = control;
        this.#content = content;
        this.#control.addEventListener('click', () => this.toggle());
        const closing = this.#content.querySelector(ReferenceDisclosure.CLOSING_CONTROL);
        if (closing !== null) {
            closing.addEventListener('click', () => this.close());
        }
    }
    // GETTERS
    get control() {
        return this.#control;
    }
    get content() {
        return this.#content;
    }
    get isOpen() {
        return this.#control.getAttribute('aria-expanded') === 'true';
    }
    // PUBLIC METHODS
    open() {
        this.#control.setAttribute('aria-expanded', 'true');
        this.#content.hidden = false;
    }
    close() {
        this.#control.setAttribute('aria-expanded', 'false');
        this.#content.hidden = true;
        this.#control.focus();
    }
    toggle() {
        if (this.isOpen === true) {
            this.close();
            return;
        }
        this.open();
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.ReferenceDisclosure = ReferenceDisclosure;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/book/bibcontrols.js ---------------
'use strict';
class BibliographyControls {
    // CONSTANTS
    static LABELS = new Map([
        ['en', {
            searchName: 'Search in references',
            shownOne: 'reference shown', shownMany: 'references shown',
            sortedBy: 'sorted by', ascending: 'ascending', descending: 'descending',
            unsorted: 'back to the original order',
            columns: 'Columns visibility:', apply: 'Apply'
        }],
        ['fr', {
            searchName: 'Rechercher dans les références',
            shownOne: 'référence affichée', shownMany: 'références affichées',
            sortedBy: 'rangé par', ascending: 'ordre croissant', descending: 'ordre décroissant',
            unsorted: 'retour à l\'ordre de départ',
            columns: 'Colonnes visibles :', apply: 'Appliquer'
        }]
    ]);
    static NARROW_WIDTH_IN_FONTS = 38.75;
    // FIELDS
    #table;
    #texts;
    #sorter;
    #field;
    #announcement;
    #columns;
    #selector;
    #wasNarrow;
    // CONSTRUCTOR
    constructor(table) {
        this.#table = table;
        this.#texts = new Labels(BibliographyControls.LABELS);
        const search = this.#buildSearch();
        this.#field = search;
        this.#announcement = this.#buildAnnouncement();
        this.#columns = this.#buildColumns();
        const panel = document.createElement('div');
        panel.className = 'wrap-panel bib-controls';
        search.classList.add('wrap-item');
        this.#columns.classList.add('wrap-item');
        panel.appendChild(search);
        panel.appendChild(this.#columns);
        this.#table.before(panel);
        this.#table.before(this.#announcement);
        this.#sorter = new SortaTable(this.#table.id);
        this.#sorter.attachSortListeners();
        this.#watchSortButtons();
        this.#selector = new ToggleSelector(this.#columns.querySelector('details').id);
        this.#wasNarrow = null;
        this.#showColumnsTheWidthAllows();
        // A device turned over changes the width without loading anything: the
        // columns follow it, as they do when the page opens.
        window.addEventListener('resize', () => this.#showColumnsTheWidthAllows());
    }
    // GETTERS
    get field() {
        return this.#field;
    }
    get announcement() {
        return this.#announcement;
    }
    // PUBLIC METHODS
    sortBy(column, isAscending = true) {
        this.#sorter.sort(column, isAscending);
        this.#putOpenedRowsBack();
        BibliographyTable.stripe(this.#table);
        this.#sayHowItIsSorted();
    }
    filter(word) {
        const wanted = BibliographyControls.#simplify(word);
        const rows = this.#table.querySelectorAll('tbody tr.bib-row');
        let shown = 0;
        rows.forEach(row => {
            const found = BibliographyControls.#simplify(this.#textOf(row)).includes(wanted);
            row.hidden = found === false;
            // A content that was left open goes away with its reference, and
            // comes back with it: nobody asked for it to be closed.
            this.#openedRowsOf(row).forEach(opened => {
                opened.hidden = found === false || this.#isOpen(opened) === false;
            });
            if (found === true) {
                shown++;
            }
        });
        BibliographyTable.stripe(this.#table);
        this.#sayHowManyAreShown(shown);
    }
    // PRIVATE METHODS
    #openedRowsOf(row) {
        return Array.from(this.#table.querySelectorAll(`tr.bib-opened-row[data-opens="${row.id}"]`));
    }
    #isOpen(opened) {
        const control = this.#table.querySelector(`[aria-controls="${opened.id}"]`);
        if (control === null) {
            return false;
        }
        return control.getAttribute('aria-expanded') === 'true';
    }
    #textOf(row) {
        const texts = [row.textContent];
        this.#openedRowsOf(row).forEach(opened => texts.push(opened.textContent));
        return texts.join(' ');
    }
    #putOpenedRowsBack() {
        const body = this.#table.querySelector('tbody');
        body.querySelectorAll('tr.bib-row').forEach(row => {
            let previous = row;
            this.#openedRowsOf(row).forEach(opened => {
                previous.after(opened);
                previous = opened;
            });
        });
    }
    #buildSearch() {
        const field = document.createElement('input');
        field.type = 'search';
        field.className = 'bib-search-field';
        // What is searched is the reference, not the whole bibliography: the
        // number and the year are not read by a search. The placeholder says it
        // in the field; the name says it to whoever does not see the field, and
        // stays when the placeholder gives way to the first letter typed.
        field.setAttribute('aria-label', this.#texts.text('searchName'));
        field.setAttribute('placeholder', this.#texts.text('searchName'));
        field.addEventListener('input', () => this.filter(field.value));
        return field;
    }
    #buildColumns() {
        const group = document.createElement('div');
        group.className = 'bib-columns';
        const details = document.createElement('details');
        details.className = 'flex-item';
        details.id = this.#table.id + '-columns';
        const summary = document.createElement('summary');
        summary.className = 'summary-choice';
        const title = document.createElement('span');
        this.#texts.write(title, 'columns');
        summary.appendChild(title);
        const all = document.createElement('button');
        all.type = 'button';
        all.className = 'accordion-action';
        all.setAttribute('data-toggle', '');
        all.setAttribute('aria-label', this.#texts.text('columns'));
        all.appendChild(document.createElement('img'));
        all.addEventListener('click', event => this.#selector.toggleSelection(event));
        all.addEventListener('keydown', event => this.#selector.toggleSelection(event));
        summary.appendChild(all);
        details.appendChild(summary);
        const holder = document.createElement('div');
        const list = document.createElement('ul');
        this.#table.querySelectorAll('thead th').forEach((header, index) => {
            const button = header.querySelector('button.sortatable');
            const name = button === null ? header.getAttribute('data-sort') : button.getAttribute('data-sort');
            if (name === null) {
                return;
            }
            const item = document.createElement('li');
            item.className = 'check-item';
            const box = document.createElement('input');
            box.type = 'checkbox';
            box.id = this.#table.id + '-column-' + name;
            box.checked = true;
            box.setAttribute('data-toggle', name);
            box.setAttribute('aria-labelledby', box.id + '-label');
            const label = document.createElement('label');
            label.id = box.id + '-label';
            label.setAttribute('for', box.id);
            label.textContent = header.textContent.trim();
            item.appendChild(box);
            item.appendChild(label);
            list.appendChild(item);
        });
        holder.appendChild(list);
        details.appendChild(holder);
        const apply = document.createElement('button');
        apply.type = 'button';
        apply.className = 'flex-item';
        apply.setAttribute('aria-label', this.#texts.text('apply'));
        icons.inject(apply, 'valid');
        apply.addEventListener('click', () => this.#applyColumns());
        group.appendChild(details);
        group.appendChild(apply);
        return group;
    }
    #showColumnsTheWidthAllows() {
        const font = parseFloat(getComputedStyle(document.documentElement).fontSize);
        const isNarrow = window.innerWidth < BibliographyControls.NARROW_WIDTH_IN_FONTS * font;
        if (isNarrow === this.#wasNarrow) {
            return;
        }
        this.#wasNarrow = isNarrow;
        this.#selector.getCheckboxes().forEach(box => {
            box.checked = isNarrow === false || box.getAttribute('data-toggle') === 'author';
        });
        this.#applyColumns();
    }
    #applyColumns() {
        this.#sorter.toggleColumnVisibility(this.#selector.getCheckboxes());
    }
    #buildAnnouncement() {
        const region = document.createElement('p');
        region.className = 'bib-announcement';
        region.setAttribute('role', 'status');
        region.setAttribute('aria-live', 'polite');
        return region;
    }
    #watchSortButtons() {
        this.#table.querySelectorAll('button.sortatable').forEach(button => {
            button.addEventListener('click', () => {
                this.#putOpenedRowsBack();
                BibliographyTable.stripe(this.#table);
                this.#sayHowItIsSorted();
            });
        });
    }
    #sayHowItIsSorted() {
        const ascending = this.#table.querySelector('button.sortatable.sort-asc');
        const descending = this.#table.querySelector('button.sortatable.sort-desc');
        if (ascending !== null) {
            this.#announce(`${this.#texts.text('sortedBy')} ${ascending.textContent}, `
                + this.#texts.text('ascending'));
            return;
        }
        if (descending !== null) {
            this.#announce(`${this.#texts.text('sortedBy')} ${descending.textContent}, `
                + this.#texts.text('descending'));
            return;
        }
        this.#announce(this.#texts.text('unsorted'));
    }
    #sayHowManyAreShown(shown) {
        if (shown === 1) {
            this.#announce(`1 ${this.#texts.text('shownOne')}`);
            return;
        }
        this.#announce(`${shown} ${this.#texts.text('shownMany')}`);
    }
    #announce(text) {
        this.#announcement.textContent = text;
        this.#texts.declare(this.#announcement);
    }
    // PRIVATE STATIC METHODS
    static #simplify(text) {
        return text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.BibliographyControls = BibliographyControls;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/book/bibbook.js ---------------
'use strict';
class BookBibliography {
    // FIELDS
    #source;
    #parser;
    #citationIndex;
    #table;
    #placeId;
    #contentId;
    #disclosures;
    #controls;
    // CONSTRUCTOR
    constructor(dataId, placeId = 'bibliography', contentId = 'main-content', address = '') {
        this.#source = new BibtexSource(dataId, address);
        this.#parser = new BibtexParser();
        this.#citationIndex = new CitationIndex();
        this.#table = new BibliographyTable();
        this.#placeId = placeId;
        this.#contentId = contentId;
        this.#disclosures = [];
        this.#controls = null;
    }
    // GETTERS
    get disclosures() {
        return [...this.#disclosures];
    }
    get citationIndex() {
        return this.#citationIndex;
    }
    get controls() {
        return this.#controls;
    }
    // PUBLIC METHODS
    async run() {
        try {
            const content = await this.#source.read();
            const references = this.#parser.parse(content);
            // The citations are numbered before anything else is looked for:
            // they are in the text, and the text is there. A document with
            // nowhere to put its bibliography still reads.
            this.#citationIndex.index(document.getElementById(this.#contentId), references);
            const place = document.getElementById(this.#placeId);
            if (place === null) {
                throw new MissingBibliographyPlace(`No element with id "${this.#placeId}".`);
            }
            const table = this.#table.build(references, this.#citationIndex.citedReferences());
            // The identifier comes from the place, which is unique by
            // definition: a page may hold more than one bibliography, and
            // sorting one must not reach the other.
            table.id = this.#placeId + '-table';
            place.textContent = '';
            place.appendChild(table);
            // What opens is written in two places: in the table, and in the
            // sentences that cite. Both are tied to what opens them the same way.
            this.#disclosures = this.#buildDisclosures(
                [place, document.getElementById(this.#contentId)]);
            this.#controls = new BibliographyControls(place.querySelector('table'));
        } catch (error) {
            if (error instanceof BibliographyError) {
                this.#report(error);
                return;
            }
            throw error;
        }
    }
    // PRIVATE METHODS
    #buildDisclosures(roots) {
        const disclosures = [];
        const controls = new Set();
        // One of the roots holds the other: the bibliography stands in the
        // content of the document. A control met twice would be tied twice,
        // and a click would open and close it in the same breath.
        roots.forEach(root => {
            if (root === null) {
                return;
            }
            root.querySelectorAll('.bib-disclosure-control[aria-controls]').forEach(control => {
                controls.add(control);
            });
        });
        controls.forEach(control => {
            const content = document.getElementById(control.getAttribute('aria-controls'));
            if (content === null) {
                console.error(`BookBibliography: the control of "${control.textContent}" opens nothing.`);
                return;
            }
            disclosures.push(new ReferenceDisclosure(control, content));
        });
        return disclosures;
    }
    #report(error) {
        console.error(`BookBibliography: ${error.message}`);
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.BookBibliography = BookBibliography;
// ---- END AUTO-GENERATED EXPORTS ----


// ---------------- extras/keypiano/keypiano.js ---------------
// --------------------------------------------------------------------------
// Constants
// --------------------------------------------------------------------------
const CSS_GROUP = 'wexa-key-piano-group';
const CSS_KEY = 'wexa-key-piano-key';
const CSS_CONTROLS = 'wexa-key-piano-controls';
const CSS_CONTROL = 'wexa-key-piano-control';
const CSS_STATUS = 'wexa-key-piano-status';
const MODE_RADIO = 'radio';
const MODE_FREE = 'free';
const DEFAULT_GROUP_SEP = '-';
const DEFAULT_KEY_SEP = '.';
const DEFAULT_BACKSPACE_LABEL = 'Delete last key';
const DEFAULT_CLEAR_LABEL = 'Clear all';
// --------------------------------------------------------------------------
class KeyPiano {
    static #BACKSPACE_ICON = 'backward';
    static #CLEAR_ICON = 'cancel';
    // Fields
    #container;
    #targetField;
    #groupSep;
    #keySep;
    #groups;
    #history;
    #buffer;
    #currentTurn;
    #freeClickCount;
    #statusElt;
    #instanceId;
    constructor(container) {
        if ((container instanceof HTMLElement) === false) {
            throw new Error(`KeyPiano instantiation failed: container is not an HTMLElement. Got ${container}.`);
        }
        this.#container = container;
        this.#instanceId = container.id.length > 0 ? container.id : `key-piano-${Math.random().toString(36).slice(2)}`;
        this.#targetField = document.getElementById(container.dataset.target);
        if (this.#targetField === null) {
            throw new Error(`KeyPiano instantiation failed: no target field found with `
                + `id: ${container.dataset.target}.`);
        }
        this.#groupSep = container.dataset.groupSep ?? DEFAULT_GROUP_SEP;
        this.#keySep = container.dataset.keySep ?? DEFAULT_KEY_SEP;
        this.#groups = Array.from(container.querySelectorAll(`.${CSS_GROUP}`));
        this.#history = [];
        this.#buffer = new Array(this.#groups.length).fill(null);
        this.#currentTurn = 0;
        this.#freeClickCount = 0;
        this.#setupGroups();
        this.#applyGating();
        this.#injectControls();
        this.#injectStatus();
        WexaLogger.debug(`KeyPiano: activated on #${this.#instanceId} with ${this.#groups.length} group(s).`);
    }
    // ------------------------------------------------------------------
    // Retargeting
    // ------------------------------------------------------------------
    setTarget(fieldId) {
        const field = document.getElementById(fieldId);
        if (field === null) {
            throw new Error(`KeyPiano.setTarget failed: no field found with id: ${fieldId}.`);
        }
        this.#targetField = field;
        this.#history = [];
        this.#freeClickCount = 0;
        this.#resetCycle();
    }
    // ------------------------------------------------------------------
    // Setup
    // ------------------------------------------------------------------
    #setupGroups() {
        this.#groups.forEach((group, index) => {
            const mode = group.dataset.mode === MODE_RADIO ? MODE_RADIO : MODE_FREE;
            group.dataset.mode = mode;
            if (mode === MODE_RADIO) {
                this.#setupRadioGroup(group, index);
            } else {
                this.#setupFreeGroup(group);
            }
        });
    }
    // ------------------------------------------------------------------
    #setupRadioGroup(group, index) {
        const groupName = `${this.#instanceId}-group-${index}`;
        const radios = group.querySelectorAll('input[type="radio"]');
        radios.forEach((radio) => {
            radio.name = groupName;
            radio.addEventListener('change', () => this.#handleRadioChange(index, radio.value));
        });
        if (radios.length === 0) {
            WexaLogger.warn(`KeyPiano: group ${index} is declared "radio" but has no radio input.`);
        }
    }
    // ------------------------------------------------------------------
    #setupFreeGroup(group) {
        const buttons = group.querySelectorAll(`button.${CSS_KEY}`);
        buttons.forEach((button) => {
            button.addEventListener('click', () => this.#handleFreeClick(button.value));
        });
        if (buttons.length === 0) {
            WexaLogger.warn('KeyPiano: a "free" group has no button key.');
        }
    }
    // ------------------------------------------------------------------
    // Radio groups: turn-taking
    // ------------------------------------------------------------------
    #handleRadioChange(index, value) {
        this.#buffer[index] = value;
        if (index === this.#currentTurn) {
            this.#currentTurn += 1;
        }
        this.#applyGating();
        const isCycleComplete = this.#groups.every((group, i) => {
            return group.dataset.mode !== MODE_RADIO || this.#buffer[i] !== null;
        });
        if (isCycleComplete === true) {
            const composedKey = this.#buffer.join(this.#groupSep);
            this.#appendToTarget(composedKey);
            this.#announce(`Key added: ${composedKey}`);
            this.#resetCycle();
        }
    }
    // ------------------------------------------------------------------
    #applyGating() {
        this.#groups.forEach((group, index) => {
            if (group.dataset.mode !== MODE_RADIO) {
                return;
            }
            const radios = group.querySelectorAll('input[type="radio"]');
            radios.forEach((radio) => {
                radio.disabled = index !== this.#currentTurn;
            });
        });
    }
    // ------------------------------------------------------------------
    #resetCycle() {
        this.#buffer = new Array(this.#groups.length).fill(null);
        this.#currentTurn = 0;
        this.#groups.forEach((group) => {
            group.querySelectorAll('input[type="radio"]:checked').forEach((radio) => {
                radio.checked = false;
            });
        });
        this.#applyGating();
    }
    // ------------------------------------------------------------------
    // Free groups: immediate append
    // ------------------------------------------------------------------
    #handleFreeClick(value) {
        const isCycleStart = this.#freeClickCount % this.#groups.length === 0;
        const separator = isCycleStart ? this.#keySep : this.#groupSep;
        this.#freeClickCount += 1;
        this.#appendToTarget(value, separator);
        this.#announce(`Added: ${value}`);
    }
    // ------------------------------------------------------------------
    // Target field: append, undo, clear
    // ------------------------------------------------------------------
    #appendToTarget(value, separator) {
        const sep = typeof separator === 'string' ? separator : this.#keySep;
        this.#history.push(this.#targetField.value);
        this.#setTargetValue(this.#targetField.value.length === 0
            ? value
            : this.#targetField.value + sep + value);
    }
    // ------------------------------------------------------------------
    #setTargetValue(value) {
        this.#targetField.value = value;
        this.#targetField.dispatchEvent(new Event('input', {bubbles: true}));
    }
    // ------------------------------------------------------------------
    #handleBackspace() {
        if (this.#currentTurn > 0) {
            const index = this.#currentTurn - 1;
            const group = this.#groups[index];
            group.querySelectorAll('input[type="radio"]:checked').forEach((radio) => {
                radio.checked = false;
            });
            this.#buffer[index] = null;
            this.#currentTurn = index;
            this.#applyGating();
            this.#announce('Last key selection undone.');
            return;
        }
        if (this.#history.length === 0) {
            this.#announce('Nothing to undo.');
            return;
        }
        this.#setTargetValue(this.#history.pop());
        this.#announce('Last entry deleted.');
    }
    // ------------------------------------------------------------------
    #handleClear() {
        this.#setTargetValue('');
        this.#history = [];
        this.#freeClickCount = 0;
        this.#resetCycle();
        this.#announce('Everything cleared.');
    }
    // ------------------------------------------------------------------
    // Injected controls: "delete last key", "clear all", live status
    // ------------------------------------------------------------------
    async #injectControls() {
        const backspaceLabel = this.#container.dataset.backspaceLabel ?? DEFAULT_BACKSPACE_LABEL;
        const clearLabel = this.#container.dataset.clearLabel ?? DEFAULT_CLEAR_LABEL;
        const backspaceButton = await this.#createControlButton(
            KeyPiano.#BACKSPACE_ICON, backspaceLabel, () => this.#handleBackspace());
        backspaceButton.classList.add(`${CSS_CONTROL}-backspace`);
        const clearButton = await this.#createControlButton(
            KeyPiano.#CLEAR_ICON, clearLabel, () => this.#handleClear());
        clearButton.classList.add(`${CSS_CONTROL}-clear`);
        // The outer container is a column flex (one row per group): both
        // controls are wrapped in their own row, same idiom as the
        // accessibility buttons sitting side by side in their <nav> section.
        const controls = document.createElement('div');
        controls.classList.add(CSS_CONTROLS);
        controls.appendChild(backspaceButton);
        controls.appendChild(clearButton);
        this.#container.appendChild(controls);
    }
    // ------------------------------------------------------------------
    async #createControlButton(iconName, label, onClick) {
        const button = document.createElement('button');
        button.type = 'button';
        button.classList.add(CSS_CONTROL);
        button.setAttribute('aria-label', label);
        button.addEventListener('click', onClick);
        button.innerHTML = await icons.get(iconName);
        return button;
    }
    // ------------------------------------------------------------------
    #injectStatus() {
        this.#statusElt = document.createElement('div');
        this.#statusElt.classList.add(CSS_STATUS);
        this.#statusElt.setAttribute('role', 'status');
        this.#statusElt.setAttribute('aria-live', 'polite');
        this.#container.appendChild(this.#statusElt);
    }
    // ------------------------------------------------------------------
    #announce(message) {
        this.#statusElt.textContent = message;
    }
}
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.KeyPiano = KeyPiano;
// ---- END AUTO-GENERATED EXPORTS ----


// ------------- SVG icons (gathered in, for a document on a disk) ------------
IconReader.gather('mono-svg', 'accessibility', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <circle cx=\"16\" cy=\"8\" r=\"3\" />\n  <path d=\"M8 15h16\" />\n  <path d=\"M16 15v10\" />\n  <path d=\"M10 25l2-6\" />\n  <path d=\"M22 25l-2-6\" />\n</svg>\n");
IconReader.gather('mono-svg', 'add', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <line x1=\"16\" y1=\"7\" x2=\"16\" y2=\"25\" />\n  <line x1=\"7\" y1=\"16\" x2=\"25\" y2=\"16\" />\n</svg>\n");
IconReader.gather('mono-svg', 'anonymous', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <circle cx=\"16\" cy=\"11\" r=\"5\" />\n  <path d=\"M5 27c0-5 5-8 11-8s11 3 11 8\" />\n  <line x1=\"8\" y1=\"8\" x2=\"24\" y2=\"24\" />\n</svg>");
IconReader.gather('mono-svg', 'arrow-down', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <line x1=\"16\" y1=\"5\" x2=\"16\" y2=\"27\" />\n  <polyline points=\"8 19 16 27 24 19\" />\n</svg>\n");
IconReader.gather('mono-svg', 'arrow-left', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <line x1=\"27\" y1=\"16\" x2=\"5\" y2=\"16\" />\n  <polyline points=\"13 8 5 16 13 24\" />\n</svg>\n");
IconReader.gather('mono-svg', 'arrow-right', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <line x1=\"5\" y1=\"16\" x2=\"27\" y2=\"16\" />\n  <polyline points=\"19 8 27 16 19 24\" />\n</svg>\n");
IconReader.gather('mono-svg', 'arrow-up', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <line x1=\"16\" y1=\"27\" x2=\"16\" y2=\"5\" />\n  <polyline points=\"8 13 16 5 24 13\" />\n</svg>\n");
IconReader.gather('mono-svg', 'audio', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <polygon points=\"7 12 12 12 17 7 17 25 12 20 7 20 7 12\"/>\n  <path d=\"M21 11.333a6.7 7 0 0 1 0 9\"/>\n</svg>\n\n\n");
IconReader.gather('mono-svg', 'back', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n    <path d=\"M20 28 L8 16 L20 4 Z\" />\n</svg>");
IconReader.gather('mono-svg', 'backward', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <polyline points=\"20 24 12 16 20 8\" />\n</svg>");
IconReader.gather('mono-svg', 'bell-off', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M24 11a8 8 0 0 0-16 0c0 9-4 8-4 11h24c0-3-4-1-4-11\" />\n  <path d=\"M18 28a3 3 0 0 1-5 0\" />\n  <line x1=\"5\" y1=\"5\" x2=\"27\" y2=\"27\" />\n</svg>\n");
IconReader.gather('mono-svg', 'bell', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" stroke=\"currentColor\" fill=\"none\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M24 11a8 8 0 0 0-16 0c0 9-4 8-4 11h24c0-3-4-1-4-11\" />\n  <path d=\"M18 28a3 3 0 0 1-5 0\" />\n</svg>");
IconReader.gather('mono-svg', 'book-open', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M4 6h10a4 4 0 0 1 4 4v16a4 4 0 0 0-4-4H4z\"/>\n  <path d=\"M28 6H18a4 4 0 0 0-4 4v16a4 4 0 0 1 4-4h10z\"/>\n</svg>\n");
IconReader.gather('mono-svg', 'book', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"5\" y=\"3\" width=\"18\" height=\"26\" rx=\"2\" />\n  <line x1=\"11\" y1=\"3\" x2=\"11\" y2=\"29\" />\n  <line x1=\"15\" y1=\"10\" x2=\"20\" y2=\"10\" />\n  <line x1=\"15\" y1=\"16\" x2=\"20\" y2=\"16\" />\n  <line x1=\"15\" y1=\"22\" x2=\"20\" y2=\"22\" />\n</svg>\n");
IconReader.gather('mono-svg', 'box', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M3 10L16 3L29 10V22L16 29L3 22z\" />\n  <line x1=\"3\" y1=\"10\" x2=\"16\" y2=\"17\" />\n  <line x1=\"29\" y1=\"10\" x2=\"16\" y2=\"17\" />\n  <line x1=\"16\" y1=\"17\" x2=\"16\" y2=\"29\" />\n  <line x1=\"9.5\" y1=\"6.5\" x2=\"22.5\" y2=\"13.5\" />\n</svg>\n");
IconReader.gather('mono-svg', 'broom', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <line x1=\"27\" y1=\"5\" x2=\"17\" y2=\"15\" />\n  <path d=\"M17 15l-6 6 6 6 6-6-6-6z\" />\n  <line x1=\"11\" y1=\"21\" x2=\"8\" y2=\"24\" />\n  <line x1=\"14\" y1=\"24\" x2=\"11\" y2=\"27\" />\n  <line x1=\"17\" y1=\"27\" x2=\"14\" y2=\"30\" />\n</svg>\n");
IconReader.gather('mono-svg', 'cadenas-open', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"7\" y=\"15\" width=\"19\" height=\"13\" rx=\"3\" />\n  <path d=\"M11 15V9a5 5 0 0 1 11 0\" />\n</svg>\n");
IconReader.gather('mono-svg', 'cadenas', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" stroke=\"currentColor\" fill=\"none\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"7\" y=\"15\" width=\"19\" height=\"13\" rx=\"3\" />\n  <path d=\"M11 15V9a5 5 0 0 1 11 0v5\" />\n</svg>");
IconReader.gather('mono-svg', 'calendar', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"5\" y=\"7\" width=\"22\" height=\"20\" rx=\"2\" />\n  <line x1=\"5\" y1=\"13\" x2=\"27\" y2=\"13\" />\n  <line x1=\"11\" y1=\"4\" x2=\"11\" y2=\"8\" />\n  <line x1=\"21\" y1=\"4\" x2=\"21\" y2=\"8\" />\n</svg>\n");
IconReader.gather('mono-svg', 'cancel', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\"  fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n\t<circle cx=\"16\" cy=\"16\" r=\"10\" />\n\t<line x1=\"10\" y1=\"22\" x2=\"22\" y2=\"10\" />\n</svg>");
IconReader.gather('mono-svg', 'checked', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M10 27H22C24 27 25 27 25 26C26 26 26 26 26 25C27 25 27 24 27 22V10C27 8 27 7 26 7C26 6 26 6 25 6C25 5 24 5 22 5H10C8 5 7 5 7 6C6 6 6 6 6 7C5 7 5 8 5 10V22C5 24 5 25 6 25C6 26 6 26 7 26C7 27 8 27 10 27Z M11 17L14 20L21 12\" />\n</svg>\n");
IconReader.gather('mono-svg', 'chevron-down', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <polyline points=\"8 13 16 21 24 13\" />\n</svg>\n");
IconReader.gather('mono-svg', 'chevron-left', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <polyline points=\"21 8 13 16 21 24\" />\n</svg>\n");
IconReader.gather('mono-svg', 'chevron-right', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <polyline points=\"11 8 19 16 11 24\" />\n</svg>\n");
IconReader.gather('mono-svg', 'chevron-up', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <polyline points=\"8 21 16 13 24 21\" />\n</svg>\n");
IconReader.gather('mono-svg', 'clip', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M28.6 14.7l-12.3 12.3a8 8 0 0 1-11.3-11.3l12.3-12.3a5.3 5.3 0 0 1 7.5 7.5l-12.3 12.3a2.7 2.7 0 0 1-3.8-3.8l11.3-11.3\" />\n</svg>\n");
IconReader.gather('mono-svg', 'clipboard', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M12 6H9a2 2 0 0 0-2 2v18a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-3\" />\n  <rect x=\"12\" y=\"3\" width=\"8\" height=\"6\" rx=\"1.5\" />\n</svg>\n");
IconReader.gather('mono-svg', 'clock', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <circle cx=\"16\" cy=\"16\" r=\"12\" />\n  <polyline points=\"16 8 16 16 22 19\" />\n</svg>\n");
IconReader.gather('mono-svg', 'close', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <line x1=\"9\" y1=\"9\" x2=\"23\" y2=\"23\" />\n  <line x1=\"23\" y1=\"9\" x2=\"9\" y2=\"23\" />\n</svg>\n");
IconReader.gather('mono-svg', 'cloud-off', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M9 25a6 6 0 0 1 0-12 8 8 0 0 1 15-2 5.5 5.5 0 0 1-1 14H9z\" />\n  <line x1=\"5\" y1=\"5\" x2=\"27\" y2=\"27\" />\n</svg>\n");
IconReader.gather('mono-svg', 'cloud', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M9 25a6 6 0 0 1 0-12 8 8 0 0 1 15-2 5.5 5.5 0 0 1-1 14H9z\" />\n</svg>\n");
IconReader.gather('mono-svg', 'color', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" \n\t  fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <!-- Outer circle -->\n  <circle cx=\"16\" cy=\"16\" r=\"13\"/>\n  <!-- Diagonal half fill -->\n  <clipPath id=\"cut\">\n\t<polygon points=\"0,32 32,0 32,32\"/>\n  </clipPath>\n  <circle cx=\"16\" cy=\"16\" r=\"13\" fill=\"currentColor\" clip-path=\"url(#cut)\" stroke=\"none\"/>\n</svg>");
IconReader.gather('mono-svg', 'compas', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <!-- Outer circle -->\n  <circle cx=\"16\" cy=\"16\" r=\"13\"/>\n\n  <!-- Compass ticks -->\n  <line x1=\"16\" y1=\"2\" x2=\"16\" y2=\"4\"/>\n  <line x1=\"16\" y1=\"28\" x2=\"16\" y2=\"30\"/>\n  <line x1=\"2\" y1=\"16\" x2=\"4\" y2=\"16\"/>\n  <line x1=\"28\" y1=\"16\" x2=\"30\" y2=\"16\"/>\n\n  <!-- Needle (angled ~30\u00b0) -->\n  <polygon points=\"18 8 22 18 14 24 10 14\"/>\n  <circle cx=\"16\" cy=\"16\" r=\"1\"/>\n</svg>\n\n");
IconReader.gather('mono-svg', 'compress', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <polyline points=\"12 8 6 16 12 24\" />\n  <polyline points=\"20 8 26 16 20 24\" />\n</svg>\n");
IconReader.gather('mono-svg', 'congrats', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <circle cx=\"16\" cy=\"11\" r=\"8\" />\n  <path d=\"M11 19l-3 8 8-4 8 4-3-8\" />\n</svg>");
IconReader.gather('mono-svg', 'content', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <circle cx=\"7\" cy=\"16\" r=\"2\" />\n  <circle cx=\"16\" cy=\"16\" r=\"2\" />\n  <circle cx=\"25\" cy=\"16\" r=\"2\" />\n</svg>");
IconReader.gather('mono-svg', 'contrast', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" aria-label=\"Contrast switcher icon\" stroke-linejoin=\"round\">\n  <path d=\"M2 16s4-8 14-8 14 8 14 8-4 8-14 8S2 16 2 16z\"/>\n  <!-- text x=\"16\" y=\"20\" font-size=\"13\" text-anchor=\"middle\" fill=\"currentColor\" font-family=\"Commissioner, sans-serif\">A</text -->\n  <!-- Letter A drawn with three lines -->\n  <line x1=\"13\" y1=\"20\" x2=\"16\" y2=\"12\"/>\n  <line x1=\"19\" y1=\"20\" x2=\"16\" y2=\"12\"/>\n  <line x1=\"14\" y1=\"18\" x2=\"18\" y2=\"18\"/>\n  \n  <!-- Plus sign (top-left) -->\n  <line x1=\"5.5\" y1=\"5.5\" x2=\"5.5\" y2=\"8.5\"/>\n  <line x1=\"4\" y1=\"7\" x2=\"7\" y2=\"7\"/>\n\n  <!-- Minus sign (bottom-right) -->\n  <line x1=\"25\" y1=\"25\" x2=\"28\" y2=\"25\"/>\n</svg>");
IconReader.gather('mono-svg', 'copy', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"11\" y=\"11\" width=\"16\" height=\"16\" rx=\"2\" />\n  <path d=\"M23 11V7a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h4\" />\n</svg>\n");
IconReader.gather('mono-svg', 'cursor-hand', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M11 20V9a2.5 2.5 0 0 1 5 0v7\" />\n  <path d=\"M16 13.5a2.5 2.5 0 0 1 5 0V17\" />\n  <path d=\"M21 15.5a2.5 2.5 0 0 1 5 0V22a7 7 0 0 1-7 7h-3a7 7 0 0 1-5-2l-4-4a2.5 2.5 0 0 1 3.5-3.5L11 21\" />\n</svg>\n");
IconReader.gather('mono-svg', 'cursor-text', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <line x1=\"16\" y1=\"6\" x2=\"16\" y2=\"26\" />\n  <path d=\"M12 6h8\" />\n  <path d=\"M12 26h8\" />\n</svg>\n");
IconReader.gather('mono-svg', 'cursor', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M8 4l17 14-7.5 1 3.5 7.5-3.5 1.5-3.5-7.5-6 5V4z\" />\n</svg>\n");
IconReader.gather('mono-svg', 'dashboard', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\"\n     stroke=\"currentColor\"\n     fill=\"none\"\n     stroke-width=\"2\"\n     stroke-linecap=\"round\"\n     stroke-linejoin=\"round\">\n  <rect x=\"5\" y=\"5\" width=\"8\" height=\"21\" rx=\"1\" />\n  <rect x=\"19\" y=\"5\" width=\"8\" height=\"8\" rx=\"1\" />\n  <rect x=\"19\" y=\"19\" width=\"8\" height=\"8\" rx=\"1\" />\n</svg>");
IconReader.gather('mono-svg', 'delete', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <line x1=\"5\" y1=\"9\" x2=\"27\" y2=\"9\" />\n  <path d=\"M12 9V6a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v3\" />\n  <path d=\"M8 9l1.5 17a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2L24 9\" />\n  <line x1=\"14\" y1=\"14\" x2=\"14\" y2=\"23\" />\n  <line x1=\"18\" y1=\"14\" x2=\"18\" y2=\"23\" />\n</svg>\n");
IconReader.gather('mono-svg', 'discovery', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <circle cx=\"9\" cy=\"21\" r=\"6\" />\n  <circle cx=\"23\" cy=\"21\" r=\"6\" />\n  <path d=\"M9 15V8a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v7\" />\n  <path d=\"M17 15V8a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v7\" />\n  <line x1=\"15\" y1=\"19\" x2=\"17\" y2=\"19\" />\n</svg>\n");
IconReader.gather('mono-svg', 'dislike', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <g transform=\"translate(0, 32) scale(1, -1)\">\n    <path d=\"M10 27V14h4l5-9a3 3 0 0 1 3 4l-1.5 5h6a2 2 0 0 1 2 2.5l-2 8a3 3 0 0 1-3 2.5H10z\" />\n    <rect x=\"4\" y=\"14\" width=\"6\" height=\"13\" rx=\"1.5\" />\n  </g>\n</svg>\n");
IconReader.gather('mono-svg', 'download', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M16 5v16\"/>\n  <polyline points=\"10 15 16 21 22 15\"/>\n  <line x1=\"6\" y1=\"27\" x2=\"26\" y2=\"27\"/>\n</svg>\n");
IconReader.gather('mono-svg', 'edit', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M22 4.7a2.8 2.8 0 0 1 4 4L9.3 25.3 4 26.7l1.3-5.3L22 4.7z\" />\n  <line x1=\"19.2\" y1=\"7.5\" x2=\"23.2\" y2=\"11.5\" />\n</svg>\n");
IconReader.gather('mono-svg', 'error', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <circle cx=\"16\" cy=\"16\" r=\"13\" />\n  <line x1=\"11\" y1=\"11\" x2=\"21\" y2=\"21\" />\n  <line x1=\"21\" y1=\"11\" x2=\"11\" y2=\"21\" />\n</svg>\n");
IconReader.gather('mono-svg', 'export', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M27 8V7a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v18a2 2 0 0 0 2 2h18a2 2 0 0 0 2-2v-1\" />\n  <line x1=\"13\" y1=\"16\" x2=\"29\" y2=\"16\" />\n  <polyline points=\"24 11 29 16 24 21\" />\n</svg>\n");
IconReader.gather('mono-svg', 'external-link', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M25 18v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h7\" />\n  <polyline points=\"20 5 27 5 27 12\" />\n  <line x1=\"14\" y1=\"18\" x2=\"27\" y2=\"5\" />\n</svg>\n");
IconReader.gather('mono-svg', 'eye-off', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M2 16s4-8 14-8 14 8 14 8-4 8-14 8S2 16 2 16z\" />\n  <circle cx=\"16\" cy=\"16\" r=\"5\" fill=\"currentColor\" stroke=\"none\" />\n  <line x1=\"5\" y1=\"5\" x2=\"27\" y2=\"27\" />\n</svg>\n");
IconReader.gather('mono-svg', 'eye', "<svg xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" stroke=\"currentColor\"\n\tviewBox=\"0 0 32 32\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M2 16s4-8 14-8 14 8 14 8-4 8-14 8S2 16 2 16z\"/>\n  <circle cx=\"16\" cy=\"16\" r=\"5\" fill=\"currentColor\" stroke=\"none\"/>\n</svg>");
IconReader.gather('mono-svg', 'faq', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"4\" y=\"4\" width=\"24\" height=\"24\" rx=\"3\" />\n  <path d=\"M12 13a4 4 0 0 1 8 0c0 3-4 3-4 5\" />\n  <circle cx=\"16\" cy=\"23\" r=\"1\" />\n</svg>\n");
IconReader.gather('mono-svg', 'favorite', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M16.0 3.0L19.2 12.1L28.8 12.3L21.1 18.2L23.9 27.4L16.0 21.9L8.1 27.4L10.9 18.2L3.2 12.3L12.8 12.1Z\" />\n</svg>\n");
IconReader.gather('mono-svg', 'feedback', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M28 20a3 3 0 0 1-3 3H9l-5 5V7a3 3 0 0 1 3-3h19a3 3 0 0 1 3 3z\" />\n</svg>\n");
IconReader.gather('mono-svg', 'file', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M9 4h9l6 6v16a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z\" />\n  <polyline points=\"18 4 18 10 24 10\" />\n</svg>\n");
IconReader.gather('mono-svg', 'filter', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M5 6h22l-8 10v9l-6 3V16L5 6z\" />\n</svg>\n");
IconReader.gather('mono-svg', 'first', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n    <path d=\"M20 28 L8 16 L20 4 Z\" />\n    <line x1=\"4\" y1=\"4\" x2=\"4\" y2=\"28\" />\n</svg>\n");
IconReader.gather('mono-svg', 'folder-off', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M4 25V8a2 2 0 0 1 2-2h6l3 4h9a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z\" />\n  <line x1=\"5\" y1=\"5\" x2=\"27\" y2=\"27\" />\n</svg>\n");
IconReader.gather('mono-svg', 'folder', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M4 25V8a2 2 0 0 1 2-2h6l3 4h9a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z\" />\n</svg>\n");
IconReader.gather('mono-svg', 'forward', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M5 8l9 8-9 8V8z\" />\n  <path d=\"M17 8l9 8-9 8V8z\" />\n</svg>\n");
IconReader.gather('mono-svg', 'fullscreen', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <polyline points=\"12 5 5 5 5 12\" />\n  <polyline points=\"20 5 27 5 27 12\" />\n  <polyline points=\"27 20 27 27 20 27\" />\n  <polyline points=\"5 20 5 27 12 27\" />\n</svg>\n");
IconReader.gather('mono-svg', 'gallery', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M11 8h15a2 2 0 0 1 2 2v13\" />\n  <rect x=\"4\" y=\"12\" width=\"19\" height=\"15\" rx=\"2\" />\n  <circle cx=\"9.5\" cy=\"17\" r=\"1.7\" />\n  <polyline points=\"5.5 25 11 19.5 15 23.5 18 20.5 22 24.5\" />\n</svg>\n");
IconReader.gather('mono-svg', 'games', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"4\" y=\"10\" width=\"24\" height=\"13\" rx=\"4\" />\n  <line x1=\"9\" y1=\"13.5\" x2=\"9\" y2=\"19.5\" />\n  <line x1=\"6\" y1=\"16.5\" x2=\"12\" y2=\"16.5\" />\n  <circle cx=\"21\" cy=\"14.5\" r=\"1.3\" fill=\"currentColor\" stroke=\"none\" />\n  <circle cx=\"24\" cy=\"18.5\" r=\"1.3\" fill=\"currentColor\" stroke=\"none\" />\n</svg>\n");
IconReader.gather('mono-svg', 'goto', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n    <path d=\"M6 8 H18 V18\" />\n    <polyline points=\"12 18 18 24 24 18\" />\n</svg>\n");
IconReader.gather('mono-svg', 'grid-view', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"5\" y=\"5\" width=\"9\" height=\"9\" rx=\"1.5\" />\n  <rect x=\"18\" y=\"5\" width=\"9\" height=\"9\" rx=\"1.5\" />\n  <rect x=\"5\" y=\"18\" width=\"9\" height=\"9\" rx=\"1.5\" />\n  <rect x=\"18\" y=\"18\" width=\"9\" height=\"9\" rx=\"1.5\" />\n</svg>\n");
IconReader.gather('mono-svg', 'half-checked', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M10 27H22C24 27 25 27 25 26C26 26 26 26 26 25C27 25 27 24 27 22V10C27 8 27 7 26 7C26 6 26 6 25 6C25 5 24 5 22 5H10C8 5 7 5 7 6C6 6 6 6 6 7C5 7 5 8 5 10V22C5 24 5 25 6 25C6 26 6 26 7 26C7 27 8 27 10 27Z\" />\n  <circle cx=\"16\" cy=\"16\" r=\"3.5\" fill=\"currentColor\" stroke=\"none\" />\n</svg>\n");
IconReader.gather('mono-svg', 'heart', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M16 28c-4-4-8-8-8-13a4 4 0 0 1 8-1 4 4 0 0 1 8 1c0 5-4 9-8 13z\" />\n</svg>\n");
IconReader.gather('mono-svg', 'help', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" stroke=\"currentColor\" fill=\"none\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <circle cx=\"16\" cy=\"16\" r=\"13\" />\n  <path d=\"M12 12a4 4 0 0 1 8 0c0 3-4 3-4 5\" />\n  <circle cx=\"16\" cy=\"23\" r=\"1\" />\n</svg>");
IconReader.gather('mono-svg', 'house', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" stroke=\"currentColor\" fill=\"none\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M4 16L16 5l12 11\" />\n  <path d=\"M7 16v9a1 1 0 0 0 1 1h5v-7h5v7h5a1 1 0 0 0 1-1v-9\" />\n</svg>");
IconReader.gather('mono-svg', 'image', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"4\" y=\"6\" width=\"24\" height=\"20\" rx=\"2\" />\n  <circle cx=\"11\" cy=\"13\" r=\"2\" />\n  <polyline points=\"6 24 13 17 18 22 22 18 26 22\" />\n</svg>\n");
IconReader.gather('mono-svg', 'import', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M5 8V7a2 2 0 0 1 2-2h18a2 2 0 0 1 2 2v18a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-1\" />\n  <line x1=\"3\" y1=\"16\" x2=\"19\" y2=\"16\" />\n  <polyline points=\"14 11 19 16 14 21\" />\n</svg>\n");
IconReader.gather('mono-svg', 'info-square', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"4\" y=\"4\" width=\"24\" height=\"24\" rx=\"3\" />\n  <line x1=\"16\" y1=\"15\" x2=\"16\" y2=\"23\" />\n  <circle cx=\"16\" cy=\"10\" r=\"1\" />\n</svg>\n");
IconReader.gather('mono-svg', 'install', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M16 4v13\" />\n  <polyline points=\"10 11 16 17 22 11\" />\n  <path d=\"M5 19v6a2 2 0 0 0 2 2h18a2 2 0 0 0 2-2v-6\" />\n</svg>\n");
IconReader.gather('mono-svg', 'lang', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M28 20a3 3 0 0 1-3 3h-5l-5 5v-5H7a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3h19a3 3 0 0 1 3 3z\" />\n  <line x1=\"11\" y1=\"12\" x2=\"21\" y2=\"12\" />\n  <line x1=\"13\" y1=\"17\" x2=\"19\" y2=\"17\" />\n</svg>");
IconReader.gather('mono-svg', 'last', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n    <path d=\"M12 4 L24 16 L12 28 Z\" />\n    <line x1=\"28\" y1=\"4\" x2=\"28\" y2=\"28\" />\n</svg>\n");
IconReader.gather('mono-svg', 'layers', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"3\" y=\"6\" width=\"26\" height=\"5\" rx=\"1\" />\n  <rect x=\"3\" y=\"13\" width=\"26\" height=\"5\" rx=\"1\" />\n  <rect x=\"3\" y=\"20\" width=\"26\" height=\"5\" rx=\"1\" />\n</svg>\n");
IconReader.gather('mono-svg', 'light-bulb', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <!-- Bulb -->\n  <circle cx=\"16\" cy=\"12\" r=\"8\"/>\n  <!-- Filament -->\n  <polyline points=\"13 13 15 15 17 11 19 13\"/>\n  <!-- Neck -->\n  <line x1=\"12\" y1=\"20\" x2=\"20\" y2=\"20\"/>\n  <line x1=\"12\" y1=\"22\" x2=\"20\" y2=\"22\"/>\n  <!-- Base -->\n  <line x1=\"13\" y1=\"24\" x2=\"19\" y2=\"24\"/>\n  <line x1=\"14\" y1=\"26\" x2=\"18\" y2=\"26\"/>\n</svg>\n");
IconReader.gather('mono-svg', 'like', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M10 27V14h4l5-9a3 3 0 0 1 3 4l-1.5 5h6a2 2 0 0 1 2 2.5l-2 8a3 3 0 0 1-3 2.5H10z\" />\n  <rect x=\"4\" y=\"14\" width=\"6\" height=\"13\" rx=\"1.5\" />\n</svg>\n");
IconReader.gather('mono-svg', 'link-off', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M14 18a5 5 0 0 0 7 0l4-4a5 5 0 0 0-7-7l-2 2\" />\n  <path d=\"M18 14a5 5 0 0 0-7 0l-4 4a5 5 0 0 0 7 7l2-2\" />\n  <line x1=\"5\" y1=\"5\" x2=\"27\" y2=\"27\" />\n</svg>\n");
IconReader.gather('mono-svg', 'link', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M14 18a5 5 0 0 0 7 0l4-4a5 5 0 0 0-7-7l-2 2\" />\n  <path d=\"M18 14a5 5 0 0 0-7 0l-4 4a5 5 0 0 0 7 7l2-2\" />\n</svg>\n");
IconReader.gather('mono-svg', 'list-view', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <line x1=\"12\" y1=\"9\" x2=\"27\" y2=\"9\" />\n  <line x1=\"12\" y1=\"16\" x2=\"27\" y2=\"16\" />\n  <line x1=\"12\" y1=\"23\" x2=\"27\" y2=\"23\" />\n  <circle cx=\"6\" cy=\"9\" r=\"1.3\" fill=\"currentColor\" stroke=\"none\" />\n  <circle cx=\"6\" cy=\"16\" r=\"1.3\" fill=\"currentColor\" stroke=\"none\" />\n  <circle cx=\"6\" cy=\"23\" r=\"1.3\" fill=\"currentColor\" stroke=\"none\" />\n</svg>\n");
IconReader.gather('mono-svg', 'logout', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M21 23l7-7-7-7\" />\n  <path d=\"M28 16H12\" />\n  <path d=\"M16 4H8a3 3 0 0 0-3 3v19a3 3 0 0 0 3 3h8\" />\n</svg>");
IconReader.gather('mono-svg', 'mail-in', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"4\" y=\"13\" width=\"24\" height=\"15\" rx=\"2\" />\n  <polyline points=\"4 15 16 24 28 15\" />\n  <line x1=\"16\" y1=\"2\" x2=\"16\" y2=\"10\" />\n  <polyline points=\"12 6 16 10 20 6\" />\n</svg>\n");
IconReader.gather('mono-svg', 'mail-open', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M4 14l12-8 12 8v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V14z\" />\n  <polyline points=\"4 14 16 22 28 14\" />\n</svg>\n");
IconReader.gather('mono-svg', 'mail-out', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"4\" y=\"13\" width=\"24\" height=\"15\" rx=\"2\" />\n  <polyline points=\"4 15 16 24 28 15\" />\n  <line x1=\"16\" y1=\"10\" x2=\"16\" y2=\"2\" />\n  <polyline points=\"12 6 16 2 20 6\" />\n</svg>\n");
IconReader.gather('mono-svg', 'mail', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"4\" y=\"7\" width=\"24\" height=\"18\" rx=\"2\" />\n  <polyline points=\"4 9 16 18 28 9\" />\n</svg>\n");
IconReader.gather('mono-svg', 'menu', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <line x1=\"4\" y1=\"8\" x2=\"28\" y2=\"8\" />\n  <line x1=\"4\" y1=\"16\" x2=\"28\" y2=\"16\" />\n  <line x1=\"4\" y1=\"24\" x2=\"28\" y2=\"24\" />\n</svg>");
IconReader.gather('mono-svg', 'microphone-off', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"12\" y=\"3\" width=\"8\" height=\"15\" rx=\"4\" />\n  <path d=\"M7 15a9 9 0 0 0 18 0\" />\n  <line x1=\"16\" y1=\"24\" x2=\"16\" y2=\"29\" />\n  <line x1=\"5\" y1=\"5\" x2=\"27\" y2=\"27\" />\n</svg>\n");
IconReader.gather('mono-svg', 'microphone', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"12\" y=\"3\" width=\"8\" height=\"15\" rx=\"4\" />\n  <path d=\"M7 15a9 9 0 0 0 18 0\" />\n  <line x1=\"16\" y1=\"24\" x2=\"16\" y2=\"29\" />\n</svg>\n");
IconReader.gather('mono-svg', 'misty-moon', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M25 12.8A9 9 0 1 1 15.2 3 7 7 0 0 0 25 12.8z\" />\n  <line x1=\"6\" y1=\"25\" x2=\"26\" y2=\"25\" />\n  <line x1=\"10\" y1=\"29\" x2=\"22\" y2=\"29\" />\n</svg>\n");
IconReader.gather('mono-svg', 'moon', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M28 17.1A12 12 0 1 1 14.9 4 9.3 9.3 0 0 0 28 17.1z\" />\n</svg>\n");
IconReader.gather('mono-svg', 'move', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <line x1=\"16\" y1=\"4\" x2=\"16\" y2=\"28\" />\n  <line x1=\"4\" y1=\"16\" x2=\"28\" y2=\"16\" />\n  <polyline points=\"12 8 16 4 20 8\" />\n  <polyline points=\"12 24 16 28 20 24\" />\n  <polyline points=\"8 12 4 16 8 20\" />\n  <polyline points=\"24 12 28 16 24 20\" />\n</svg>\n");
IconReader.gather('mono-svg', 'next', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n    <path d=\"M12 4 L24 16 L12 28 Z\" />\n</svg>");
IconReader.gather('mono-svg', 'no', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"currentColor\">\n  <path d=\"M4 21Q16 5 28 21Q16 13 4 21Z\" />\n</svg>\n");
IconReader.gather('mono-svg', 'open', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M4 25V8a2 2 0 0 1 2-2h6l3 4h9a2 2 0 0 1 2 2v3\" />\n  <path d=\"M4 25l4-10h22l-4 10H4z\" />\n</svg>\n");
IconReader.gather('mono-svg', 'page', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"5\" y=\"2\" width=\"22\" height=\"28\" rx=\"2\" />\n  <line x1=\"10\" y1=\"10\" x2=\"22\" y2=\"10\" />\n  <line x1=\"10\" y1=\"16\" x2=\"22\" y2=\"16\" />\n  <line x1=\"10\" y1=\"22\" x2=\"18\" y2=\"22\" />\n</svg>\n");
IconReader.gather('mono-svg', 'parameters', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" stroke=\"currentColor\" fill=\"none\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <line x1=\"5\" y1=\"9\" x2=\"27\" y2=\"9\" />\n  <circle cx=\"11\" cy=\"9\" r=\"2\" />\n  <line x1=\"5\" y1=\"23\" x2=\"27\" y2=\"23\" />\n  <circle cx=\"21\" cy=\"23\" r=\"2\" />\n</svg>");
IconReader.gather('mono-svg', 'pathway', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <circle cx=\"5\" cy=\"16\" r=\"3\" />\n  <circle cx=\"16\" cy=\"5\" r=\"3\" />\n  <circle cx=\"27\" cy=\"21\" r=\"3\" />\n  <path d=\"M7 15L14 7L25 19\" />\n</svg>");
IconReader.gather('mono-svg', 'pause', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <line x1=\"12\" y1=\"6\" x2=\"12\" y2=\"26\" />\n  <line x1=\"20\" y1=\"6\" x2=\"20\" y2=\"26\" />\n</svg>\n");
IconReader.gather('mono-svg', 'pin', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M12 4h8l-1.5 10.5h-5L12 4z\" />\n  <path d=\"M9.5 17.5h13\" />\n  <path d=\"M16 17.5v11.5\" />\n</svg>\n");
IconReader.gather('mono-svg', 'play', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M11 6l15 10-15 10V6z\" />\n</svg>\n");
IconReader.gather('mono-svg', 'plugin', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M6 6h7a3 3 0 0 1 6 0h7v7a3 3 0 0 0 0 6v7h-7a3 3 0 0 0-6 0H6v-7a3 3 0 0 1 0-6V6z\" />\n</svg>\n");
IconReader.gather('mono-svg', 'position', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M16 29s10-9.5 10-16a10 10 0 0 0-20 0c0 6.5 10 16 10 16z\" />\n  <circle cx=\"16\" cy=\"13\" r=\"3.5\" />\n</svg>\n");
IconReader.gather('mono-svg', 'post-it', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M6 5h20v13l-8 9H6V5z\" />\n  <polyline points=\"26 18 18 18 18 27\" />\n  <line x1=\"10\" y1=\"11\" x2=\"22\" y2=\"11\" />\n  <line x1=\"10\" y1=\"15\" x2=\"19\" y2=\"15\" />\n</svg>\n");
IconReader.gather('mono-svg', 'power', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M10 8a11 11 0 1 0 12 0\" />\n  <line x1=\"16\" y1=\"3\" x2=\"16\" y2=\"16\" />\n</svg>\n");
IconReader.gather('mono-svg', 'print', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M9 12V5h14v7\" />\n  <path d=\"M9 23H7a2 2 0 0 1-2-2v-6a2 2 0 0 1 2-2h18a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2h-2\" />\n  <rect x=\"9\" y=\"19\" width=\"14\" height=\"9\" rx=\"1\" />\n</svg>\n");
IconReader.gather('mono-svg', 'radio-checked', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <circle cx=\"16\" cy=\"16\" r=\"10\" />\n  <circle cx=\"16\" cy=\"16\" r=\"5\" fill=\"currentColor\" stroke=\"none\" />\n</svg>\n");
IconReader.gather('mono-svg', 'radio-unchecked', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <circle cx=\"16\" cy=\"16\" r=\"10\" />\n</svg>\n");
IconReader.gather('mono-svg', 'readings', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M5 25h21M5 20h13M5 15h21M5 9h13\" />\n</svg>");
IconReader.gather('mono-svg', 'redo', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M27.3 20a12 12 0 1 1-2.8-12.5L30.7 13.3\" />\n  <polyline points=\"30.7 5.3 30.7 13.3 22.7 13.3\" />\n</svg>\n");
IconReader.gather('mono-svg', 'refresh', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <polyline points=\"27 6 27 13 20 13\" />\n  <polyline points=\"5 26 5 19 12 19\" />\n  <path d=\"M6.3 13A11 11 0 0 1 25.5 10.5L27 13\" />\n  <path d=\"M25.7 19A11 11 0 0 1 6.5 21.5L5 19\" />\n</svg>\n");
IconReader.gather('mono-svg', 'remove', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <line x1=\"7\" y1=\"16\" x2=\"25\" y2=\"16\" />\n</svg>\n");
IconReader.gather('mono-svg', 'rename', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M22 4.7a2.8 2.8 0 0 1 4 4L14 20.7 8.7 22l1.3-5.3L22 4.7z\" />\n  <line x1=\"5\" y1=\"27\" x2=\"27\" y2=\"27\" />\n</svg>\n");
IconReader.gather('mono-svg', 'researchinfo', "<svg xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" stroke=\"currentColor\"\n     viewBox=\"0 0 32 32\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n    <!-- Left brace { -->\n    <path d=\"M13 5\n             C10 5 10 8 10 10\n             C10 12 8 12 8 12\n             C10 12 10 14 10 16\n             C10 18 8 18 8 18\n             C10 18 10 20 10 22\n             C10 24 10 27 13 27\" />\n    <!-- Right brace } -->\n    <path d=\"M19 5\n             C22 5 22 8 22 10\n             C22 12 24 12 24 12\n             C22 12 22 14 22 16\n             C22 18 24 18 24 18\n             C22 18 22 20 22 22\n             C22 24 22 27 19 27\" />\n    <!-- Dot -->\n    <circle cx=\"16\" cy=\"16\" r=\"1.5\" />\n</svg>\n");
IconReader.gather('mono-svg', 'rewind', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M27 8l-9 8 9 8V8z\" />\n  <path d=\"M15 8l-9 8 9 8V8z\" />\n</svg>\n");
IconReader.gather('mono-svg', 'root', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <polyline points=\"4 16 8 16 14 27 22 5 29 5\" />\n</svg>\n");
IconReader.gather('mono-svg', 'ruler', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"3\" y=\"11\" width=\"26\" height=\"10\" rx=\"2\" />\n  <line x1=\"9\" y1=\"11\" x2=\"9\" y2=\"16\" />\n  <line x1=\"14\" y1=\"11\" x2=\"14\" y2=\"16\" />\n  <line x1=\"19\" y1=\"11\" x2=\"19\" y2=\"16\" />\n  <line x1=\"24\" y1=\"11\" x2=\"24\" y2=\"16\" />\n</svg>\n");
IconReader.gather('mono-svg', 'save', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M5 7a2 2 0 0 1 2-2h14l6 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V7z\" />\n  <path d=\"M10 5v7h10V7\" />\n  <rect x=\"10\" y=\"18\" width=\"12\" height=\"9\" rx=\"1\" />\n</svg>\n");
IconReader.gather('mono-svg', 'screen', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"2\" y=\"4\" width=\"28\" height=\"18\" rx=\"2\" />\n  <line x1=\"16\" y1=\"22\" x2=\"16\" y2=\"28\" />\n  <line x1=\"10\" y1=\"28\" x2=\"22\" y2=\"28\" />\n</svg>\n");
IconReader.gather('mono-svg', 'scrolltop', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" \n\t fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <!-- upward arrow -->\n  <polyline points=\"8 18 16 10 24 18\" />\n  <!-- top baseline -->\n  <line x1=\"8\" y1=\"22\" x2=\"24\" y2=\"22\" />\n</svg>");
IconReader.gather('mono-svg', 'search', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <circle cx=\"14\" cy=\"14\" r=\"8\" />\n  <line x1=\"19.7\" y1=\"19.7\" x2=\"27\" y2=\"27\" />\n</svg>\n");
IconReader.gather('mono-svg', 'settings', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <line x1=\"5.3\" y1=\"28\" x2=\"5.3\" y2=\"18.7\" />\n  <line x1=\"5.3\" y1=\"13.3\" x2=\"5.3\" y2=\"4\" />\n  <line x1=\"16\" y1=\"28\" x2=\"16\" y2=\"16\" />\n  <line x1=\"16\" y1=\"10.7\" x2=\"16\" y2=\"4\" />\n  <line x1=\"26.7\" y1=\"28\" x2=\"26.7\" y2=\"21.3\" />\n  <line x1=\"26.7\" y1=\"16\" x2=\"26.7\" y2=\"4\" />\n  <line x1=\"1.3\" y1=\"18.7\" x2=\"9.3\" y2=\"18.7\" />\n  <line x1=\"12\" y1=\"10.7\" x2=\"20\" y2=\"10.7\" />\n  <line x1=\"22.7\" y1=\"21.3\" x2=\"30.7\" y2=\"21.3\" />\n</svg>\n");
IconReader.gather('mono-svg', 'share', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <circle cx=\"24\" cy=\"7\" r=\"3\" />\n  <circle cx=\"8\" cy=\"16\" r=\"3\" />\n  <circle cx=\"24\" cy=\"25\" r=\"3\" />\n  <line x1=\"10.6\" y1=\"14.5\" x2=\"21.4\" y2=\"8.5\" />\n  <line x1=\"10.6\" y1=\"17.5\" x2=\"21.4\" y2=\"23.5\" />\n</svg>\n");
IconReader.gather('mono-svg', 'smiley-neutral', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <circle cx=\"16\" cy=\"16\" r=\"13\"/>\n  <circle cx=\"11\" cy=\"12\" r=\"1\"/>\n  <circle cx=\"21\" cy=\"12\" r=\"1\"/>\n  <line x1=\"11\" y1=\"21\" x2=\"21\" y2=\"21\"/>\n</svg>\n\n\n");
IconReader.gather('mono-svg', 'smiley-sad', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <circle cx=\"16\" cy=\"16\" r=\"13\"/>\n  <circle cx=\"11\" cy=\"12\" r=\"1\"/>\n  <circle cx=\"21\" cy=\"12\" r=\"1\"/>\n  <path d=\"M11 21 Q16 16 21 21\" fill=\"none\"/>\n</svg>\n\n");
IconReader.gather('mono-svg', 'smiley-smile', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <circle cx=\"16\" cy=\"16\" r=\"13\"/>\n  <circle cx=\"11\" cy=\"12\" r=\"1\"/>\n  <circle cx=\"21\" cy=\"12\" r=\"1\"/>\n  <path d=\"M11 21 Q16 26 21 21\" fill=\"none\"/>\n</svg>\n");
IconReader.gather('mono-svg', 'sort', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <polyline points=\"8 12 12 8 16 12\" />\n  <line x1=\"12\" y1=\"8\" x2=\"12\" y2=\"24\" />\n  <polyline points=\"18 20 22 24 26 20\" />\n  <line x1=\"22\" y1=\"24\" x2=\"22\" y2=\"8\" />\n</svg>\n");
IconReader.gather('mono-svg', 'stop', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"8\" y=\"8\" width=\"16\" height=\"16\" rx=\"2\" />\n</svg>\n");
IconReader.gather('mono-svg', 'sun', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <circle cx=\"16\" cy=\"16\" r=\"6\" />\n  <line x1=\"16\" y1=\"2\" x2=\"16\" y2=\"5\" />\n  <line x1=\"16\" y1=\"27\" x2=\"16\" y2=\"30\" />\n  <line x1=\"2\" y1=\"16\" x2=\"5\" y2=\"16\" />\n  <line x1=\"27\" y1=\"16\" x2=\"30\" y2=\"16\" />\n  <line x1=\"6.1\" y1=\"6.1\" x2=\"8.2\" y2=\"8.2\" />\n  <line x1=\"23.8\" y1=\"23.8\" x2=\"25.9\" y2=\"25.9\" />\n  <line x1=\"6.1\" y1=\"25.9\" x2=\"8.2\" y2=\"23.8\" />\n  <line x1=\"23.8\" y1=\"8.2\" x2=\"25.9\" y2=\"6.1\" />\n</svg>\n");
IconReader.gather('mono-svg', 'sunrise', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M22.7 24a6.7 6.7 0 0 0-13.4 0\" />\n  <line x1=\"1.3\" y1=\"24\" x2=\"4\" y2=\"24\" />\n  <line x1=\"28\" y1=\"24\" x2=\"30.7\" y2=\"24\" />\n  <line x1=\"5.6\" y1=\"13.6\" x2=\"7.5\" y2=\"15.5\" />\n  <line x1=\"24.5\" y1=\"15.5\" x2=\"26.4\" y2=\"13.6\" />\n  <line x1=\"1.3\" y1=\"29.3\" x2=\"30.7\" y2=\"29.3\" />\n  <polyline points=\"10.7 8 16 2.7 21.3 8\" />\n  <line x1=\"16\" y1=\"2.7\" x2=\"16\" y2=\"16\" />\n</svg>\n");
IconReader.gather('mono-svg', 'tag', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M5 5h10l12 12-10 10L5 15V5z\" />\n  <circle cx=\"10\" cy=\"10\" r=\"1.5\" />\n</svg>\n");
IconReader.gather('mono-svg', 'target', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\"\n     fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"\n     stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\">\n    <circle cx=\"16\" cy=\"16\" r=\"13\"/>\n    <circle cx=\"16\" cy=\"16\" r=\"5\" fill=\"currentColor\" stroke=\"none\"/>\n    <line x1=\"16\" y1=\"3\"  x2=\"16\" y2=\"8\"/>\n    <line x1=\"16\" y1=\"24\" x2=\"16\" y2=\"29\"/>\n    <line x1=\"3\"  y1=\"16\" x2=\"8\"  y2=\"16\"/>\n    <line x1=\"24\" y1=\"16\" x2=\"29\" y2=\"16\"/>\n</svg>\n");
IconReader.gather('mono-svg', 'text', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <line x1=\"7\" y1=\"7\" x2=\"25\" y2=\"7\" />\n  <line x1=\"16\" y1=\"7\" x2=\"16\" y2=\"26\" />\n  <line x1=\"11\" y1=\"26\" x2=\"21\" y2=\"26\" />\n</svg>\n");
IconReader.gather('mono-svg', 'theme', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M16 4C8 4 3 10 3 16s6 12 13 12c2 0 3-1 3-2s-1-2-1-3c0-1 1-2 2-2h2c5 0 7-3 7-6 0-6-6-11-13-11z\" />\n  <circle cx=\"10\" cy=\"12\" r=\"1.8\" fill=\"currentColor\" stroke=\"none\" />\n  <circle cx=\"16\" cy=\"9\"  r=\"1.8\" fill=\"currentColor\" stroke=\"none\" />\n  <circle cx=\"22\" cy=\"12\" r=\"1.8\" fill=\"currentColor\" stroke=\"none\" />\n</svg>\n");
IconReader.gather('mono-svg', 'unchecked', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M10 27H22C24 27 25 27 25 26C26 26 26 26 26 25C27 25 27 24 27 22V10C27 8 27 7 26 7C26 6 26 6 25 6C25 5 24 5 22 5H10C8 5 7 5 7 6C6 6 6 6 6 7C5 7 5 8 5 10V22C5 24 5 25 6 25C6 26 6 26 7 26C7 27 8 27 10 27Z\" />\n</svg>\n");
IconReader.gather('mono-svg', 'undo', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <g transform=\"translate(32, 0) scale(-1, 1)\">\n    <path d=\"M27.3 20a12 12 0 1 1-2.8-12.5L30.7 13.3\" />\n    <polyline points=\"30.7 5.3 30.7 13.3 22.7 13.3\" />\n  </g>\n</svg>\n");
IconReader.gather('mono-svg', 'upload', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M16 21V5\" />\n  <polyline points=\"10 11 16 5 22 11\" />\n  <line x1=\"6\" y1=\"27\" x2=\"26\" y2=\"27\" />\n</svg>\n");
IconReader.gather('mono-svg', 'user', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <circle cx=\"16\" cy=\"11\" r=\"5\" />\n  <path d=\"M5 27c0-5 5-8 11-8s11 3 11 8\" />\n</svg>");
IconReader.gather('mono-svg', 'valid', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <polyline points=\"7 17 12 23 25 9\" />\n</svg>");
IconReader.gather('mono-svg', 'video-off', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"4\" y=\"8\" width=\"20\" height=\"16\" rx=\"3\" />\n  <polygon points=\"21 13 28 9 28 23 21 19\" />\n  <line x1=\"5\" y1=\"5\" x2=\"27\" y2=\"27\" />\n</svg>\n");
IconReader.gather('mono-svg', 'video', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <rect x=\"4\" y=\"8\" width=\"20\" height=\"16\" rx=\"3\" />\n  <polygon points=\"21 13 28 9 28 23 21 19\" />\n</svg>");
IconReader.gather('mono-svg', 'volume-high', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M6 12h5l6-5v18l-6-5H6a1 1 0 0 1-1-1v-6a1 1 0 0 1 1-1z\" />\n  <path d=\"M20.5 12.5a5 5 0 0 1 0 7\" />\n  <path d=\"M24 10a9 9 0 0 1 0 12\" />\n  <path d=\"M27 7.5a13 13 0 0 1 0 17\" />\n</svg>\n");
IconReader.gather('mono-svg', 'volume-low', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M6 12h5l6-5v18l-6-5H6a1 1 0 0 1-1-1v-6a1 1 0 0 1 1-1z\" />\n  <path d=\"M20.5 12.5a5 5 0 0 1 0 7\" />\n</svg>\n");
IconReader.gather('mono-svg', 'volume-medium', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M6 12h5l6-5v18l-6-5H6a1 1 0 0 1-1-1v-6a1 1 0 0 1 1-1z\" />\n  <path d=\"M20.5 12.5a5 5 0 0 1 0 7\" />\n  <path d=\"M24 10a9 9 0 0 1 0 12\" />\n</svg>\n");
IconReader.gather('mono-svg', 'volume-mute', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M6 12h5l6-5v18l-6-5H6a1 1 0 0 1-1-1v-6a1 1 0 0 1 1-1z\" />\n  <line x1=\"22\" y1=\"12\" x2=\"29\" y2=\"19\" />\n  <line x1=\"29\" y1=\"12\" x2=\"22\" y2=\"19\" />\n</svg>\n");
IconReader.gather('mono-svg', 'warning', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M16 5L29 27H3L16 5z\" />\n  <line x1=\"16\" y1=\"13\" x2=\"16\" y2=\"19\" />\n  <line x1=\"16\" y1=\"22.5\" x2=\"16\" y2=\"23.5\" />\n</svg>\n");
IconReader.gather('mono-svg', 'wifi-off', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M4 12a18 18 0 0 1 24 0\" />\n  <path d=\"M9 18a11 11 0 0 1 14 0\" />\n  <path d=\"M13.5 23.5a4 4 0 0 1 5 0\" />\n  <circle cx=\"16\" cy=\"27\" r=\"1.3\" fill=\"currentColor\" stroke=\"none\" />\n  <line x1=\"5\" y1=\"5\" x2=\"27\" y2=\"27\" />\n</svg>\n");
IconReader.gather('mono-svg', 'wifi', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <path d=\"M4 12a18 18 0 0 1 24 0\" />\n  <path d=\"M9 18a11 11 0 0 1 14 0\" />\n  <path d=\"M13.5 23.5a4 4 0 0 1 5 0\" />\n  <circle cx=\"16\" cy=\"27\" r=\"1.3\" fill=\"currentColor\" stroke=\"none\" />\n</svg>\n");
IconReader.gather('mono-svg', 'yes', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"currentColor\">\n  <path d=\"M4.5 15.5L12.8 27L28 5.5L24.6 3.6L12.4 21.6L8 13.9Z\" />\n</svg>\n");
IconReader.gather('mono-svg', 'zoom-in', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <circle cx=\"14\" cy=\"14\" r=\"8\" />\n  <line x1=\"19.7\" y1=\"19.7\" x2=\"27\" y2=\"27\" />\n  <line x1=\"14\" y1=\"10.5\" x2=\"14\" y2=\"17.5\" />\n  <line x1=\"10.5\" y1=\"14\" x2=\"17.5\" y2=\"14\" />\n</svg>\n");
IconReader.gather('mono-svg', 'zoom-out', "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n  <circle cx=\"14\" cy=\"14\" r=\"8\" />\n  <line x1=\"19.7\" y1=\"19.7\" x2=\"27\" y2=\"27\" />\n  <line x1=\"10.5\" y1=\"14\" x2=\"17.5\" y2=\"14\" />\n</svg>\n");

// ---------------- wexa.js ---------------
// --- Debug -------------------------------------------------------
console.debug('Imports OK:', {
    OnLoadManager,
    WexaLogger,
    AccessibilityManager,
    MenuManager,
    DialogManager,
    LinkController,
    ToggleSelector,
    ProgressBar,
    BaseManager,
    RequestManager,
    IconManager,
    AccessibilityNav,
    KeyboardController
});
// ----- Exports (framework public API) -----
// ---------------------------------------------------------------------------
// Global namespace for Whakerexa.
//
// This namespace exposes:
// - Singletons: framework-level managers that must exist exactly once.
// - Classes: reusable components that applications can instantiate freely.
//
// This unified API ensures consistency between ES6 module usage and the
// bundled (non-module) version. Applications can safely rely on Wexa.*
// regardless of whether modules are loaded or the bundle is used.
// ---------------------------------------------------------------------------
window.Wexa = Object.assign(window.Wexa || {}, {
    // ---------------------------------------------------------------
    // Singletons (global services)
    // ---------------------------------------------------------------
    // Logger is a class with only static methods → no cost / no instance.
    logger: WexaLogger,
    // Note: OnLoadManager is not instantiated because it is a scheduler /
    // dispatcher whose methods are static or utility-like.
    onload: OnLoadManager,
    // What answers a name with a drawing. A page brings its own sets to it,
    // and the components of the framework ask it for what they draw.
    icons,
    // What the framework carries as themes: a page names one of them by its
    // name alone, and the loader knows where it stands.
    THEMES_BASE,
    REFERENCE_THEMES,
    accessibility: new AccessibilityManager(),
    dialog: new DialogManager(),
    links: new LinkController(),
    // ---------------------------------------------------------------
    // Public classes (instantiable components)
    // ---------------------------------------------------------------
    WexaLogger,
    OnLoadManager,
    AccessibilityManager,
    DialogManager,
    LinkController,
    MenuManager,
    ProgressBar,
    ToggleSelector,
    BaseManager,
    RequestManager,
    IconManager,
    AccessibilityNav,
    KeyboardController
});
// Make every [data-href] element without a real href focusable via Tab.
OnLoadManager.addLoadFunction(() => LinkController.initFocusable());
// ---------------- extras/slides/slides.init.js ---------------
'use strict';
const _MODULE_URL = null;
class SlidesInitializer {
    // -----------------------------------------------------------------------
    // PRIVATE FIELDS
    // -----------------------------------------------------------------------
    #base;
    #themesAttr;
    #defaultName;
    #themesBase;
    #mode;
    #logoSrc;
    #progressOn;
    // -----------------------------------------------------------------------
    // CONSTRUCTOR
    // -----------------------------------------------------------------------
    constructor() {
        this.#base = (_MODULE_URL !== null) ? new URL('.', _MODULE_URL).href : null;
        const scriptEl = this.#findScriptElement();
        this.#themesAttr  = (scriptEl?.dataset.themes     || '').trim();
        this.#defaultName = (scriptEl?.dataset.default    || '').trim();
        // data-themes-path is what this attribute was called: a presentation
        // written before keeps working, and says the same thing.
        this.#themesBase  = (scriptEl?.dataset.themesBase
                             || scriptEl?.dataset.themesPath || '').trim();
        this.#mode        = (scriptEl?.dataset.mode       || 'presentation').trim();
        this.#logoSrc     = (scriptEl?.dataset.logo       || '').trim();
        this.#progressOn  = (scriptEl?.dataset.progress   !== 'false');
    }
    // -----------------------------------------------------------------------
    // PUBLIC METHODS
    // -----------------------------------------------------------------------
    async init() {
        if (this.#base === null) {
            this.#initFromLoadedBundle();
        } else if (window.location.protocol === 'file:') {
            await this.#initFromBundle();
        } else {
            await this.#initFromModules();
        }
    }
    // -----------------------------------------------------------------------
    // PRIVATE METHODS — initialization paths
    // -----------------------------------------------------------------------
    #findScriptElement() {
        if (_MODULE_URL === null) {
            return document.currentScript;
        }
        const scripts = Array.from(document.querySelectorAll('script[type="module"][src]'));
        for (const script of scripts) {
            try {
                if (new URL(script.src).href === _MODULE_URL) {
                    return script;
                }
            } catch {
                // Malformed src attribute — skip this element.
            }
        }
        return null;
    }
    #initFromBundle() {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = new URL('../../wexa.bundle.js', this.#base).href;
            script.onerror = () => {
                reject(new Error('SlidesInitializer: failed to load wexa.bundle.js.'));
            };
            script.onload = async () => {
                window.Wexa = window.Wexa || {};
                await this.#injectBoilerplate();
                window.Wexa.accessibility = new window.Wexa.AccessibilityManager();
                this.#registerThemes(window.Wexa.ThemeManager || null,
                                     window.Wexa.REFERENCE_THEMES);
                const app = this.#buildConfig(window.Wexa.Slides);
                app.init();
                this.#ready(app);
                resolve();
            };
            document.head.appendChild(script);
        });
    }
    async #initFromLoadedBundle() {
        if (document.querySelectorAll('section.slide').length === 0) {
            return;
        }
        window.Wexa = window.Wexa || {};
        await this.#injectBoilerplate();
        window.Wexa.accessibility = new window.Wexa.AccessibilityManager();
        this.#registerThemes(window.Wexa.ThemeManager || null,
                                     window.Wexa.REFERENCE_THEMES);
        await this.#paginate(window.Wexa.SlidesPagination || null);
        const app = this.#buildConfig(window.Wexa.Slides);
        app.init();
        this.#ready(app);
    }
    async #initFromModules() {
        const [slidesModule] = await Promise.all([
            import(new URL('slides.js', this.#base).href),
            import(new URL('../../wexa.js', this.#base).href),
        ]);
        window.Wexa = window.Wexa || {};
        await this.#injectBoilerplate();
        if (this.#themesAttr !== '') {
            const [{ ThemeManager }, { REFERENCE_THEMES }] = await Promise.all([
                import(new URL('../../customize/theme_manager.js', this.#base).href),
                import(new URL('../../customize/theme_reference.js', this.#base).href)
            ]);
            this.#registerThemes(ThemeManager, REFERENCE_THEMES);
        }
        const { SlidesPagination } = await import(new URL('slides_pagination.js', this.#base).href);
        await this.#paginate(SlidesPagination);
        const app = this.#buildConfig(slidesModule.default);
        app.init();
        this.#ready(app);
    }
    // -----------------------------------------------------------------------
    // PRIVATE METHODS — DOM building
    // -----------------------------------------------------------------------
    #ensureCss(filename) {
        const alreadyLoaded = Array.from(document.querySelectorAll('link[rel="stylesheet"]'))
            .some(link => link.href.endsWith(filename));
        if (alreadyLoaded === true) {
            return;
        }
        if (this.#base === null) {
            console.warn(`SlidesInitializer: ${filename} not found in <head>. Add it manually in bundle mode.`);
            return;
        }
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = new URL(`../../../css/${filename}`, this.#base).href;
        document.head.appendChild(link);
    }
    async #injectBoilerplate() {
        this.#ensureCss('menu.css');
        this.#ensureCss('togglegroup.css');
        if (this.#progressOn === true && document.getElementById('progress-container') === null) {
            const container = document.createElement('div');
            container.id = 'progress-container';
            const bar = document.createElement('div');
            bar.id = 'progress-bar';
            container.appendChild(bar);
            document.body.appendChild(container);
        }
        if (document.getElementById('overview-container') === null) {
            const overview = document.createElement('div');
            overview.id = 'overview-container';
            document.body.appendChild(overview);
        }
        if (document.getElementById('accessibility-controls') === null) {
            document.body.appendChild(await this.#buildAccessibilityNav());
        }
        if (document.getElementById('nav-content') === null) {
            document.body.appendChild(await this.#buildNavContent());
        }
        if (this.#logoSrc !== '' && document.getElementById('logo-container') === null) {
            const logo = document.createElement('div');
            logo.id = 'logo-container';
            logo.className = 'top right';
            const img = document.createElement('img');
            img.src = this.#logoSrc;
            img.alt = '';
            img.className = 'img-logo';
            logo.appendChild(img);
            document.body.appendChild(logo);
        }
    }
    async #buildAccessibilityNav() {
        // The bundle holds the class in the namespace, and there is nothing to
        // import: an import there would be given a null base and would raise.
        const NavClass = (window.Wexa !== undefined && window.Wexa.AccessibilityNav)
            ? window.Wexa.AccessibilityNav
            : (await import(new URL('../../accessibility_nav.js', this.#base).href))
                .AccessibilityNav;
        const bar = new NavClass({
            theme: this.#themesAttr !== '',
            contrast: true,
            color: true
        });
        return await bar.build({
            id: 'accessibility-controls',
            className: 'nav-wexa controls-hidden',
            label: 'Accessibility controls'
        });
    }
    async #buildNavContent() {
        const nav = document.createElement('nav');
        nav.id = 'nav-content';
        nav.className = 'nav-wexa bottom controls-hidden';
        nav.setAttribute('aria-label', 'Slide navigation');
        const prevIcon  = await window.Wexa.icons.get('back');
        const nextIcon  = await window.Wexa.icons.get('next');
        const firstIcon = await window.Wexa.icons.get('first');
        const lastIcon  = await window.Wexa.icons.get('last');
        const gotoIcon  = await window.Wexa.icons.get('goto');
        nav.innerHTML =
            '<section>'
            +     '<button class="menuitem" id="btn-prev" aria-label="Previous slide" title="Previous slide">' + prevIcon + '</button>'
            +     '<button class="menuitem" id="btn-next" aria-label="Next slide" title="Next slide">' + nextIcon + '</button>'
            +     '<button class="menuitem" id="btn-back" aria-label="First slide" title="First slide">' + firstIcon + '</button>'
            +     '<button class="menuitem" id="btn-last" aria-label="Last slide" title="Last slide">' + lastIcon + '</button>'
            +     '<button class="menuitem" id="btn-goto" aria-label="Go to slide" title="Go to slide">' + gotoIcon + '</button>'
            + '</section>'
            + '<section>'
            +     '<button class="menuitem" id="btn-fullscreen">Fullscreen</button>'
            + '</section>'
            + '<section id="slides-controls-view" class="toggle-group" role="radiogroup" aria-label="View mode">'
            +     '<label class="menuitem" for="btn-overview">'
            +         '<input type="radio" name="view-mode" id="btn-overview" value="overview">'
            +         ' Overview'
            +     '</label>'
            +     '<label class="menuitem" for="btn-handout">'
            +         '<input type="radio" name="view-mode" id="btn-handout" value="handout">'
            +         ' Handout'
            +     '</label>'
            +     '<label class="menuitem" for="btn-note">'
            +         '<input type="radio" name="view-mode" id="btn-note" value="note">'
            +         ' Note'
            +     '</label>'
            +     '<label class="menuitem" for="btn-presentation">'
            +         '<input type="radio" name="view-mode" id="btn-presentation" value="presentation" checked>'
            +         ' Slides'
            +     '</label>'
            + '</section>';
        return nav;
    }
    // -----------------------------------------------------------------------
    // PRIVATE METHODS — application bootstrap
    // -----------------------------------------------------------------------
    #themesFolder() {
        if (this.#themesBase !== '') {
            return this.#themesBase;
        }
        if (this.#base === null) {
            return '';
        }
        return new URL('../../../css/themes/', this.#base).href;
    }
    #placeOf(path) {
        if (/^(\.{1,2}\/|\/)/.test(path) === true) {
            return path;
        }
        if (/^[a-z][a-z0-9+.-]*:\/\//i.test(path) === true) {
            return path;
        }
        return this.#themesFolder() + path;
    }
    #registerThemes(ThemeManager, reference) {
        if (this.#themesAttr === '' || ThemeManager === null) {
            return;
        }
        const carried = Array.isArray(reference) === true ? reference : [];
        const manager = new ThemeManager();
        let chosen = false;
        for (const declared of this.#themesAttr.split(/[\n,]/)) {
            const said = declared.trim();
            if (said === '') {
                continue;
            }
            const first = said.indexOf(':');
            if (first === -1) {
                const found = carried.find(theme => theme[0] === said);
                if (found === undefined) {
                    console.error('SlidesInitializer: the framework carries no theme'
                        + ' named "' + said + '".');
                    continue;
                }
                manager.register(found[0], this.#themesFolder() + found[1]);
                chosen = true;
                continue;
            }
            manager.register(said.slice(0, first).trim(),
                             this.#placeOf(said.slice(first + 1).trim()));
        }
        // Nothing chosen among the framework's: it takes them all.
        if (chosen === false) {
            carried.forEach(theme => manager.register(theme[0],
                                                      this.#themesFolder() + theme[1]));
        }
        const logger = (window.Wexa || {}).logger;
        if (manager.themeNames.length === 1 && logger !== undefined) {
            logger.warn('SlidesInitializer: one theme is registered, "'
                + manager.themeNames[0] + '". What switches them has nowhere to go.');
        }
        if (this.#defaultName !== '') {
            manager.setDefault(this.#defaultName);
        }
        window.themes = manager;
    }
    async #paginate(SlidesPagination) {
        if (SlidesPagination === null || SlidesPagination === undefined) {
            console.warn('SlidesInitializer: SlidesPagination not found. Slides are shown as they are written.');
            return;
        }
        const pending = (window.Wexa && Array.isArray(window.Wexa.contentReady))
            ? window.Wexa.contentReady
            : [];
        await Promise.allSettled(pending);
        // A slide only has the height of a slide once the body wears the class
        // of the view. Measured before that, it is as tall as what it holds,
        // and nothing ever overflows. The class is the one app.init() sets.
        document.body.classList.add(this.#mode + '-view');
        await new SlidesPagination().run();
    }
    #buildConfig(SlidesClass) {
        return new SlidesClass({
            slides:               document.querySelectorAll('section.slide'),
            controls:             document.getElementById('nav-content'),
            controlsView:         document.getElementById('slides-controls-view'),
            overviewContainer:    document.getElementById('overview-container'),
            progressBarContainer: this.#progressOn === true ? document.getElementById('progress-container') : null,
            progressBar:          this.#progressOn === true ? document.getElementById('progress-bar')        : null,
            logo:                 document.getElementById('logo-container'),
            accessibility:        document.getElementById('accessibility-controls'),
            mode:                 this.#mode,
        });
    }
    #ready(app) {
        window.app = app;
        window.dispatchEvent(new CustomEvent('wexa:slides:ready', { detail: { app } }));
    }
}
// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------
const initializer = new SlidesInitializer();
initializer.init();
// ---- AUTO-GENERATED EXPORTS (Whakerexa bundle) ----
if (typeof window.Wexa !== 'object') { window.Wexa = {}; }
window.Wexa.SlidesInitializer = SlidesInitializer;
// ---- END AUTO-GENERATED EXPORTS ----

