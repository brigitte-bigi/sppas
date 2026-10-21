/**
 :filename: wexa_statics/js/extras/book/bibformatter.js
 :author: Brigitte Bigi
 :contact: contact@sppas.org
 :summary: A class to display a bibliographic reference according to its type.

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
'use strict';

import { Labels } from './labels.js';

/**
 * Display a bibliographic reference according to its type.
 *
 * A journal article and a talk are not read the same way, and do not carry the
 * same fields. Which fields a type shows, and in which order, is written in
 * one place: changing a display is changing a template, and nothing else.
 *
 * Every field is written in an element of its own, and the stylesheet decides
 * what it looks like. Nothing here knows about italics.
 */
export class ReferenceFormatter {
    // CONSTANTS
    /**
     * Which fields each type shows, and in which order.
     *
     * A type that is not listed falls back on FALLBACK_TEMPLATE, so that a
     * reference is always displayed, whatever its type.
     */
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

    /**
     * Which fields a type cannot do without.
     *
     * One of these missing is worth showing, because the reference cannot be
     * found again without it. Any other missing field leaves no trace: an
     * article without a volume is not an article with a hole.
     */
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

    /**
     * What is required of a type nobody planned for: a title, and nothing
     * more. Guessing what an unknown type needs would only be guessing.
     */
    static FALLBACK_REQUIRED = ['title'];

    /**
     * What stands between two fields, and what closes a line.
     */
    static SEPARATOR = ', ';
    static TERMINATOR = '.';

    /**
     * What surrounds the year, which follows the authors rather than being
     * listed with the rest: a reader looks for a name and a date first.
     */
    static YEAR_OPENING = ' (';
    static YEAR_CLOSING = ')';

    /**
     * What each type is called, in the languages the program knows.
     *
     * BibTeX writes "@Article", "@article" and "@ARTICLE" for one same type,
     * and a column that repeated them would read as three. A type nobody
     * planned for is written as the data wrote it, its first letter in
     * capital: naming it would only be guessing.
     */
    static TYPE_NAMES = new Map([
        ['en', {
            article: 'Article', inproceedings: 'Conference',
            conference: 'Conference', incollection: 'Chapter',
            inbook: 'Chapter', book: 'Book', techreport: 'Report',
            phdthesis: 'PhD thesis', mastersthesis: "Master's thesis",
            unpublished: 'Unpublished', misc: 'Miscellaneous'
        }],
        ['fr', {
            article: 'Article', inproceedings: 'Communication',
            conference: 'Communication', incollection: 'Chapitre',
            inbook: 'Chapitre', book: 'Ouvrage', techreport: 'Rapport',
            phdthesis: 'Thèse', mastersthesis: 'Mémoire',
            unpublished: 'Non publié', misc: 'Divers'
        }]
    ]);

    /**
     * What each line is called, whatever the type of the reference.
     *
     * The names do not change from one type to the next: a stylesheet that
     * wants the three lines side by side, or wrapped, has one name to reach
     * them by.
     */
    static LINE_NAMES = ['authors', 'title', 'source'];


    // FIELDS
    #texts;


    // CONSTRUCTOR
    /**
     * Instantiate what displays a reference.
     */
    constructor() {
        this.#texts = new Labels(ReferenceFormatter.TYPE_NAMES);
    }


    // PUBLIC METHODS
    /**
     * Say what a type is called, in the language of the document.
     *
     * The case of the type is ignored, BibTeX being written by hand. A type
     * that is not named is written as it was, its first letter in capital.
     *
     * @param type {string} The entry type, as written.
     * @returns {string} What to write for it.
     */
    nameOf(type) {
        const wanted = type.toLowerCase();
        const written = this.#texts.text(wanted);

        if (written === undefined) {
            return wanted.charAt(0).toUpperCase() + wanted.slice(1);
        }

        return written;
    }

    /**
     * Display a reference.
     *
     * Every author is written, whatever their number: a bibliography that
     * hides names behind "et al." hides people who did the work.
     *
     * @param reference {Reference} The reference to display.
     * @returns {DocumentFragment} What to put in a cell, never empty.
     */
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
    /**
     * Display one line of a reference.
     *
     * A reference read as a single run of commas is a reference nobody reads:
     * who wrote it, what it is called, and where it came out are three
     * questions, and each of them gets its own line.
     *
     * @param reference {Reference} The reference being displayed.
     * @param fields {string[]} The fields of this line, in order.
     * @param required {string[]} The fields the type cannot do without.
     * @param order {number} Which line it is, from 0 up.
     * @returns {HTMLElement} The line, or null when it would hold nothing.
     */
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

    /**
     * Display one field of a reference.
     *
     * @param reference {Reference} The reference being displayed.
     * @param name {string} The name of the field.
     * @param isRequired {boolean} Whether the type cannot do without it.
     * @returns {HTMLElement} The element to add, or null when there is nothing to say.
     */
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

    /**
     * Display a field that is missing.
     *
     * What is missing is written in full rather than left out, so that it is
     * seen on screen, read by a screen reader, and noticed by whoever keeps
     * the BibTeX data.
     *
     * @param name {string} The name of the missing field.
     * @returns {HTMLElement} The element to add.
     */
    #formatMissing(name) {
        const element = document.createElement('span');
        element.className = 'bib-missing';
        element.textContent = '[' + name + ']';
        element.setAttribute('title', 'This reference has no ' + name + '.');

        return element;
    }

    /**
     * Get the fields a type shows, and in which order.
     *
     * The case of the type is ignored: BibTeX is written by hand, and
     * "@Article" and "@article" are the same type seen twice.
     *
     * @param type {string} The entry type, as written.
     * @returns {string[]} The fields to show, never empty.
     */
    #templateFor(type) {
        const wanted = type.toLowerCase();

        if (ReferenceFormatter.TEMPLATES.has(wanted) === false) {
            return ReferenceFormatter.FALLBACK_TEMPLATE;
        }

        return ReferenceFormatter.TEMPLATES.get(wanted);
    }

    /**
     * Get the fields a type cannot do without.
     *
     * @param type {string} The entry type, as written.
     * @returns {string[]} The fields to show as missing when they are absent.
     */
    #requiredFor(type) {
        const wanted = type.toLowerCase();

        if (ReferenceFormatter.REQUIRED.has(wanted) === false) {
            return ReferenceFormatter.FALLBACK_REQUIRED;
        }

        return ReferenceFormatter.REQUIRED.get(wanted);
    }
}
