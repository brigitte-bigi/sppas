# Whakerexa — A minimalist and lightweight web kit for accessible contents


## Overview

`Whakerexa` is a lightweight front-end toolkit that blends clarity, accessibility, and flexibility, and long-term maintainability.
It provides a modern CSS foundation and a fully modular ES6 JavaScript components to build interfaces that are both elegant and inclusive — with minimal code and maximum readability, without dependencies.

Designed around accessibility from the start, Whakerexa makes it easy to craft clean, human-friendly HTML that just works — without drowning your pages in class names or dependencies.
Every visual aspect — colors, typography, spacing, animations — is defined through CSS variables, giving you full creative control with a few redefinitions.

Version 2.0 introduces a unified public API through `wexa.js` and a stable global namespace through `wexa.bundle.js`, ensuring support for both modern ES6 module-based applications and offline/static environments.

It pairs naturally with `WhakerPy`, the lightweight Python library for generating dynamic HTML, offering a seamless workflow from code to design.



### Features

- ✨ Lightweight, semantic, dependency-free, and modular
- 🌓 Built-in light / dark themes
- 🔆 High-contrast accessibility mode
- 🎨 Fully customizable through CSS variables — using `@layer` so your rules always win without `!important`
- 🧩 Composable and extensible — adapt to your needs
- ⚙️ Object-oriented ES6 components
- ⚙️ Unified API (`import … from "wexa.js"` or `Wexa.*`)
- ⚙️ Single-file bundle for no-module environments
- ⚙️ Zero dependencies, 100 % open source


## Install Whakerexa

Whakerexa is distributed as a ZIP archive.  
Simply unpack it.


## Quick Start

For usage examples of the CSS and JS frameworks, visit the **online documentation**:

👉 <https://brigitte-bigi.github.io/Whakerexa/>

The HTML files available in the `docs` folder are also provided for offline reference.

Browse to Whakerexa folder and either double-clic index.html or launch:
``` 
> python -m http.server 8000 
```
Then open a new tab into Firefox with the url: http://localhost:8000/


## Projects using Whakerexa

Whakerexa was initially developed within SPPAS <https://sppas.org>. 
It was extracted from its original software in 2024 by the author to lead its own life as standalone tool.


### Websites

It is used by the website of the "AutoCuedSpeech" project at <https://auto-cuedspeech.org> and the website of SPPAS <https://sppas.org>.


## Author/Copyright

Copyright (C) 2023-2026 - Brigitte Bigi, CNRS - <contact@sppas.org>
Laboratoire Parole et Langage, Aix-en-Provence, France.

See the AUTHORS file for the full list of contributors.


## License

Whakerexa is under the terms of the GNU Affero General Public License, version 3.


## Support

Whakerexa was initially developed within <https://auto-cuedspeech.org> project, generously funded by FIRAH (Fondation Internationale de Recherche Appliquée sur le Handicap), <https://www.firah.org/>.
It is also developed with the support of Laboratoire Parole et Langage <https://lpl-aix.fr>.



# Changes

## Version 0.1

- Initial version, extracted from SPPAS 4.17.
- Added or updated, and tested JavaScripts 
- Updated CSS frameworks to be more generic
- Added HTML documentation of the CSS frameworks
- Added a CSS/JS framework for playing a video in a popup dialog


## Version 0.2

- Added code.css, a set of colors for highlighting source code.
- Added menu.css, a solution for an accessible responsive sticky menubar
- Added layout.css, a set of classes to easily organize HTML content
- Added accordion.js which must be added when using "rise-panel"


## Version 0.3

- Changed some colors of code.css
- Added variable 'border-radius' in wexa.css
- Modified details/summary to act and look like buttons
- The "rise-panel/accordion" is deprecated (HTML-3), use HTML-5 details/summary instead
- Added modal dialogs to show an alert message: info, success, warning, error, tips, question


## Version 0.4

This is mainly a bug-correction version: adjusted some width, removed transparency of 
background dialogs, corrected a bug in accessibility.


## Version 0.5 

- Added accessibility icons
- Added upload of files in request.js
- Minor CSS changes
- Migrated license, from GPL to AGPL.


## Version 0.6

- Added `sortatable`: a CSS/JS utility designed for sorting table rows in ascending or descending order
- Added `toggleselect`: CSS/JS utility for toggling checkbox states.
- Added custom buttons: introduced CSS classes `text-reveal-button`, `action-button`, `apply-button` and `switch`.
- Updated request.js: better support of upload, better error management in post.


## Version 0.7

- Re-organized documentation
- Updated the switch button
- Debug of action-button
- Minor changes in wexa.css


## Version 0.8

- This is mainly some debug.


## Version 1.0

Version 1.0 establishes Whakerexa as a modular, object-oriented web kit centered on a unified entry point.

- Core entry point: `wexa.js`, which instantiates:
    1. OnLoadManager — Delayed, ordered component initialization.
    2. WexaLogger — Unified logging.
    3. AccessibilityManager — Color mode (light/dark) and contrast mode.
    4. MenuManager — Navigation menus and submenus.
    5. DialogManager — Opening/closing dialogs and popup videos.

