/**
 :filename: wexa_statics/js/extras/book/bibcontrols.js
 :author: Brigitte Bigi
 :contact: contact@sppas.org
 :summary: A class to sort and to search a bibliography.

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

import { SortaTable } from '../sortatable.js';
import { ToggleSelector } from '../../toggleselect.js';
import { BibliographyTable } from './bibtable.js';
import { Labels } from './labels.js';
import { icons } from '../../customize/icons.js';

/**
 * Sort and search a bibliography.
 *
 * Sorting is done by SortaTable, which the table was built for: its headers
 * carry the buttons it expects, and the cell of a reference carries the value
 * it is sorted on, the family name of its first author.
 *
 * Searching is new: SortaTable hides columns, not rows. A search keeps the
 * references a word appears in, and hides the others.
 *
 * Whatever changes is said, and not only shown: a reader who does not see the
 * table has no other way of knowing that it just became shorter.
 */
export class BibliographyControls {
    // CONSTANTS
    /**
     * What the program writes, in the languages it knows.
     */
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


    /**
     * The width under which the reference alone is shown, counted in fonts.
     *
     * A phone held sideways starts there. Under it, a column of two or four
     * characters still asks for its share, and the text is left with a dozen
     * characters a line. The width is counted in font sizes and not in pixels:
     * the contrast mode writes larger, and what is too narrow for a text of 16
     * is too narrow sooner for a text of 18.
     */
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
    /**
     * Instantiate the controls of a bibliography.
     *
     * The search field and what is said are written before the table, so that
     * a reader meets them before what they act upon.
     *
     * @param table {HTMLTableElement} The table of the bibliography.
     */
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
    /**
     * Get the field a word is searched from.
     *
     * @returns {HTMLElement}
     */
    get field() {
        return this.#field;
    }

    /**
     * Get what says aloud whatever changes.
     *
     * @returns {HTMLElement}
     */
    get announcement() {
        return this.#announcement;
    }


    // PUBLIC METHODS
    /**
     * Sort the bibliography on one of its columns.
     *
     * The numbers do not move: they were given by the order of the text, and
     * nothing here starts that again.
     *
     * @param column {string} The name of the column, as its button declares it.
     * @param isAscending {boolean} Whether the order goes up.
     * @returns {void}
     */
    sortBy(column, isAscending = true) {
        this.#sorter.sort(column, isAscending);
        this.#putOpenedRowsBack();
        BibliographyTable.stripe(this.#table);
        this.#sayHowItIsSorted();
    }

    /**
     * Keep the references a word appears in, and hide the others.
     *
     * The case and the accents of the word do not matter: someone looking for
     * "Andre" is looking for "André".
     *
     * @param word {string} The word to look for. An empty word shows everything.
     * @returns {void}
     */
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
    /**
     * Get the rows that hold what one reference opens.
     *
     * @param row {HTMLElement} The row of a reference.
     * @returns {HTMLElement[]} Its contents, possibly none.
     */
    #openedRowsOf(row) {
        return Array.from(this.#table.querySelectorAll(`tr.bib-opened-row[data-opens="${row.id}"]`));
    }

    /**
     * Tell whether a content is open.
     *
     * The answer is read on the control that opens it, which is the only
     * place where it is written.
     *
     * @param opened {HTMLElement} The row holding a content.
     * @returns {boolean}
     */
    #isOpen(opened) {
        const control = this.#table.querySelector(`[aria-controls="${opened.id}"]`);

        if (control === null) {
            return false;
        }

        return control.getAttribute('aria-expanded') === 'true';
    }

    /**
     * Get everything a reference is searched through.
     *
     * The abstract counts: someone looking for a word looks for it in what
     * the reference says, not only in its title.
     *
     * @param row {HTMLElement} The row of a reference.
     * @returns {string} What is searched.
     */
    #textOf(row) {
        const texts = [row.textContent];

        this.#openedRowsOf(row).forEach(opened => texts.push(opened.textContent));

