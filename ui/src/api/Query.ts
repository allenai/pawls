import queryString from 'querystring';
import { Location } from 'history';

import { unwrap } from '../utils';

/**
 * Representation of a query, which consists of a question and two choices.
 */
export class Query {
    constructor(readonly question: string = '', readonly choices: [string, string] = ['', '']) {}
    /**
     * Returns whether the current query has a non-empty question and two
     * non-empty answers.
     *
     * @return {boolean}
     */
    isValid() {
        return (
            this.question.trim() !== '' &&
            this.choices.filter(choice => choice.trim() !== '').length === 2
        );
    }

    /**
     * In JavaScript (and TypeScript) object comparison is by reference. We
     * provide an equals value as to compare two instances, allowing us to
     * determine if they're logically equal
     *
     * @param {Query} query
     *
     * @returns {boolean} True if the two queries are logically equal (their
     * values are the same). False if not.
     */
    equals(query: Query): boolean {
        return (
            this.question === query.question &&
            this.choices[0] === query.choices[0] &&
            this.choices[1] === query.choices[1]
        );
    }

    /**
     * Serializes the query to a URL appropriate representation.
     *
     * @returns {string}
     */
    toQueryString(): string {
        return queryString.stringify({ q: this.question, c: this.choices });
    }

    /**
     * Factory that returns a Query instance based upon the provided URL.
     *
     * @param {Location} location
     *
     * @returns {Query}
     */
    public static fromQueryString(location: Location): Query {
        const locationSearchWithoutQuestionmark = location.search.replace(/^\?/, '');
        const qs = queryString.parse(locationSearchWithoutQuestionmark);
        const [first, second] = !Array.isArray(qs.c) ? [qs.c, ''] : qs.c;
        const choices: [string, string] = [first || '', second || ''];
        return new Query(unwrap(qs.q), choices);
    }
}
