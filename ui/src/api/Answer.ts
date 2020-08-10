import { Query } from './Query';

/**
 * Representation of an Answer returned from the API.
 */
export interface Answer {
    query: Query;
    answer: string;
    score: number;
}