        return texts.join(' ');
    }

    /**
     * Put every content back behind the reference it belongs to.
     *
     * Sorting moves rows, and knows nothing about the ones that hold a content
     * across the whole table. They are put back afterwards, in the order they
     * were built in.
     *
     * @returns {void}
     */
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

    /**
     * Build the field a word is searched from.
     *
     * No visible label: the magnifier wexa.css draws in a search field says
     * what it is, and the field carries its name for whoever does not see it.
     *
     * @returns {HTMLElement} The field itself: nothing has to hold it.
     */
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

    /**
     * Build the list of the columns that can be shown or hidden.
     *
     * The markup is the one the column selector of a sortable table is written
     * with: a details holding a list of check items, and a button that applies
     * what is checked. A document writes its data and its text; what acts upon
     * them is built here, with the search field.
     *
     * The button that applies carries a mark and not a word: a word is as long
     * as the language it is written in, and the line it stands on is the one
     * of a phone. What it does is said to whoever does not see the mark.
     *
     * @returns {HTMLElement} What holds the list and the button that applies it.
     */
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

            // A column whose header says it opens hidden is listed like the
            // others, and unchecked: what it holds is read by whoever asks for
            // it. The header decides, here nothing is named. B27.
            const startsHidden = header.hasAttribute('data-starts-hidden');

            const box = document.createElement('input');
            box.type = 'checkbox';
            box.id = this.#table.id + '-column-' + name;
            box.checked = startsHidden === false;
            box.setAttribute('data-toggle', name);
            box.setAttribute('aria-labelledby', box.id + '-label');

            if (startsHidden === true) {
                box.setAttribute('data-starts-hidden', '');
            }

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

    /**
     * Show the columns the width of the screen has room for.
     *
     * Nothing is taken away: the reader checks back whatever they want to read.
     * The columns are set when the page opens and each time the screen crosses
     * that width, a device turned over being the ordinary case; between two
     * crossings, what the reader checked is left alone.
     *
     * @returns {void}
     */
    #showColumnsTheWidthAllows() {
        const font = parseFloat(getComputedStyle(document.documentElement).fontSize);
        const isNarrow = window.innerWidth < BibliographyControls.NARROW_WIDTH_IN_FONTS * font;
        if (isNarrow === this.#wasNarrow) {
            return;
        }
        this.#wasNarrow = isNarrow;

        this.#selector.getCheckboxes().forEach(box => {
            if (box.hasAttribute('data-starts-hidden') === true) {
                box.checked = false;
                return;
            }

            box.checked = isNarrow === false || box.getAttribute('data-toggle') === 'author';
        });

        this.#applyColumns();
    }

    /**
     * Apply to the table what the checkboxes say.
     *
     * Nothing is announced: what the boxes say is what the table shows, and a
     * count of columns tells a reader nothing they cannot see.
     *
     * @returns {void}
     */
    #applyColumns() {
        this.#sorter.toggleColumnVisibility(this.#selector.getCheckboxes());
    }

    /**
     * Build what says aloud whatever changes.
     *
     * @returns {HTMLElement} A region a screen reader reads when it changes.
     */
    #buildAnnouncement() {
        const region = document.createElement('p');
        region.className = 'bib-announcement';
        region.setAttribute('role', 'status');
        region.setAttribute('aria-live', 'polite');

        return region;
    }

    /**
     * Listen to the buttons of the headers, to say what they just did.
     *
     * SortaTable does the sorting itself; these listeners are added after its
     * own, so that the state of the buttons is already the new one.
     *
     * @returns {void}
     */
    #watchSortButtons() {
        this.#table.querySelectorAll('button.sortatable').forEach(button => {
            button.addEventListener('click', () => {
                this.#putOpenedRowsBack();
                BibliographyTable.stripe(this.#table);
                this.#sayHowItIsSorted();
            });
        });
    }

    /**
     * Say on which column and in which order the bibliography is sorted.
     *
     * @returns {void}
     */
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

    /**
     * Say how many references are left after a search.
     *
     * @param shown {number} How many references are still displayed.
     * @returns {void}
     */
    #sayHowManyAreShown(shown) {
        if (shown === 1) {
            this.#announce(`1 ${this.#texts.text('shownOne')}`);
            return;
        }

        this.#announce(`${shown} ${this.#texts.text('shownMany')}`);
    }

    /**
     * Say something aloud.
     *
     * @param text {string} What to say.
     * @returns {void}
     */
    #announce(text) {
        this.#announcement.textContent = text;
        this.#texts.declare(this.#announcement);
    }


    // PRIVATE STATIC METHODS
    /**
     * Write a text the way it is compared: lower case, and without accents.
     *
     * @param text {string} The text to simplify.
     * @returns {string} What is compared.
     */
    static #simplify(text) {
        return text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
    }
}
