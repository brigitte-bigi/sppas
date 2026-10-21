/**
 :filename: wexa_statics/js/extras/book/bibtable.js
 :author: Brigitte Bigi
 :contact: contact@sppas.org
 :summary: A class to build the table of a bibliography.

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

import { Citation } from './bibcitation.js';
import { ReferenceFormatter } from './bibformatter.js';
import { Link, LinkKind } from './biblink.js';
import { Labels } from './labels.js';

/**
 * Build the table of a bibliography.
 *
 * The table holds one row per reference, whether it is cited or not: the
 * bibliography lists what the BibTeX data holds, and knows nothing about the
 * citations. What the text owes to a reference, its number and the places it
 * is cited at, is handed over from the outside, and the number column only
 * exists when there is something to put in it.
 */
export class BibliographyTable {
    // CONSTANTS
    /**
     * The identifier of the table, needed to sort it afterwards.
     */
    static TABLE_ID = 'bibliography-table';

    /**
     * What starts the identifier of a row, so that a citation can lead to it.
     */
    static ROW_PREFIX = 'bib-';

    /**
     * What a reference without a number is sorted on.
     *
     * An empty cell would sort before every number, and a reference nobody
     * cites would come first of all. It has no number at all, so it goes after
     * every reference that has one.
     */
    static UNCITED_SORT_VALUE = String(Number.MAX_SAFE_INTEGER);

    /**
     * What tells apart two ways back to a reference cited more than once.
     */
    static BACK_SEPARATOR = '-';

    /**
     * What the program writes, in the languages it knows.
     *
     * A language it does not know falls back on English, and what is written
     * then says so, as WCAG 3.1.2 asks.
     */
    static LABELS = new Map([
        ['en', {
            number: 'No.', year: 'Year', type: 'Type', reference: 'Reference',
            abstract: 'Abstract', source: 'BibTeX', backTo: 'Back to citation',
            pdf: 'PDF', repository: 'Open archive', publisher: 'Publisher', other: 'Link',
            of: 'of'
        }],
        ['fr', {
            number: 'N°', year: 'Année', type: 'Type', reference: 'Référence',
            abstract: 'Résumé', source: 'BibTeX', backTo: 'Retour à la citation',
            pdf: 'PDF', repository: 'Archive ouverte', publisher: 'Éditeur', other: 'Lien',
            of: 'de'
        }]
    ]);

    // FIELDS
    #formatter;
    #texts;


    // CONSTRUCTOR
    /**
     * Instantiate the builder of the table.
     *
     * @param formatter {ReferenceFormatter} What displays a reference according to its type.
     */
    constructor(formatter = new ReferenceFormatter()) {
        this.#formatter = formatter;
        this.#texts = new Labels(BibliographyTable.LABELS);
    }


    // PUBLIC METHODS
    /**
     * Build the table of the bibliography.
     *
     * @param references {Map} The references, by key.
     * @param cited {Map} What the text owes to each cited reference, by key. May be empty.
     * @returns {HTMLTableElement} The table, ready to be put in the page.
     */
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

    /**
     * Mark one row out of two, counting the references only.
     *
     * Striping a table of a hundred rows is what lets an eye follow one of
     * them across its columns. Counting every row would count the contents
     * that open, and the colours would shift by one as soon as anything
     * opened; a content takes the colour of the reference it belongs to, so
     * that the two read as one.
     *
     * Rows that a search hides are not counted: the stripes follow what is
     * displayed, not what exists.
     *
     * @param table {HTMLTableElement} The table of the bibliography.
     * @returns {void}
     */
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
    /**
     * Build the headers of the table.
     *
     * A header carries a button rather than a listener of its own: sorting is
     * attached afterwards, and a button is what a keyboard reaches.
     *
     * @param hasNumbers {boolean} Whether the number column exists.
     * @returns {HTMLElement} The head of the table.
     */
    #buildHead(hasNumbers) {
        const head = document.createElement('thead');
        const row = document.createElement('tr');

