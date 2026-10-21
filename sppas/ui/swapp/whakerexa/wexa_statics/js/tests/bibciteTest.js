/**
:filename: tests.js.bibciteTest.js
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Test file of the CitationIndex class.

.. _This file is part of Whakerexa: https://github.com/brigitte-bigi/Whakerexa ,
.. on 2026-07-30.
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
let citation_index_tests = new UnitTest();


/**
 * Write in the page a text citing the given keys, in that order.
 *
 * @param {string} name - What tells the elements of this test from the others.
 * @param {string[]} keys - The keys cited, in the order they appear.
 * @returns {Object} The text, its citations, and what removes it.
 */
function write_text(name, keys) {
    const root = document.createElement('div');
    root.id = name + '-text';

    keys.forEach(key => {
        const sentence = document.createElement('p');
        sentence.appendChild(document.createTextNode('This is said in '));

        const element = document.createElement('span');
        element.setAttribute('data-bibtex', key);
        element.textContent = key;
        sentence.appendChild(element);
        sentence.appendChild(document.createTextNode('.'));

        root.appendChild(sentence);
    });

    document.body.appendChild(root);

    return {
        root: root,
        elements: Array.from(root.querySelectorAll('[data-bibtex]')),
        remove: () => root.remove()
    };
}

/**
 * Give references bearing the given keys.
 *
 * @param {string[]} keys - The keys the references bear.
 * @returns {Map} The references, by key.
 */
function references_named(keys) {
    const entries = keys.map(key => '@misc{' + key + ', title = {A Title}}').join('\n\n');

    return new BibtexParser().parse(entries);
}


/**
 * Give the number a citation shows.
 *
 * A citation that names a reference writes its number twice: once in the
 * button that opens the reference, and once in the anchor that stays a link
 * on paper. What is read on screen is the button. A citation that names
 * nothing has neither, and says so by itself.
 *
 * @param {HTMLElement} element - The citation written in the text.
 * @returns {string} The number, brackets included.
 */
function number_shown(element) {
    const control = element.querySelector('.bib-citation-control');

    if (control === null) {
        return element.textContent;
    }

    return control.textContent;
}

// -----------------------------------------------------------------------
// Numbers follow the order the citations appear in the text, and there
// is a single sequence for the whole document. C13 and C14.
// -----------------------------------------------------------------------

citation_index_tests.add_test(() => {
    const written = write_text('order', ['one2026', 'two2026', 'three2026']);
    const index = new CitationIndex();

    index.index(written.root, references_named(['one2026', 'two2026', 'three2026']));

    UnitTest.assert_values_equals('[1]', number_shown(written.elements[0]), "index_first_number_test");
    UnitTest.assert_values_equals('[2]', number_shown(written.elements[1]), "index_second_number_test");
    UnitTest.assert_values_equals('[3]', number_shown(written.elements[2]), "index_third_number_test");

    written.remove();
});

// -----------------------------------------------------------------------
// A reference is numbered the first time it is cited, and every later
// citation of it carries that same number. C11 and C12.
// -----------------------------------------------------------------------

citation_index_tests.add_test(() => {
    const written = write_text('again', ['one2026', 'two2026', 'one2026', 'three2026']);
    const index = new CitationIndex();

    index.index(written.root, references_named(['one2026', 'two2026', 'three2026']));

    UnitTest.assert_values_equals('[1]', number_shown(written.elements[0]), "index_again_first_test");
    UnitTest.assert_values_equals('[2]', number_shown(written.elements[1]), "index_again_second_test");
    UnitTest.assert_values_equals('[1]', number_shown(written.elements[2]), "index_again_repeated_test");
    UnitTest.assert_values_equals('[3]', number_shown(written.elements[3]), "index_again_next_test");

    written.remove();
});

// -----------------------------------------------------------------------
// A key that names nothing stays visible, says so, and takes no number:
// the numbering goes on without a gap. Requirement C8.
// -----------------------------------------------------------------------

citation_index_tests.add_test(() => {
    const written = write_text('missing', ['one2026', 'nothing2026', 'two2026']);
    const index = new CitationIndex();

    index.index(written.root, references_named(['one2026', 'two2026']));

    UnitTest.assert_values_equals('[1]', number_shown(written.elements[0]), "index_missing_before_test");
    UnitTest.assert_values_equals('[?]', number_shown(written.elements[1]), "index_missing_test");
    UnitTest.assert_values_equals('[2]', number_shown(written.elements[2]), "index_missing_after_test");

    written.remove();
});

// -----------------------------------------------------------------------
// What the text owes to each reference: its number, and every place it
// is cited at. Requirements C26 and C27.
// -----------------------------------------------------------------------

citation_index_tests.add_test(() => {
    const written = write_text('owes', ['one2026', 'two2026', 'one2026']);
    const index = new CitationIndex();

    index.index(written.root, references_named(['one2026', 'two2026']));
    const cited = index.citedReferences();

    UnitTest.assert_values_equals(2, cited.size, "index_cited_count_test");
    UnitTest.assert_values_equals(1, cited.get('one2026').number, "index_cited_number_test");
    UnitTest.assert_values_equals(2, cited.get('one2026').places.length, "index_cited_places_test");
    UnitTest.assert_values_equals(written.elements[0], cited.get('one2026').places[0],
        "index_cited_first_place_test");
    UnitTest.assert_values_equals(written.elements[2], cited.get('one2026').places[1],
        "index_cited_second_place_test");

    written.remove();
});

