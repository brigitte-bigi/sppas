/**
 * :filename: tests.js.loggerTest.js
 * :author: Brigitte Bigi
 * :contact: contact@sppas.org
 * :summary: Test file of the WexaLogger class.
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
 */

'use strict';

let logger_tests = new UnitTest();


// -----------------------------------------------------------------------
// D2: a name or a number, as Python writes them.
// -----------------------------------------------------------------------

logger_tests.add_test(() => {
    UnitTest.assert_values_equals(10, WexaLogger.levelOf('debug'), "level_of_debug_test");
    UnitTest.assert_values_equals(20, WexaLogger.levelOf('info'), "level_of_info_test");
    UnitTest.assert_values_equals(30, WexaLogger.levelOf('warning'), "level_of_warning_test");
    UnitTest.assert_values_equals(40, WexaLogger.levelOf('error'), "level_of_error_test");
    UnitTest.assert_values_equals(50, WexaLogger.levelOf('critical'), "level_of_critical_test");
});

logger_tests.add_test(() => {
    UnitTest.assert_values_equals(10, WexaLogger.levelOf('DEBUG'), "level_of_upper_name_test");
    UnitTest.assert_values_equals(30, WexaLogger.levelOf(' warning '), "level_of_spaced_name_test");
});

logger_tests.add_test(() => {
    UnitTest.assert_values_equals(10, WexaLogger.levelOf(10), "level_of_number_test");
    UnitTest.assert_values_equals(35, WexaLogger.levelOf('35'), "level_of_number_said_test");
    UnitTest.assert_values_equals(0, WexaLogger.levelOf(0), "level_of_zero_test");
});


// -----------------------------------------------------------------------
// C3, L31: what is understood by neither changes nothing.
// -----------------------------------------------------------------------

logger_tests.add_test(() => {
    UnitTest.assert_values_equals(null, WexaLogger.levelOf('loud'), "level_of_unknown_name_test");
    UnitTest.assert_values_equals(null, WexaLogger.levelOf(''), "level_of_nothing_test");
    UnitTest.assert_values_equals(null, WexaLogger.levelOf(null), "level_of_null_test");
    UnitTest.assert_values_equals(null, WexaLogger.levelOf(undefined), "level_of_undefined_test");
    UnitTest.assert_values_equals(null, WexaLogger.levelOf(-1), "level_of_below_test");
    UnitTest.assert_values_equals(null, WexaLogger.levelOf(51), "level_of_above_test");
});

logger_tests.add_test(() => {
    const held = WexaLogger.getLogLevel();

    WexaLogger.setLogLevel('loud');
    UnitTest.assert_values_equals(held, WexaLogger.getLogLevel(), "set_unknown_holds_test");

    WexaLogger.setLogLevel('debug');
    UnitTest.assert_values_equals(10, WexaLogger.getLogLevel(), "set_by_name_test");

    WexaLogger.setLogLevel(20);
    UnitTest.assert_values_equals(20, WexaLogger.getLogLevel(), "set_by_number_test");
});


// -----------------------------------------------------------------------
// D3: nothing said, the level is 20.
// -----------------------------------------------------------------------

logger_tests.add_test(() => {
    UnitTest.assert_values_equals(20, WexaLogger.DEFAULT_LEVEL, "default_level_test");
});


logger_tests.launch_unit_test();
