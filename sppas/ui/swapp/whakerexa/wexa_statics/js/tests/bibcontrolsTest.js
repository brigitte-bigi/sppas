/**
:filename: tests.js.bibcontrolsTest.js
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Test file of the BibliographyControls class.

.. _This file is part of Whakerexa: https://github.com/brigitte-bigi/Whakerexa ,
.. on 2026-07-28.
    -------------------------------------------------------------------------

    Copyright (C) 2026 Brigitte Bigi
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

// instantiate unit tests class
let bibliography_controls_tests = new UnitTest();


/**
 * The BibTeX data every test of this file works on.
 *
 * Three references, whose years and authors are all different, and one of them
 * with an accent in the name of its author.
 */
const CONTROLS_DATA = String.raw`
@article{controls2022,
    author = {Brigitte Bigi},
    title = {A Large Open Corpus},
    journal = {A Journal},
    year = {2022}
}

@article{controls2019,
    author = {Carine André},
    title = {Another Title},
    journal = {A Journal},
    year = {2019}
}

@article{controls2026,
    author = {Alain Ghio},
    title = {A Third Title},
    journal = {A Journal},
    year = {2026}
}`;


/**
 * Build a bibliography, put it in the page, and give its controls.
 *
 * The table has to be in the document before the controls are built: the
 * search field and what is said are written before it.
 *
 * @param {string} name - What tells the elements of this test from the others.
 * @returns {Object} The table, its controls, and what removes them.
 */
function write_bibliography(name) {
    const references = new BibtexParser().parse(CONTROLS_DATA);
    const table = new BibliographyTable().build(references, new Map());
    table.id = name + '-table';

    const holder = document.createElement('div');
    holder.id = name + '-holder';
    holder.appendChild(table);
    document.body.appendChild(holder);

    return {table: table, controls: new BibliographyControls(table), remove: () => holder.remove()};
}

/**
 * Give the keys of the rows that are still displayed, in the order they are.
 *
 * @param {HTMLTableElement} table - The table of the bibliography.
 * @returns {string[]} The identifiers of the visible rows.
 */
function shown_rows(table) {
    const rows = Array.from(table.querySelectorAll('tbody tr.bib-row'));

    return rows.filter(row => row.hidden === false).map(row => row.id);
}


// -----------------------------------------------------------------------
// A field to search from, and a place for what is said, are written
// before the table. Requirements B19 and B20.
// -----------------------------------------------------------------------

bibliography_controls_tests.add_test(() => {
    const written = write_bibliography('written');

    UnitTest.assert_values_not_equals(null, document.querySelector('#written-holder .bib-search-field'),
        "controls_search_field_test");
    UnitTest.assert_values_not_equals(null, document.querySelector('#written-holder .bib-announcement'),
        "controls_announcement_test");
    UnitTest.assert_values_equals('polite',
        document.querySelector('#written-holder .bib-announcement').getAttribute('aria-live'),
        "controls_announcement_is_read_test");

    written.remove();
});

// -----------------------------------------------------------------------
// A search keeps the references the word appears in. Requirement B19.
// -----------------------------------------------------------------------

bibliography_controls_tests.add_test(() => {
    const written = write_bibliography('search');

    written.controls.filter('Ghio');

    UnitTest.assert_values_equals(1, shown_rows(written.table).length, "controls_filter_test");
    UnitTest.assert_array_contains('bib-controls2026', shown_rows(written.table),
        "controls_filter_keeps_the_right_one_test");

    written.remove();
});

// -----------------------------------------------------------------------
// A word that is nowhere leaves nothing, and an empty word brings
// everything back.
// -----------------------------------------------------------------------

bibliography_controls_tests.add_test(() => {
    const written = write_bibliography('empty');

    written.controls.filter('nothing-like-a-word');
    UnitTest.assert_values_equals(0, shown_rows(written.table).length, "controls_filter_nothing_test");

    written.controls.filter('');
    UnitTest.assert_values_equals(3, shown_rows(written.table).length, "controls_filter_all_test");

    written.remove();
});

// -----------------------------------------------------------------------
// Neither the case nor the accents matter: someone looking for "Andre"
// is looking for "André".
// -----------------------------------------------------------------------