- Menus are fully re-implemented (CSS + JS). See `docs/menu.html`.
- Dialogs are managed by `DialogManager` (legacy functions replaced).
- Backward compatibility with pre-1.0 procedural APIs is limited and not fully ensured.
- Not all minor/specialized classes have been ported (e.g., `Book`, `ToggleSelector`, `SortaTable`).

This version also includes a set of monochrome SVG icons.


## Version 2.0 

Version 2.0 is a complete modernization.
Previous procedural APIs are not preserved.

- Unified ES6 entry point (`wexa.js`) exporting all components.
- `wexa.bundle.js` exposes the global namespace `window.Wexa` for `file://` usage.
- The `progress()` function is removed. Use the `ProgressBar` class instead (see `docs/progressbar.html`).
- Use `Wexa.onload` instead of `OnLoadManager`, `Wexa.dialog` instead of `DialogManager`, etc.
- `WexaLogger` is extended: numeric levels from 0 (most verbose) to 50 (critical only). Messages are shown when their level is >= the current `logLevel`.
- Improved `request.js`: JSON detection through `Content-Type` with silent fallback for non-JSON responses.
- Updated documentation and offline demos. Fixed license documentation to GFDL 1.3, except for slides. See: <https://www.gnu.org/licenses/fdl-1.3.en.html> for details.
- Added an "extra" JS package for slides. Currently proposed as a PoC.


## Version 2.1

Increased accessibility and corrected bugs.


## Version 3.0

Version 3.0 introduces architectural changes in CSS and JavaScript. Previous CSS selectors and JS APIs are not preserved.

- CSS now uses `@layer reset, base, theme, accessibility`. Rules written outside any layer override framework defaults automatically — no `!important` needed.
- Light/dark/contrast modes are controlled by `.dark` and `.contrast` classes on `:root` (the old `[data-theme=dark]` attribute is removed).
- Print styles moved to a separate `print.css` loaded with `media="print"`.
- Alternative themes are standalone CSS files containing only an `@layer theme` block. Three themes are provided: `wexa_theme` (navy/teal), `aurora` (blue/mauve/violet) and `highcontrast`.
- New `ThemeManager` class: registers named themes, cycles through them, and persists the choice via URL parameter.
- New `SVGIconsManager` class: loads SVG icons from `icons/mono-svg/` and injects them inline so they inherit `currentColor`. `inject(element, name)` guards against double-injection. In bundle mode, icons are pre-registered at build time — no `fetch()` required on `file://`.
- `AccessibilityManager` manages exactly two modes — color (light/dark) and contrast (normal/high). Methods renamed to `switchColorScheme()` and `switchContrastScheme()`.
- Card inner zones renamed: use `<div class="card-header">`, `.card-body`, `.card-footer` inside `<article class="card">`.
- New `.cta-button` class in `button.css`.
- `code.css`: complete dark-mode color palette.
- Slides: new handout (`d`), overview (`o`) and memo (`m`) view modes. Speaker notes are now `<aside for="slide-id">` siblings, not nested inside the slide. A help dialog (`h` / `?`) lists all keyboard shortcuts. The slides loader auto-detects `file://` vs `http(s)://` and loads the bundle or ES module accordingly. Nav control font-size is controlled by `--slides-nav-font-size`, defined per view mode.

### Breaking changes:

| What changed | Old | New |
|---|---|---|
| Theme selector | `[data-theme=dark]` | `.dark` on `:root` |
| Card inner zones | `<header>`, `<main>`, `<footer>` | `.card-header`, `.card-body`, `.card-footer` |
| Slide notes | `<aside role="note">` inside slide | `<aside for="slide-id">` sibling |
| Toggleselect button | `.action-button` | `.toggleselect-action` |
| Book ToC nav | `.side-nav` | `.book-toc` |
| Book number variable | `--numbers-color` | `--numbers-bg-color` / `--numbers-fg-color` |
| Print styles | `@media print` per file | `print.css` |
| Accessibility button | `btn-theme` | `btn-color` |

### Known bugs

- `layout.css` alternates `panel-item` section backgrounds via `main > .panel-item:nth-child(even)`, which 
  redefines `--bg-color` and `--fg-color`. Some child elements (cards, code blocks, etc.) do not inherit these 
  redefined variables and render with the wrong background color.


## Version 3.1

- Extra Book. Added `abstract` class.
- Extra Book. Added `aside.book-toc-aside`: toggleable ToC panel, auto-injected toggle button, 
  new variable `--toc-aside-width`.