// -----------------------------------------------------------------------
// A reference that is never cited owes nothing to the text, and is not
// there at all.
// -----------------------------------------------------------------------

citation_index_tests.add_test(() => {
    const written = write_text('uncited', ['one2026']);
    const index = new CitationIndex();

    index.index(written.root, references_named(['one2026', 'never2026']));
    const cited = index.citedReferences();

    UnitTest.assert_values_equals(1, cited.size, "index_uncited_count_test");
    UnitTest.assert_object_not_contains_key('never2026', Object.fromEntries(cited),
        "index_uncited_absent_test");

    written.remove();
});

// -----------------------------------------------------------------------
// A key that names nothing owes nothing either: no number was given.
// -----------------------------------------------------------------------

citation_index_tests.add_test(() => {
    const written = write_text('nothing', ['nothing2026']);
    const index = new CitationIndex();

    index.index(written.root, references_named(['one2026']));

    UnitTest.assert_values_equals(0, index.citedReferences().size, "index_nothing_cited_test");

    written.remove();
});

// -----------------------------------------------------------------------
// A text without any citation gives nothing, and the bibliography gets
// its table all the same. The two domains are independent.
// -----------------------------------------------------------------------

citation_index_tests.add_test(() => {
    const written = write_text('none', []);
    const index = new CitationIndex();

    index.index(written.root, references_named(['one2026']));

    UnitTest.assert_values_equals(0, index.citations.length, "index_no_citation_test");
    UnitTest.assert_values_equals(0, index.citedReferences().size, "index_no_cited_test");

    written.remove();
});

// -----------------------------------------------------------------------
// Reading the text again gives the same numbers. Requirement C30.
// -----------------------------------------------------------------------

citation_index_tests.add_test(() => {
    const written = write_text('twice', ['one2026', 'two2026', 'one2026']);
    const index = new CitationIndex();
    const references = references_named(['one2026', 'two2026']);

    index.index(written.root, references);
    const once = Object.fromEntries(index.citedReferences());

    index.index(written.root, references);
    const twice = Object.fromEntries(index.citedReferences());

    UnitTest.assert_values_equals(once['one2026'].number, twice['one2026'].number,
        "index_same_number_test");
    UnitTest.assert_values_equals(2, index.citedReferences().get('one2026').places.length,
        "index_places_not_doubled_test");

    written.remove();
});

// -----------------------------------------------------------------------
// The citations are kept in the order they appear, each carrying the key
// it bears. Requirement C7.
// -----------------------------------------------------------------------

citation_index_tests.add_test(() => {
    const written = write_text('kept', ['one2026', 'two2026']);
    const index = new CitationIndex();

    index.index(written.root, references_named(['one2026', 'two2026']));
    const citations = index.citations;

    UnitTest.assert_values_equals(2, citations.length, "index_citations_count_test");
    UnitTest.assert_values_equals(1, citations[0].place, "index_citation_place_test");
    UnitTest.assert_values_equals('one2026', citations[0].citedKeys[0].writtenKey,
        "index_citation_key_test");

    written.remove();
});

// -----------------------------------------------------------------------
// Without any text to read, nothing is raised: a document whose content
// cannot be found is still a document.
// -----------------------------------------------------------------------

citation_index_tests.add_test(() => {
    const index = new CitationIndex();
    let raised = '';

    try {
        index.index(null, references_named(['one2026']));
    } catch (error) {
        raised = error.name;
    }

    UnitTest.assert_values_equals('', raised, "index_no_text_does_not_raise_test");
    UnitTest.assert_values_equals(0, index.citedReferences().size, "index_no_text_cited_test");
});


// -----------------------------------------------------------------------
// The addresses that open under a citation open where those of the table
// open: one page, one answer. B28.
// -----------------------------------------------------------------------

citation_index_tests.add_test(() => {
    const written = write_text('target', ['addressed2026']);
    const carrying = new BibtexParser().parse(
        '@misc{addressed2026, title = {A Title}, url = {http://www.example.org/paper.pdf}}');

    new CitationIndex().index(written.root, carrying);

    const address = written.root.querySelector('a.bib-link.external-link');
    UnitTest.assert_values_equals('_blank', address.getAttribute('target'),
        "index_address_opens_a_tab_test");
    UnitTest.assert_values_equals('noopener', address.getAttribute('rel'),
        "index_address_holds_nothing_test");

    written.remove();
});

// -----------------------------------------------------------------------
// A page that asks to stay where it is is answered here too. B28.
// -----------------------------------------------------------------------

citation_index_tests.add_test(() => {
    const written = write_text('target-self', ['addressed2026']);
    const carrying = new BibtexParser().parse(
        '@misc{addressed2026, title = {A Title}, url = {http://www.example.org/paper.pdf}}');

    Link.setTarget('_self');
    new CitationIndex().index(written.root, carrying);
    Link.resetTarget();

    const address = written.root.querySelector('a.bib-link.external-link');
    UnitTest.assert_values_equals('_self', address.getAttribute('target'),
        "index_address_stays_test");
    UnitTest.assert_values_equals(null, address.getAttribute('rel'),
        "index_address_no_rel_test");

    written.remove();
});

// launch all unit tests added
citation_index_tests.launch_unit_test();
