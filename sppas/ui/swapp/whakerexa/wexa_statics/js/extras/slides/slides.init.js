/**
 :filename: statics.js.extras.slides.slides.init.js
 :author: Brigitte Bigi
 :contact: contact@sppas.org
 :summary: One-tag initializer for Whakerexa Slides.

 -------------------------------------------------------------------------

 This file is part of Whakerexa: https://github.com/brigitte-bigi/Whakerexa

 Copyright (C) 2023-2026 Brigitte Bigi, CNRS
 Laboratoire Parole et Langage, Aix-en-Provence, France

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with this program.  If not, see <https://www.gnu.org/licenses/>.

 This banner notice must not be removed.

 -------------------------------------------------------------------------

 -------------------------------------------------------------------------
 Theme use cases
 -------------------------------------------------------------------------

 Case 1 — No theme (plain wexa.css only):
   <script type="module" src="slides.init.js"></script>

 Case 2 — Themes of the framework, switch on the fly:
   <script type="module" src="slides.init.js"
           data-themes="wexa_theme, aurora"
           data-default="wexa_theme">
   </script>

 Case 3 — No ThemeManager, custom overrides in a <style> block:
   <style>
       @layer theme { :root { --a-color: rgb(200, 0, 0); } }
   </style>
   <script type="module" src="slides.init.js"></script>

 Case 4 — Own theme only, no switching (load as a static CSS link):
   <link rel="stylesheet" href="my_theme.css">
   <script type="module" src="slides.init.js"></script>

 Case 5 — Own theme and themes of the framework, switch on the fly:
   <script type="module" src="slides.init.js"
           data-themes="mine:./my_theme.css, wexa_theme, highcontrast"
           data-default="mine">
   </script>

 -------------------------------------------------------------------------
 Data attributes (all optional)
 -------------------------------------------------------------------------

   data-themes      The themes the presentation takes, in the order it cycles
                    through them: a name alone for one of the framework --
                    wexa_theme, aurora, highcontrast --, and "name:path" for
                    one the page brings. Separated by commas or one per line,
                    as on wexa.loader.js. Omit entirely to skip ThemeManager.
   data-default     Name of the theme active on load (must be in data-themes).
   data-themes-base Where the themes of the framework stand, when they are not
                    under css/themes/ of wexa_statics. Read from this file
                    otherwise, and required in bundle mode, where nothing says
                    where this file is. data-themes-path is the name it had,
                    and is still read: "wexa:wexa_theme.css" says what
                    "wexa_theme" says, the file being read from that folder.
   data-mode        Initial view mode: "presentation" (default), "handout", "note".
   data-logo        Path to a logo image (relative to the HTML page).
                    Omit to disable the logo overlay.
   data-progress    "true" (default) or "false". Set to "false" to disable
                    the progress bar entirely.

 -------------------------------------------------------------------------
 Auto-injected elements (skipped when already present in the HTML)
 -------------------------------------------------------------------------

   #accessibility-controls   nav: theme-switcher + color-scheme button
   #progress-container       progress bar wrapper  (skipped if data-progress="false")
   #progress-bar             progress bar fill     (skipped if data-progress="false")
   #overview-container       overview panel
   #nav-content              Prev/Next/First/Last/GoTo/Fullscreen + view-mode group
   #slides-controls-view     radio group inside #nav-content
   #logo-container           injected only when data-logo is set

 */

'use strict';

const _MODULE_URL = import.meta.url;

/**
 * One-tag initializer for Whakerexa Slides.
 *
 * Reads configuration from data-* attributes on its own <script type="module">
 * element, injects the required boilerplate elements into the DOM, loads the
 * Slides and Wexa modules, then starts the application.
 *
 * Two execution paths are handled transparently:
 *   - file:// — loads wexa.bundle.js as a classic script, because browsers
 *     block ES module imports on the file: protocol.
 *   - http(s):// — imports slides.js, wexa.js, and optionally theme_manager.js
 *     as ES modules. Top-level await ensures AccessibilityManager is
 *     instantiated before window.onload, so OnLoadManager runs correctly.
 *
 * After initialization, window.app holds the Slides instance and the
 * 'wexa:slides:ready' event is dispatched on window.
 */
export default class SlidesInitializer {

    // -----------------------------------------------------------------------
    // PRIVATE FIELDS
    // -----------------------------------------------------------------------

    /** @type {string} Base URL of this module, used to resolve sibling imports. */
    #base;

    /** @type {string} Raw value of data-themes ("name:file,name:file,…"). */
    #themesAttr;

    /** @type {string} Name of the default theme (data-default). */
    #defaultName;

    /** @type {string} Where the themes of the framework stand (data-themes-base). */
    #themesBase;

    /** @type {string} Initial view mode (data-mode). */
    #mode;

    /** @type {string} Logo image path relative to the HTML page (data-logo). */
    #logoSrc;

    /** @type {boolean} Whether the progress bar is enabled (data-progress). */
    #progressOn;

    // -----------------------------------------------------------------------
    // CONSTRUCTOR
    // -----------------------------------------------------------------------

    /**
     * Create a new SlidesInitializer.
     *
     * Finds the <script type="module"> element that loaded this file and
     * reads its data-* attributes. Defaults are applied for absent attributes.
     *
     * @constructor
     */
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

    /**
     * Load modules, inject boilerplate, and start the application.
     *
     * Dispatches 'wexa:slides:ready' on window when done and assigns the
     * Slides instance to window.app.
     *
     * @async
     * @returns {Promise<void>}
     */
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