- Extra Book. Improved chapter and aside page-break handling.
- Extra Book. Theme support: chapter numbers use `--custom-color1` / `--custom-color2`.
- Themes. Corrected `--custom-color1` / `--custom-color2` in `highcontrast`.
- Extra KeyPiano. New extra: generic clickable "piano" of buttons composing a technical sequence into a target text field.
- Extra Slides. Added the missing "Note" (`m`) view mode to the nav menu.
- Extra Slides. Nav split into three sections: navigation, fullscreen, view mode.
- Extra Slides. Prev/First/Last/Next/GoTo buttons now use SVG icons (new `first.svg`, `last.svg`); 
  view-mode toggle renamed "Slides" (was "Slides View") and uses the new `.toggle-group`.
- Themes. Fixed `highcontrast` slide `h2` title: white text was unreadable on its yellow background.
- wexa.css. Fixed `--nav-bg-color` (light mode): flat gray replaced with a blue matching the theme's palette.
- menu.css. Added the missing `gap` on horizontal nav `> section` groups (top/bottom), already present on the side variant.
- New `togglegroup.css`. Generic segmented "toggle group" component for mutually-exclusive choices, 
  composable with `.menuitem`. Documented in `docs/button.html`.


## Version 3.2

- index.html. Fixed missing `./` in the `theme_manager.js` module import path.
- ThemeManager. Fixed `next()`: resumes after the default theme instead of the first registered one.
- OnLoadManager. Now registers its own `load` listener on first `addLoadFunction()` call.
- wexa.js. Removed the now-redundant manual `window.onload` wiring.
- New `.wrap-panel` / `.wrap-item` in layout.css. Space-driven flex wrap container.
- AccessibilityManager. New `data-named-target` attribute on plain `<a>` links.
- LinkController. Fixed named targets: the window name is now honored.
- Icons. New `info-square` icon, and removed the XML namespaces of the mono-svg icons.
- layout.css. Bug corrected. Alternating `panel-item` sections now swap the whole color pair. 
- New variables `--panel-bg-color`, `--panel-fg-color`, `--panel-bg-color-alt`, `--panel-fg-color-alt`. 
  Documented in `docs/layout.html`.


## Version 3.3

- Extra Book. New `bibbook.css`, new modules under `js/extras/book/`, Write your BibTeX on the page or in a `.bib` file
- Extra Book. Choose which columns of a bibliography are shown; on a narrow screen the reference is kept whole.
- Extra Book. Number the titles of a table of contents. New variable `--toc-number-width`.
- Extra Slides. Put a bibliography in a presentation: it is laid on as many slides as it takes.
- Icons SVG: New `unchecked` and `half-checked`.
- Fonts. A page downloads only the character blocks it displays. New `scripts/build_fonts_subsets.py`.
- Screens. One border between mobile and desktop, at 1024px.
- Logos. Lighter `whakerexa-512.webp` and `whakerexa-128.webp` to use instead of the png.


## Version 3.4

- Breaking change. An element no longer gets a background of its own. 
- Fonts. A page downloads none: the system fonts are used, and a theme brings the ones of the house back.
- New `--img-bg-color`. A theme can give an image background, in every mode.
- New `wexa_statics/css.min`: the same stylesheets, half the weight. Point your pages at it to serve them.
- New `--nav-height`, the room a nav bar takes: place under a bar with it.
- Extra Book. The number of a chapter is announced by its word, in the language of the page.


## Version 4.0.0

- New `KeyboardController` in `keyboard.js`, used by extra slides.
- New page `docs/javascript.html`: the JavaScript API, and the conventions a module follows.
- New page `docs/gallery.html`: an all-in-one page to demonstrate themes, accessibility and JS features.
- New `AccessibilityNav` builds the bar of three buttons, and `NAV_WORDING` says what 
  each one is called. 
- New : Bring your own icons. Declare sets of them, the reader chooses, and what you do not draw is still shown.
- New `wexa.loader.js`: one tag loads Whakerexa, the bundle on `file://` and the modules over HTTP.
- New `scripts/check_ecodesign.py`: what a served page downloads, and what it borrows from elsewhere.
- Fonts. The whole fonts move to `build/fonts/`: they are cut, never served.
- Icons. Extended and cleaned icon set in mono-svg: the same grid of 32, the same stroke of 2, rounded 
  caps and joins, and the color of the text it stands beside. Now 152 icons available.
- Dialogs. New `--dialog-bg-color` and `--dialog-fg-color` variables.
- Breaking change. `ThemeManager` moves to `js/customize/theme_manager.js`, and `SVGIconsManager` is removed: 
  `Wexa.icons` is now the manager of the sets, with the same `get()` and `inject()`.
- Breaking change. The JavaScript API is camelCase throughout: `fillTable`, `addHtmlTags`, 
  `deleteHtmlTags`, `sendPostRequest`, `sendGetRequest`, `requestUrl`.
- Loading. `wexa.loader.js` takes `data-themes`.


## Version 4.1.0 - stable

- Themes. `data-themes` says which ones a page takes, and in which order.
- Icons. New `Wexa.gatheredIcons`. A file written by an older build is still read.
- Themes. Slides read `data-themes` the way the loader does.
- Logging. A page says how much the framework says: `Wexa.logLevel = 'warning'`, before the loader.