bibliography_controls_tests.add_test(() => {
    const written = write_bibliography('accents');

    written.controls.filter('andre');

    UnitTest.assert_values_equals(1, shown_rows(written.table).length, "controls_filter_accents_test");

    written.remove();
});

// -----------------------------------------------------------------------
// What changed is said, and not only shown. Requirement B20.
// -----------------------------------------------------------------------

bibliography_controls_tests.add_test(() => {
    const written = write_bibliography('said');

    written.controls.filter('Ghio');
    const one = written.controls.announcement.textContent;

    written.controls.filter('');
    const all = written.controls.announcement.textContent;

    UnitTest.assert_values_not_equals(0, one.length, "controls_search_is_said_test");
    UnitTest.assert_values_not_equals(one, all, "controls_search_says_how_many_test");

    written.remove();
});

// -----------------------------------------------------------------------
// Sorting on the year puts the rows in the order of the years. B16.
// -----------------------------------------------------------------------

bibliography_controls_tests.add_test(() => {
    const written = write_bibliography('years');

    written.controls.sortBy('year', true);

    UnitTest.assert_values_equals('bib-controls2019', shown_rows(written.table)[0],
        "controls_sort_year_ascending_test");

    written.controls.sortBy('year', false);

    UnitTest.assert_values_equals('bib-controls2026', shown_rows(written.table)[0],
        "controls_sort_year_descending_test");

    written.remove();
});

// -----------------------------------------------------------------------
// Sorting on the author sorts on the family name, which the cell carries
// apart from what it displays. Requirement B16.
// -----------------------------------------------------------------------

bibliography_controls_tests.add_test(() => {
    const written = write_bibliography('authors');

    written.controls.sortBy('author', true);
    const order = shown_rows(written.table);

    // André, Bigi, Ghio. Sorting on what is displayed would give Alain,
    // Brigitte, Carine, and put André last of all for its accent.
    UnitTest.assert_values_equals('bib-controls2019', order[0], "controls_sort_author_first_test");
    UnitTest.assert_values_equals('bib-controls2022', order[1], "controls_sort_author_second_test");
    UnitTest.assert_values_equals('bib-controls2026', order[2], "controls_sort_author_third_test");

    written.remove();
});

// -----------------------------------------------------------------------
// How the bibliography is sorted is said too. Requirement B20.
// -----------------------------------------------------------------------

bibliography_controls_tests.add_test(() => {
    const written = write_bibliography('sort-said');

    written.controls.sortBy('year', true);

    UnitTest.assert_values_not_equals(0, written.controls.announcement.textContent.length,
        "controls_sort_is_said_test");

    written.remove();
});

// -----------------------------------------------------------------------
// Typing in the field searches, without anything else being called.
// -----------------------------------------------------------------------

bibliography_controls_tests.add_test(() => {
    const written = write_bibliography('typing');

    written.controls.field.value = 'Ghio';
    written.controls.field.dispatchEvent(new Event('input'));

    UnitTest.assert_values_equals(1, shown_rows(written.table).length, "controls_typing_test");

    written.remove();
});

// -----------------------------------------------------------------------
// A search hides rows; sorting then leaves them hidden, because nobody
// asked for them to come back.
// -----------------------------------------------------------------------

bibliography_controls_tests.add_test(() => {
    const written = write_bibliography('both');

    written.controls.filter('Ghio');
    written.controls.sortBy('year', true);

    UnitTest.assert_values_equals(1, shown_rows(written.table).length, "controls_filter_survives_sort_test");

    written.remove();
});


// -----------------------------------------------------------------------
// A column whose header says it opens hidden is listed in the selector,
// unchecked, and its cells are not displayed. B27.
// -----------------------------------------------------------------------

bibliography_controls_tests.add_test(() => {
    const written = write_bibliography('hidden');

    const box = document.querySelector('#hidden-table-column-type');
    UnitTest.assert_values_not_equals(null, box, "controls_hidden_column_listed_test");
    UnitTest.assert_values_equals(false, box.checked, "controls_hidden_column_unchecked_test");

    const cell = written.table.querySelector('td.bib-type');
    UnitTest.assert_values_equals(true, cell.classList.contains('hidden'),
        "controls_hidden_column_cell_test");

    written.remove();
});

// launch all unit tests added
bibliography_controls_tests.launch_unit_test();
