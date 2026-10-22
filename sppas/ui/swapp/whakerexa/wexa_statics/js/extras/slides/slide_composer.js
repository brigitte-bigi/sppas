/**
 :filename: statics.js.slides.slide_composer.js
 :author: Brigitte Bigi
 :contact: contact@sppas.org
 :summary: Engender the slides a layout asks for, and lay the blocks down.

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
 * Engender the slides a layout asks for, and lay the blocks down.
 *
 * This is the only class that changes the document shown. It moves the blocks
 * that no longer belong to the first slide, and never copies them: what the
 * author wrote is laid out, not duplicated.
 *
 * A table that is split keeps its head on every slide, and a list that is split
 * stays a list: a row taken out of its table, or an item out of its list, would
 * lose what makes it readable.
 */
export class SlideComposer {

    // PUBLIC METHODS
    /**
     * Lay a slide out on as many slides as the layout asks for.
     *
     * @param slide {HTMLElement} The slide written by the author.
     * @param layout {SlideLayout} What was decided for its blocks.
     * @returns {HTMLElement[]} The slides, the written one first.
     */
    compose(slide, layout) {
        const parts = layout.parts;
        const slides = [slide];

        for (let rank = 1; rank < parts.length; rank++) {
            const next = this.#buildSlide(slide);

            this.#lay(next, parts[rank]);

            slides[slides.length - 1].after(next);
            slides.push(next);
        }

        return slides;
    }


    // PRIVATE METHODS
    /**
     * Build a slide that continues another one, empty of any content.
     *
     * @param source {HTMLElement} The slide it continues.
     * @returns {HTMLElement} A slide, with the same classes and no identifier.
     */
    #buildSlide(source) {
        const next = document.createElement(source.tagName);
        next.className = source.className;

        return next;
    }

    /**
     * Lay the blocks of a part in the slide that receives them.
     *
     * The blocks are moved, never copied, and those that were written in the
     * same table or the same list are laid down together, inside a table or a
     * list of their own.
     *
     * @param next {HTMLElement} The slide that receives them.
     * @param blocks {SlideBlock[]} The blocks of that part, in order.
     * @returns {void}
     */
    #lay(next, blocks) {
        let group = [];
        let parent = null;

        blocks.forEach(block => {
            const holder = block.element.parentElement;

            if (holder !== parent && group.length > 0) {
                this.#layGroup(next, parent, group);
                group = [];
            }

            parent = holder;
            group.push(block.element);
        });

        if (group.length > 0) {
            this.#layGroup(next, parent, group);
        }
    }

    /**
     * Lay a group of elements written in the same holder.
     *
     * @param next {HTMLElement} The slide that receives them.
     * @param parent {HTMLElement} What they were written in.
     * @param elements {HTMLElement[]} The elements to move, in order.
     * @returns {void}
     */
    #layGroup(next, parent, elements) {
        if (parent === null) {
            elements.forEach(element => next.appendChild(element));
            return;
        }

        if (parent.tagName === 'TBODY') {
            next.appendChild(this.#rebuildTable(parent, elements));
            return;
        }

        if (parent.tagName === 'UL' || parent.tagName === 'OL') {
            next.appendChild(this.#rebuildList(parent, elements));
            return;
        }

        elements.forEach(element => next.appendChild(element));
    }

    /**
     * Build the table that receives some rows, with the head of theirs.
     *
     * @param body {HTMLElement} The body the rows were written in.
     * @param rows {HTMLElement[]} The rows to move, in order.
     * @returns {HTMLTableElement} A table holding the head and those rows.
     */
    #rebuildTable(body, rows) {
        const source = body.closest('table');
        const table = source.cloneNode(false);
        const head = source.querySelector('thead');

        // An identifier names one element. The part says which table it
        // continues, and whoever acts on the columns reads that.
        table.removeAttribute('id');
        if (source.id.length > 0) {
            table.dataset.partOf = source.id;
        }

        if (head !== null) {
            table.appendChild(head.cloneNode(true));
        }

        // One part of a table is shown at a time: sorting a column would move
        // rows the reader does not see. The heads keep their text and lose
        // their buttons, in the table written and in the parts.
        SlideComposer.#unsortable(source);
        SlideComposer.#unsortable(table);

        const next = document.createElement('tbody');
        rows.forEach(row => next.appendChild(row));
        table.appendChild(next);

        return table;
    }

    /**
     * Take the sort buttons off the heads of a table, keeping their text.
     *
     * @param table {HTMLTableElement} A table laid out on several slides.
     * @returns {void}
     */
    static #unsortable(table) {
        table.querySelectorAll('thead button.sortatable').forEach(button => {
            button.replaceWith(document.createTextNode(button.textContent));
        });
    }

    /**
     * Build the list that receives some items.
     *
     * @param source {HTMLElement} The list the items were written in.
     * @param items {HTMLElement[]} The items to move, in order.
     * @returns {HTMLElement} A list of the same kind, holding those items.
     */
    #rebuildList(source, items) {
        const list = source.cloneNode(false);
        items.forEach(item => list.appendChild(item));

        return list;
    }

}