        if (hasNumbers === true) {
            row.appendChild(this.#buildHeader('number', true));
        }
        row.appendChild(this.#buildHeader('year', true));

        // What nothing else writes: a reference is displayed by the fields its
        // type asks for, and two types ask for the same ones. The column opens
        // unchecked, a bibliography being read for its references. B27.
        const type = this.#buildHeader('type', true);
        type.setAttribute('data-starts-hidden', '');
        row.appendChild(type);

        row.appendChild(this.#buildHeader('reference', true, 'author'));

        head.appendChild(row);

        return head;
    }

    /**
     * Build one header.
     *
     * @param name {string} The label to write.
     * @param isSortable {boolean} Whether the column can be sorted on.
     * @param sortName {string} What the column is called when sorting, when it differs.
     * @returns {HTMLElement} The header.
     */
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

    /**
     * Build the row of one reference.
     *
     * @param reference {Reference} The reference to display.
     * @param cited {CitedReference} What the text owes to it, or undefined when it is never cited.
     * @param hasNumbers {boolean} Whether the number column exists.
     * @returns {HTMLElement} The row.
     */
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

        // What the formatter calls this type, and never what BibTeX wrote:
        // "@Article", "@article" and "@ARTICLE" are one type, and a column
        // that repeated them would read as three. The column sorts as it
        // reads, so the value to sort on is the written name. B27.
        const written = this.#formatter.nameOf(reference.type);

        const type = document.createElement('td');
        type.className = 'bib-type';
        type.textContent = written;
        type.setAttribute('data-sort-value', written.toLowerCase());
        row.appendChild(type);

        row.appendChild(this.#buildReferenceCell(reference, cited));

        return row;
    }

    /**
     * Build the cell that displays the reference.
     *
     * The cell carries the value to sort on, because a bibliography is sorted
     * by its first author, and the first author is not displayed apart.
     *
     * @param reference {Reference} The reference to display.
     * @param cited {CitedReference} What the text owes to it, or undefined.
     * @returns {HTMLElement} The cell.
     */
    #buildReferenceCell(reference, cited) {
        const cell = document.createElement('td');
        cell.className = 'bib-reference';
        cell.setAttribute('data-sort-value', this.#sortValueOf(reference));
        cell.appendChild(this.#formatter.format(reference));

        cell.appendChild(this.#buildActions(reference, cited));

        return cell;
    }

    /**
     * Build what leads to the publication and what opens on demand.
     *
     * They stand under the reference they belong to. A column of their own
     * would be as wide as its widest label and say nothing.
     *
     * @param reference {Reference} The reference to display.
     * @param cited {CitedReference} What the text owes to it, or undefined.
     * @returns {HTMLElement} The addresses, the controls, and the way back to the text.
     */
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

    /**
     * Get the value the row is sorted on when sorting by author.
     *
     * A reference without any author falls back on its title, so that it takes
     * a place in the order instead of gathering with the others at one end.
     *
     * @param reference {Reference} The reference to sort.
     * @returns {string} The value to sort on.
     */
    #sortValueOf(reference) {
        const authors = reference.authors;

        if (authors.length === 0) {
            return reference.field('title');
        }

        return authors[0].sortValue();
    }

    /**
     * Build a link back to every place of the text where a reference is cited.
     *
     * A way back bears the same mark as the citation it leads to, written the
     * same way: the reader recognises "[12]" on both sides. When a reference
     * is cited more than once, a letter tells the ways back apart.
     *
     * A place without an identifier cannot be reached, and is left out rather
     * than turned into a link that leads nowhere.
     *
     * @param places {HTMLElement[]} Where the reference is cited, in the order of the text.
     * @param number {number} The number the reference bears in the text.
     * @returns {DocumentFragment} The links, possibly none.
     */
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

    /**
     * Get what a reference has to offer that opens on demand.
     *
     * @param reference {Reference} The reference to display.
     * @returns {Object[]} A name and a text for each of them.
     */
    #openableOf(reference) {
        const openable = [];

        if (reference.abstract.length > 0) {
            openable.push({name: 'abstract', text: reference.abstract});
        }
        openable.push({name: 'source', text: reference.sourceWithoutAbstract});

        return openable;
    }

    /**
     * Build a link to the publication.
     *
     * What the link says is what it leads to, read in the address itself: the
     * name of the BibTeX field it came from says nothing.
     *
     * @param link {Link} The address to reach.
     * @returns {HTMLElement} The link.
     */
    #buildLink(link, reference) {
        const element = document.createElement('a');

        // Every address of a reference leaves the document: the reader is told
        // so before following it, the way Whakerexa marks any outward link.
        element.className = 'bib-link external-link';
        element.setAttribute('href', link.address);

        // The class says the link leaves the document, the attribute says
        // where it opens: what a reader is told, and what a browser does.
        Link.openIn(element);

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

    /**
     * Get the name a screen reader gives to one link.
     *
     * @param label {string} What the link leads to: a PDF, an archive, a publisher.
     * @param reference {Reference} The reference the link belongs to.
     * @returns {string} A name no other link of the page bears.
     */
    #nameOf(label, reference) {
        const title = reference.field('title');

        if (title.length === 0) {
            return this.#texts.text(label);
        }

        return this.#texts.text(label) + ' ' + this.#texts.text('of') + ' ' + title;
    }

    /**
     * Build the control that opens a content.
     *
     * The control says itself whether it is open or closed, and names what it
     * opens: the content is a row of its own, further down.
     *
     * @param key {string} The key of the reference, which makes the identifiers unique.
     * @param name {string} What is opened: the abstract or the BibTeX source.
     * @returns {HTMLElement} The control.
     */
    #buildControl(key, name) {
        const control = document.createElement('button');
        control.type = 'button';
        control.className = 'bib-disclosure-control';
        control.setAttribute('aria-expanded', 'false');
        control.setAttribute('aria-controls', BibliographyTable.#contentId(key, name));
        this.#texts.write(control, name);

        return control;
    }

    /**
     * Build the rows that hold what opens on demand.
     *
     * A content takes a row of its own, across the whole table: an abstract
     * read in the width of one column is an abstract nobody reads. The row
     * follows the one of its reference, so that the keyboard reaches it by
     * going on, and it carries the key it belongs to, so that sorting can put
     * it back where it belongs.
     *
     * @param reference {Reference} The reference to display.
     * @param columns {number} How many columns the table has.
     * @returns {HTMLElement[]} One row per content that opens.
     */
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
    /**
     * Put the references in the order they are read in.
     *
     * The numbers come first, and they go up: reading the bibliography from
     * one end to the other, a reader follows the text. What is never cited
     * has no number and comes after, by year, oldest first.
     *
     * This is also the order the bibliography is printed in, whatever the
     * reader sorted it by on screen before.
     *
     * @param references {Map} The references, by key.
     * @param cited {Map} What the text owes to each cited reference, by key.
     * @returns {Reference[]} The references, in the order they are displayed.
     */
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

    /**
     * Get the number a reference bears in the text.
     *
     * @param reference {Reference} The reference to place.
     * @param cited {Map} What the text owes to each cited reference, by key.
     * @returns {number} Its number, or a number no reference can reach.
     */
    static #numberOf(reference, cited) {
        const owed = cited.get(reference.key);

        if (owed === undefined) {
            return Number.MAX_SAFE_INTEGER;
        }

        return owed.number;
    }

    /**
     * Get what tells one way back from the others.
     *
     * A reference cited once needs nothing: its mark is enough. Cited more
     * than once, each way back gets a letter, a to z, then aa, ab, and so on.
     *
     * @param order {number} Which way back it is, from 0 up.
     * @param total {number} How many there are.
     * @returns {string} The suffix, empty when there is only one.
     */
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

    /**
     * Get how many columns the table has.
     *
     * @param hasNumbers {boolean} Whether the number column exists.
     * @returns {number} The number of columns.
     */
    static #columnCount(hasNumbers) {
        if (hasNumbers === true) {
            return 4;
        }

        return 3;
    }

    /**
     * Get the identifier of a content that opens.
     *
     * @param key {string} The key of the reference.
     * @param name {string} What is opened: the abstract or the BibTeX source.
     * @returns {string} The identifier, unique in the page.
     */
    static #contentId(key, name) {
        return BibliographyTable.ROW_PREFIX + key + '-' + name;
    }

    /**
     * Get the label that says what an address leads to.
     *
     * @param kind {string} One of the LinkKind values.
     * @returns {string} The name of the label to write.
     */
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