    /**
     * Find the script element that loaded this file.
     *
     * In bundle (classic script) context (_MODULE_URL is null), returns
     * document.currentScript immediately. In ES module context, iterates
     * module scripts and compares each resolved src href to the module URL.
     *
     * @private
     * @returns {HTMLScriptElement|null} The script element, or null if not found.
     */
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

    /**
     * Initialize via wexa.bundle.js (file:// protocol).
     *
     * Injects a classic <script> tag pointing to the bundle and bootstraps
     * the application inside its onload callback. Returns a Promise that
     * resolves when initialization is complete, keeping the module's top-level
     * await alive until then — so window.onload fires after the bundle is ready.
     *
     * @private
     * @returns {Promise<void>}
     */
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

    /**
     * Initialize using classes already available in window.Wexa (bundle context).
     *
     * Called when this file is included in wexa.bundle.js and executed as a
     * classic script. All classes are already present; no module loading needed.
     *
     * @async
     * @private
     * @returns {Promise<void>}
     */
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

    /**
     * Initialize via ES module imports (http(s):// protocol).
     *
     * Loads slides.js and wexa.js in parallel, then optionally loads
     * theme_manager.js if data-themes is set. AccessibilityManager is
     * constructed before window.onload fires, thanks to top-level await
     * in the module's entry point.
     *
     * @private
     * @async
     * @returns {Promise<void>}
     */
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

    /**
     * Inject a required stylesheet into <head> if it is absent.
     *
     * Called before any nav elements are built so that menu and toggle-group
     * styles are always available. In bundle mode (this.#base === null) a
     * warning is emitted instead, because relative URL resolution is not
     * possible.
     *
     * @private
     * @param {string} filename - CSS file name, relative to wexa_statics/css/.
     * @returns {void}
     */
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

    /**
     * Inject standard boilerplate elements that are absent from the page.
     *
     * Each element is created only if no element with its id already exists,
     * so that users can override any element by writing their own in the HTML.
     *
     * @async
     * @private
     * @returns {Promise<void>}
     */
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

    /**
     * Build the accessibility controls nav element.
     *
     * The bar itself belongs to the framework: what it commands is the
     * accessibility of a document, whatever the shape that document takes.
     * The theme button is asked for only when data-themes is set, ThemeManager
     * not being loaded otherwise.
     *
     * @async
     * @private
     * @returns {Promise<HTMLElement>}
     */
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

    /**
     * Build the slide navigation controls nav element.
     *
     * @async
     * @private
     * @returns {Promise<HTMLElement>}
     */
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

    /**
     * Say where the themes of the framework stand.
     *
     * data-themes-base when the page says it, and otherwise the folder they
     * stand in, read from where this file stands. In bundle mode nothing says
     * where this file is, and the page has to.
     *
     * @private
     * @returns {string}
     */
    #themesFolder() {
        if (this.#themesBase !== '') {
            return this.#themesBase;
        }
        if (this.#base === null) {
            return '';
        }
        return new URL('../../../css/themes/', this.#base).href;
    }

    /**
     * Give the place a page wrote, as the page meant it.
     *
     * The same rule as the loader: what is written './', '../', '/' or with a
     * scheme is taken as it is, and a bare path is read from where the themes
     * of the framework stand.
     *
     * @private
     * @param {string} path - What the page wrote.
     * @returns {string}
     */
    #placeOf(path) {
        if (/^(\.{1,2}\/|\/)/.test(path) === true) {
            return path;
        }
        if (/^[a-z][a-z0-9+.-]*:\/\//i.test(path) === true) {
            return path;
        }
        return this.#themesFolder() + path;
    }

    /**
     * Register the themes the page takes, and hold them for it.
     *
     * data-themes is written as it is on the loader: a name alone chooses among
     * the themes of the framework, and 'name:path' is one the page brings. A
     * presentation that names none of the framework's takes them all, after
     * what it brings. Saying nothing at all registers nothing, a presentation
     * being free of a theme.
     *
     * @private
     * @param {Function|null} ThemeManager - The class, or null to skip.
     * @param {Array} reference - What the framework carries: (name, file).
     * @returns {void}
     */
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

    /**
     * Lay every written slide on as many slides as it takes.
     *
     * It happens here, and not later: the slides are counted and the overview
     * is built from what section.slide gives, so counting before laying out
     * would give wrong numbers and an incomplete overview.
     *
     * A page that builds content of its own — a bibliography, a table of
     * contents — pushes its promise into window.Wexa.contentReady: measuring a
     * table that does not exist yet measures nothing. A content that fails to
     * build does not stop the layout: what exists is laid out all the same.
     *
     * @private
     * @async
     * @param {Function|null} SlidesPagination - SlidesPagination constructor, or null to skip.
     * @returns {Promise<void>}
     */
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

    /**
     * Instantiate the Slides class with all DOM elements and configuration.
     *
     * @private
     * @param {Function} SlidesClass - The Slides constructor.
     * @returns {Object} The Slides instance, ready to call init() on.
     */
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

    /**
     * Finalize initialization: assign the app to window and fire the ready event.
     *
     * @private
     * @param {Object} app - The initialized Slides instance.
     * @returns {void}
     */
    #ready(app) {
        window.app = app;
        window.dispatchEvent(new CustomEvent('wexa:slides:ready', { detail: { app } }));
    }

}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

const initializer = new SlidesInitializer();
await initializer.init();
