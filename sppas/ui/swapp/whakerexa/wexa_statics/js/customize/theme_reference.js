/**
 * :filename: statics.js.customize.theme_reference.js
 * :author: Brigitte Bigi
 * :contact: contact@sppas.org
 * :summary: What the framework carries as themes.
 *
 *  -------------------------------------------------------------------------
 *
 *  This file is part of Whakerexa: https://github.com/brigitte-bigi/Whakerexa
 *
 *  Copyright (C) 2023-2026 Brigitte Bigi, CNRS
 *  Laboratoire Parole et Langage, Aix-en-Provence, France
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU Affero General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU Affero General Public License for more details.
 *
 *  You should have received a copy of the GNU Affero General Public License
 *  along with this program.  If not, see <https://www.gnu.org/licenses/>.
 *
 *  This banner notice must not be removed.
 *
 *  -------------------------------------------------------------------------
 *
 *  Written by scripts/build_theme_reference.py. A page names a theme of the
 *  framework by its name alone: the list is read here and never asked for, so
 *  that a name is known with no request at all.
 */

'use strict';

/** Where the themes stand, from the base of wexa_statics. */
export const THEMES_BASE = 'css/themes/';

/** The themes it carries, the default one first. */
export const REFERENCE_THEMES = [
    ['wexa_theme', 'wexa_theme.css'],
    ['aurora', 'wexa_theme_aurora.css'],
    ['highcontrast', 'wexa_theme_highcontrast.css'],
];
