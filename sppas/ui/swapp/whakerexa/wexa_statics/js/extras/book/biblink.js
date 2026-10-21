/**
 :filename: wexa_statics/js/extras/book/biblink.js
 :author: Brigitte Bigi
 :contact: contact@sppas.org
 :summary: A class to represent an address where a publication can be reached.

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

/**
 * What an address leads to.
 *
 * A reader does not choose a link for its address but for what is at the end
 * of it: the document itself, a page that gives it away, or the page of the
 * publisher.
 */
export const LinkKind = Object.freeze({
    PDF: 'pdf',
    REPOSITORY: 'repository',
    PUBLISHER: 'publisher',
    OTHER: 'other'
});

/**
 * An address where a publication can be reached.
 *
 * A link only exists as part of a reference, and its address is what tells it
 * apart from the others.
 *
 * BibTeX has a single URL field. When two addresses are needed, NOTE holds the
 * second one. This is a habit of the house, not a standard, so the name of the
 * field says nothing about where its address leads. That is read in the
 * address itself.
 *
 * A link never changes once it is built.
 */
export class Link {
    // CONSTANTS
    /**
     * Hosts that give a document away rather than sell it.
     *
     * The list is short on purpose: an unknown host is a link like any other,
     * and is shown as such. Every field has its own archives, so a document
     * adds the ones it cites with addRepositoryHosts().
     */
    static DEFAULT_REPOSITORY_HOSTS = ['hal.science', 'archives-ouvertes.fr', 'arxiv.org', 'zenodo.org'];

    /**
     * What a DOI looks like in an address, whichever form it takes.
     */
    static PUBLISHER_MARKS = ['doi.org', '/doi/'];

    /**
     * Where an address opens when the page says nothing.
     *
     * A bibliography is read alongside what cites it, and a reader who
     * follows an address has not finished reading: the document stays as it
     * was, and the address opens beside it. B28.
     */
    static DEFAULT_TARGET = '_blank';

    /**
     * Where an address may open: what HTML already writes, and nothing else.
     */
    static TARGETS = ['_self', '_blank'];

    // FIELDS
    /**
     * The hosts currently known as archives, shared by every link.
     */
    static #repositoryHosts = [...Link.DEFAULT_REPOSITORY_HOSTS];

    /**
     * Where the addresses of this page open, shared by every link.
     */
    static #target = Link.DEFAULT_TARGET;

    #address;


    // PUBLIC STATIC METHODS
    /**
     * Get the hosts currently known as archives.
     *
     * @returns {string[]} A copy: the list only changes through the methods below.
     */
    static get repositoryHosts() {
        return [...Link.#repositoryHosts];
    }

    /**
     * Add hosts to the ones known as archives.
     *
     * A host already known is not added twice, so that calling this from two
     * places costs nothing.
     *
     * @param hosts {string} (0, n) The hosts to add, "openaccess.example.org" for instance.
     * @returns {void}
     */
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

    /**
     * Remove hosts from the ones known as archives.
     *
     * A host that is not known is left alone, and said so: it is most often a
     * spelling mistake.
     *
     * @param hosts {string} (0, n) The hosts to remove
     * @returns {void}
     */
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

    /**
     * Give back the hosts known as archives the way they were at the start.
     *
     * @returns {void}
     */
    static resetRepositoryHosts() {
        Link.#repositoryHosts = [...Link.DEFAULT_REPOSITORY_HOSTS];
    }

    /**
     * Get where the addresses of this page open.
     *
     * @returns {string} "_blank" or "_self".
     */
    static get target() {
        return Link.#target;
    }

    /**
     * Say where the addresses of this page open.
     *
     * One page, one answer: a document does not open some of its addresses
     * one way and the rest another. What is neither of the two is said and
     * changes nothing.
     *
     * @param said {string} "_blank" or "_self".
     * @returns {void}
     */
    static setTarget(said) {
        if (Link.TARGETS.includes(said) === false) {
            console.warn(`Link.setTarget: "${said}" is not where an address opens.`
                + ` It is "${Link.TARGETS.join('" or "')}".`);
            return;
        }
        Link.#target = said;
    }

    /**
     * Give back where the addresses open the way it was at the start.
     *
     * @returns {void}
     */
    static resetTarget() {
        Link.#target = Link.DEFAULT_TARGET;
    }

    /**
     * Say on an element where it opens.
     *
     * A page opened in a tab of its own otherwise keeps a handle on the one
     * that opened it, and an address of a reference comes from data the
     * document did not write: nothing is handed over. B28.
     *
     * @param element {HTMLElement} The link that leads outside.
     * @returns {void}
     */
    static openIn(element) {
        element.setAttribute('target', Link.#target);

        if (Link.#target === '_blank') {
            element.setAttribute('rel', 'noopener');
        }
    }


    // CONSTRUCTOR
    /**
     * Instantiate a link.
     *
     * @param address {string} The address, as written in the BibTeX data.
     */
    constructor(address) {
        this.#address = address;
    }


    // GETTERS
    /**
     * Get the address.
     *
     * It is given back exactly as it was written, because printing writes it
     * in full and a reader has to be able to type it again.
     *
     * @returns {string}
     */
    get address() {
        return this.#address;
    }


    // PUBLIC METHODS
    /**
     * Get what this address leads to.
     *
     * The address is the only thing that can be trusted here, and it is read
     * again at every call rather than stored: what is computed is never kept
     * beside what it is computed from.
     *
     * @returns {string} One of the LinkKind values, never anything else.
     */
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
    /**
     * Tell whether an address carries any of the given marks.
     *
     * @param address {string} The address, in lower case.
     * @param marks {string[]} The marks to look for.
     * @returns {boolean} True if at least one mark is there.
     */
    static #containsOneOf(address, marks) {
        return marks.some(mark => address.includes(mark));
    }
}
