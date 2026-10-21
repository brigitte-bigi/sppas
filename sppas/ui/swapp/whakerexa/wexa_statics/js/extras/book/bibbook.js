/**
 :filename: wexa_statics/js/extras/book/bibbook.js
 :author: Brigitte Bigi
 :contact: contact@sppas.org
 :summary: A class to build the bibliography of a document when its page opens.

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

import { BibtexSource } from './bibsource.js';
import { BibtexParser } from './bibparser.js';
import { CitationIndex } from './bibcite.js';
import { BibliographyTable } from './bibtable.js';
import { ReferenceDisclosure } from './bibdisclosure.js';
import { BibliographyControls } from './bibcontrols.js';
import { Link } from './biblink.js';
import { BibliographyError, MissingBibliographyPlace } from './biberrors.js';

/**
 * Build the bibliography of a document when its page opens.
 *
 * This class is the one that knows in which order the work is done, and it is
 * the only one that does: reading the data, then preparing the references,
 * then composing the bibliography. It is also the only place where an error is
 * caught. Whatever happens, run() never raises: a page that opens a
 * bibliography has nothing to protect itself from, and a document whose data
 * are missing is still a document.
 *
 * Nobody runs anything: the author writes BibTeX entries and text, and the
 * work happens in the browser of whoever opens the page.
 */
export class BookBibliography {
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
    /**
     * Instantiate the bibliography of a document.
     *
     * @param dataId {string} The id of the element holding the BibTeX data.
     * @param placeId {string} The id of the element where the bibliography goes.
     * @param contentId {string} The id of the element holding the text to read citations from.
     * @param address {string} The address of a BibTeX file, when the data are not in the page.
     */
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
    /**
     * Get the contents that can be opened, one per abstract and per source.
     *
     * @returns {ReferenceDisclosure[]} A copy, empty until run() has been called.
     */
    get disclosures() {
        return [...this.#disclosures];
    }

    /**
     * Get what numbers the citations of the text.
     *
     * @returns {CitationIndex} Empty until run() has read the text.
     */
    get citationIndex() {
        return this.#citationIndex;
    }

    /**
     * Get what sorts and searches the bibliography.
     *
     * @returns {BibliographyControls} Null until run() has built the table.
     */
    get controls() {
        return this.#controls;
    }


    // PUBLIC METHODS
    /**
     * Do the whole work, and never raise.
     *
     * The promise is what the table of contents waits for: the bibliography
     * carries a heading, and has to exist before the headings are gathered.
     *
     * @returns {Promise<void>} Kept once everything is done, or once it cannot be.
     */
    async run() {
        try {
            const content = await this.#source.read();
            const references = this.#parser.parse(content);

            // Where the addresses open is read once, before the first one is
            // written, and it is read where the bibliography stands. A page
            // that says nothing opens a tab of its own. B28.
            this.#takeWhereAddressesOpen();

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
    /**
     * Take where the page says its addresses open.
     *
     * The element where the bibliography stands carries it, written as HTML
     * writes it: data-links-target="_self" to stay in the document. What is
     * not said, and what is not one of the two, leaves the tab of its own.
     *
     * @returns {void}
     */
    #takeWhereAddressesOpen() {
        Link.resetTarget();

        const place = document.getElementById(this.#placeId);
        if (place === null) {
            return;
        }

        const said = place.getAttribute('data-links-target');
        if (said === null) {
            return;
        }

        Link.setTarget(said);
    }

    /**
     * Give a life to every content the table wrote as opening on demand.
     *
     * The table writes the control and the content; what opens and closes them
     * is put on top afterwards, so that neither has to know the other.
     *
     * @param roots {HTMLElement[]} Where to look, one of them possibly null.
     * @returns {ReferenceDisclosure[]} One per content that opens, never two.
     */
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

    /**
     * Say what went wrong, to whoever wrote the document.
     *
     * The reader is told nothing: a bibliography that could not be built is
     * not their doing, and a page that shouts about it is worse than a page
     * without a bibliography.
     *
     * @param error {BibliographyError} What went wrong.
     * @returns {void}
     */
    #report(error) {
        console.error(`BookBibliography: ${error.message}`);
    }
}
