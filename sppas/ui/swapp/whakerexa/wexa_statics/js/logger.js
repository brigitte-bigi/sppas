/**
 *  :filename: wexa_statics.js.logger.js
 *  :author: Brigitte Bigi
 *  :contact: contact@sppas.org
 *  :summary: A unified logging utility for all Whakerexa modules.
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

/**
 * Manage centralized logging for Whakerexa modules.
 *
 * This static class provides consistent, prefixed log messages across the
 * framework. It mimics Python's logging system with numeric levels from
 * 0 (silent) to 50 (critical). Only messages with a severity less than or
 * equal to the current `logLevel` are displayed.
 *
 * Levels:
 *  - 10 → Debug
 *  - 20 → Info
 *  - 30 → Warning
 *  - 40 → Error
 *  - 50 → Critical
 *
 * @example
 * WexaLogger.setLogLevel(20);
 * WexaLogger.info('Initialization complete.');
 * WexaLogger.error('Unhandled exception.', err);
 */
export class WexaLogger {

    /** @type {number} What is heard when a page says nothing. Info, as Python counts it. */
    static DEFAULT_LEVEL = 20;

    /** @type {Object} The names Python writes, and what they count for. */
    static #NAMES = {
        debug: 10,
        info: 20,
        warning: 30,
        error: 40,
        critical: 50
    };

    static #logLevel = WexaLogger.DEFAULT_LEVEL;

    // -----------------------------------------------------------------------

    /**
     * Say what a level written by a page counts for.
     *
     * A name as Python writes it, or a number between 0 and 50. Anything else
     * is not a level, and is answered with null so that what holds holds.
     *
     * @param {string|number} said - What the page wrote.
     * @returns {number|null} The level, or null when it is not one.
     */
    static levelOf(said) {
        if (typeof said === 'number') {
            return (said >= 0 && said <= 50) ? said : null;
        }

        if (typeof said !== 'string') {
            return null;
        }

        const written = said.trim().toLowerCase();
        if (written === '') {
            return null;
        }

        if (Object.prototype.hasOwnProperty.call(WexaLogger.#NAMES, written) === true) {
            return WexaLogger.#NAMES[written];
        }

        if (/^[0-9]+$/.test(written) === false) {
            return null;
        }

        const counted = Number(written);
        return counted <= 50 ? counted : null;
    }

    // -----------------------------------------------------------------------

    /**
     * Take the level a page left on the namespace, before anything is said.
     *
     * A page writes it before the framework is there -- Wexa.logLevel = 'debug'
     * -- so this is read when this file is read, which is before any other of
     * the framework. What is not a level is ignored, and the page holds.
     *
     * @returns {void}
     */
    static takeWhatThePageSaid() {
        const namespace = (typeof window !== 'undefined') ? window.Wexa : undefined;
        if (namespace === undefined || namespace === null) {
            return;
        }

        const level = WexaLogger.levelOf(namespace.logLevel);
        if (level !== null) {
            WexaLogger.#logLevel = level;
        }
    }

    /**
     * Get the current log level.
     *
     * @returns {number} The current log level (0–50).
     */
    static getLogLevel() {
        return this.#logLevel;
    }

    /**
     * Set the global log level, once the page is open.
     *
     * A name as Python writes it, or a number between 0 and 50 -- what a page
     * writes on the namespace is written the same way. What is neither is said
     * and changes nothing.
     *
     * @param {string|number} level - A name, or a value between 0 and 50.
     * @returns {void}
     */
    static setLogLevel(level) {
        const counted = WexaLogger.levelOf(level);
        if (counted === null) {
            console.warn('[WexaWarning] Invalid log level: ' + level
                + '. A name -- debug, info, warning, error, critical -- or a'
                + ' number between 0 and 50.');
            return;
        }
        WexaLogger.#logLevel = counted;
    }

    /**
     * Log a debug message if level <= 10.
     *
     * @param {string} msg - Message to display.
     * @returns {void}
     */
    static debug(msg) {
        if (this.#logLevel <= 10) console.info(`[WexaDebug] ${msg}`);
    }

    /**
     * Log an informational message if level <= 20.
     *
     * @param {string} msg - Message to display.
     * @returns {void}
     */
    static info(msg) {
        if (this.#logLevel <= 20) console.info(`[WexaInfo] ${msg}`);
    }

    /**
     * Log a warning message if level <= 30.
     *
     * @param {string} msg - Message to display.
     * @returns {void}
     */
    static warn(msg) {
        if (this.#logLevel <= 30) console.warn(`[WexaWarning] ${msg}`);
    }

    /**
     * Log an error message if level <= 40.
     *
     * @param {string} msg - Message to display.
     * @param {Error|string} [err] - Optional associated error.
     * @returns {void}
     */
    static error(msg, err) {
        if (this.#logLevel <= 40) console.error(`[WexaError] ${msg}`, err || '');
    }

    /**
     * Log a critical message whatever the level.
     *
     * @param {string} msg - Message to display.
     * @param {Error|string} [err] - Optional associated error.
     * @returns {void}
     */
    static critical(msg, err) {
        console.error(`[WexaCritical] ${msg}`, err || '');
    }
}

// What the page said before the framework was there. This file is the first of
// the framework to be read, so nothing of it has spoken yet.
WexaLogger.takeWhatThePageSaid();
