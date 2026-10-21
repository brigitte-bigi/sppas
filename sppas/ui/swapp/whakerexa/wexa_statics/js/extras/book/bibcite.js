/**
 :filename: wexa_statics/js/extras/book/bibcite.js
 :author: Brigitte Bigi
 :contact: contact@sppas.org
 :summary: A class to number the citations of a text and tie them to references.

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
import { CitedKey } from './bibcitedkey.js';
import { CitedReference } from './bibcitedref.js';
import { Link } from './biblink.js';
import { ReferenceFormatter } from './bibformatter.js';
import { BibliographyTable } from './bibtable.js';
import { Labels } from './labels.js';

/**
 * Number the citations of a text and tie them to references.
 *
 * A reference is numbered the first time it is cited, and every later citation
 * of it carries that same number. Numbers follow the order the citations
 * appear in the text, and there is a single sequence for the whole document:
 * reading it from one end to the other, the numbers go up, which is what tells
 * a reader whether a reference is a new one without opening anything.
 *
 * Nothing is kept from one reading to the next. The order of the text does not
 * change, so opening the page again gives the same numbers.
 *
 * A key that names no reference is said in the console, and the citation says
 * so where it stands. Nothing raises: a key someone mistyped is not a reason
 * to leave a document without its other citations.
 */
export class CitationIndex {
    // CONSTANTS
    /**
     * What a citation looks like in the source of a document.
     *
     * A span is allowed between two words of a sentence, and the attribute is
     * what tells a citation from a "cite" element bearing a title.
     */
    static CITATION_SELECTOR = '[data-bibtex]';

    /**
     * Where the key is written.
     */
    static KEY_ATTRIBUTE = 'data-bibtex';

    /**
     * What the program writes, in the languages it knows.
     */
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
    /**
     * Instantiate what numbers the citations of a document.
     *
     * @param formatter {ReferenceFormatter} What displays a reference according to its type.
     */
    constructor(formatter = new ReferenceFormatter()) {
        this.#citations = [];
        this.#numbersByKey = new Map();
        this.#placesByKey = new Map();
        this.#formatter = formatter;
        this.#texts = new Labels(CitationIndex.LABELS);
    }


    // GETTERS
    /**
     * Get the citations, in the order they appear in the text.
     *
     * @returns {Citation[]} A copy, empty until index() has been called.
     */
    get citations() {
        return [...this.#citations];
    }


    // PUBLIC METHODS
    /**
     * Read the text, number every citation, and make each of them show it.
     *
     * @param root {HTMLElement} The element holding the text to read.
     * @param references {Map} The references, by key.
     * @returns {void}
     */
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

    /**
     * Get what the text owes to each reference it cites.
     *
     * This is what the bibliography receives: it never asks the citations
     * anything, so that a page without any of them gets its table all the same.
     *
     * @returns {Map} A CitedReference by key. Empty when nothing is cited.
     */
    citedReferences() {
        const cited = new Map();

        this.#numbersByKey.forEach((number, key) => {
            cited.set(key, new CitedReference(number, this.#placesOf(key)));
        });

        return cited;
    }


    // PRIVATE METHODS
    /**
     * Build what a citation opens: the whole reference, without leaving the
     * sentence.
     *
     * Everything is written at once rather than behind one more control: a
     * reader who opens a citation wants the reference, not another door. What
     * it holds is phrasing content, so that a paragraph stays a paragraph.
     *
     * @param reference {Reference} The reference that is cited.
     * @returns {DocumentFragment} What opens under the citation.
     */
    #buildContent(reference) {
        const content = document.createDocumentFragment();

        content.appendChild(this.#formatter.format(reference));
        content.appendChild(this.#buildBibliographyLink(reference.key));

        reference.links.forEach(link => {
            const address = document.createElement('a');
            address.className = 'bib-link external-link';
            address.setAttribute('href', link.address);
            address.textContent = link.address;
            Link.openIn(address);
            content.appendChild(address);
        });

        if (reference.abstract.length > 0) {
            content.appendChild(this.#buildPart('abstract', reference.abstract));
        }

        return content;
    }

    /**
     * Build the link that leads to the reference in the bibliography.
     *
     * @param key {string} The key of the reference.
     * @returns {HTMLElement} The link.
     */
    #buildBibliographyLink(key) {
        const link = document.createElement('a');
        link.className = 'bib-citation-link';
        link.setAttribute('href', '#' + BibliographyTable.ROW_PREFIX + key);
        this.#texts.write(link, 'inBibliography');

        return link;
    }

    /**
     * Build one named part of what a citation opens.
     *
     * @param name {string} What it is: the abstract.
     * @param text {string} What is written inside.
     * @returns {HTMLElement} The part, with its name before it.
     */
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

    /**
     * Give back a reference, or null when there is none.
     *
     * A Map gives undefined for a key it does not hold; a cited key that names
     * nothing holds null, which is the one absence this project writes.
     *
     * @param reference {Reference} What the Map gave back.
     * @returns {Reference} The reference, or null.
     */
    #found(reference) {
        if (reference === undefined) {
            return null;
        }

        return reference;
    }

    /**
     * Get the number of a key, giving it a new one the first time.
     *
     * @param key {string} The key of a reference that exists.
     * @returns {number} Its number, from 1 up, without a gap.
     */
    #numberOf(key) {
        if (this.#numbersByKey.has(key) === false) {
            this.#numbersByKey.set(key, this.#numbersByKey.size + 1);
        }

        return this.#numbersByKey.get(key);
    }

    /**
     * Remember where a reference is cited.
     *
     * @param key {string} The key of the reference.
     * @param element {HTMLElement} Where it is cited.
     * @returns {void}
     */
    #rememberPlace(key, element) {
        if (this.#placesByKey.has(key) === false) {
            this.#placesByKey.set(key, []);
        }

        this.#placesByKey.get(key).push(element);
    }

    /**
     * Get the places of the text where a reference is cited.
     *
     * @param key {string} The key of the reference.
     * @returns {HTMLElement[]} The places, in the order of the text.
     */
    #placesOf(key) {
        if (this.#placesByKey.has(key) === false) {
            return [];
        }

        return [...this.#placesByKey.get(key)];
    }
}
