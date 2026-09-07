/**
 :filename: wexa_statics.js.wexa.js
 :author: Brigitte Bigi
 :contact: contact@sppas.org

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
 */
/**
 * Whakerexa main module entry point.
 *
 * This module imports all public classes of the framework and exposes them
 * under the global `window.Wexa` namespace. It centralizes the API surface
 * while keeping modules clean and free of global side effects. This design
 * ensures consistency between ES6-module usage (HTTP) and bundle usage
 * (file://) without duplicating logic.
 *
 * Imported classes:
 * - Core managers (OnLoadManager, WexaLogger, AccessibilityManager, MenuManager,
 *   DialogManager, LinkController)
 * - UI components (ProgressBar, ToggleSelector)
 * - Extras (Book, SortaTable, ThemeManager) are imported directly by pages that need them.
 *
 * The global namespace is defined at the end of the file.
 */

import { OnLoadManager } from './dom-loader.js';
import { WexaLogger } from './logger.js';
import { AccessibilityManager } from './accessibility.js';
import { AccessibilityNav } from './accessibility_nav.js';
import { MenuManager } from './menu.js';
import { DialogManager } from './dialog.js';
import { LinkController } from './links.js';

import { ProgressBar } from './progressbar.js';
import { ToggleSelector } from './toggleselect.js';
import { IconSet } from './customize/icon_set.js';
import { IconSets } from './customize/icon_sets.js';
import { IconManager } from './customize/icon_manager.js';
import { icons } from './customize/icons.js';
import { THEMES_BASE, REFERENCE_THEMES } from './customize/theme_reference.js';
import { KeyboardController } from './keyboard.js';

import { BaseManager } from './transport/base_manager.js';
import { RequestManager } from './transport/request.js';



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
export {
    THEMES_BASE,
    REFERENCE_THEMES,
    OnLoadManager,
    WexaLogger,
    AccessibilityManager,
    MenuManager,
    DialogManager,
    LinkController,
    ProgressBar,
    ToggleSelector,
    BaseManager,
    RequestManager,
    IconSet,
    IconSets,
    IconManager,
    AccessibilityNav,
    KeyboardController
};

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
