import { createContext } from 'react';
import pdfjs from 'pdfjs-dist';

import { Token } from '../api';
import { TokenId, TokenSpanAnnotation } from './AnnotationStore';

export interface Bounds {
    left: number;
    top: number;
    right: number;
    bottom: number;
}

/**
 * Returns the provided bounds scaled by the provided factor.
 */
function scaled(bounds: Bounds, scale: number): Bounds {
    return {
        left: bounds.left * scale,
        top: bounds.top * scale,
        right: bounds.right * scale,
        bottom: bounds.bottom * scale
    };
}

/**
 * Returns the provided bounds adjusted to be relative to the top-left corner of the provided
 * bounds.
 */
function relativeTo(a: Bounds, b: Bounds): Bounds {
    return {
        left: a.left - b.left,
        top: a.top - b.top,
        right: a.right - b.left,
        bottom: a.bottom - b.top
    };
}

/**
 * Computes a bound which contains all of the bounds passed as arguments.
 */
function spanningBound(bounds: Bounds[], padding: number = 5): Bounds{

    // Start with a bounding box for which any bound would be
    // contained within, meaning we immediately update maxBound.
    const maxBound: Bounds = {
        left: Number.MAX_VALUE,
        top: Number.MAX_VALUE,
        right: 0,
        bottom: 0
    }

    bounds.forEach(bound => {
        maxBound.bottom = Math.max(bound.bottom, maxBound.bottom)
        maxBound.top = Math.min(bound.top, maxBound.top)
        maxBound.left = Math.min(bound.left, maxBound.left)
        maxBound.right = Math.max(bound.right, maxBound.right)
    })

    maxBound.top = maxBound.top - padding
    maxBound.left = maxBound.left - padding
    maxBound.right = maxBound.right + padding
    maxBound.bottom = maxBound.bottom + padding

    return maxBound

}


/**
 * Returns true if the provided bounds overlap.
 */
function doOverlap(a: Bounds, b: Bounds): boolean {
    if (a.left >= b.right || a.right <= b.left) {
        return false;
    } else if (a.bottom <= b.top || a.top >= b.bottom) {
        return false;
    }
    return true;
}

export class PDFPageInfo {
    constructor(
        public readonly page: pdfjs.PDFPageProxy,
        public readonly tokens: Token[] = [],
        public bounds?: Bounds
    ) {}
    getTokenSpanAnnotationForBounds(selection: Bounds): TokenSpanAnnotation {

        /* This function is quite complicated. Our objective here is to
           compute overlaps between a bounding box provided by a user and
           grobid token spans associated with a pdf. The complexity here is
           that grobid spans are relative to an absolute scale of the pdf,
           but our user's bounding box is relative to the pdf rendered in their
           client. 

           The critical key here is that anything we *store* must be relative
           to the underlying pdf. So for example, inside the for loop, we are
           computing: 
           
           whether a grobid token (tokenBound), scaled to the current scale of the
           pdf in the client (scaled(tokenBound, this.scale)), is overlapping with
           the bounding box drawn by the user (selection) relative to the edge of 
           the pdf in the client (relativeTo(selection, this.bounds)).

           But! Once we have computed this, we store the grobid tokens and the bound
           that contains all of them relative to the *original grobid tokens*.

           This means that the stored data is not tied to a particular scale, and we
           can re-scale it when we need to (mainly when the user resizes the browser window).
         */

        if (this.bounds === undefined) {
            throw new Error('Unknown Page Bounds');
        }
        const ids: TokenId[] = [];
        const tokenBounds: Bounds[] = [];
        for(let i = 0; i < this.tokens.length; i++) {
            const tokenBound = this.getTokenBounds(this.tokens[i])
            if (doOverlap(
                scaled(tokenBound, this.scale), 
                relativeTo(selection, this.bounds))
                ) {
                ids.push({
                    pageIndex: this.page.pageNumber - 1,
                    tokenIndex: i,
                    ...this.tokens[i]
                });
                tokenBounds.push(tokenBound);
            }
        }
        const bounds = spanningBound(tokenBounds)
        return new TokenSpanAnnotation(ids, [bounds], [this.page.pageNumber - 1])
    }

    getIntersectingTokens(selection: Bounds): Token[] {
        const annotation = this.getTokenSpanAnnotationForBounds(selection);
        return annotation.tokens.map(id => this.tokens[id.tokenIndex]);
    }

    getScaledTokenBounds(t: Token): Bounds {
        return this.getScaledBounds(this.getTokenBounds(t));
    }

    getTokenBounds(t: Token): Bounds {
        const b = {
            left: t.x,
            top: t.y,
            right: t.x + t.width,
            bottom: t.y + t.height
        };
        return b;
    }

    getScaledBounds(b: Bounds): Bounds {
        return scaled(b, this.scale)
    }

    get scale(): number {
        if (this.bounds === undefined) {
            throw new Error('Unknown Page Bounds');
        }
        const pdfPageWidth = this.page.view[2] - this.page.view[1];
        const domPageWidth = this.bounds.right - this.bounds.left;
        return domPageWidth / pdfPageWidth;
    }
}

interface _PDFStore {
    pages?: PDFPageInfo[];
    doc?: pdfjs.PDFDocumentProxy;
    onError: (err: Error) => void;
}

export const PDFStore = createContext<_PDFStore>({
    onError: (_: Error) => {
        throw new Error('Unimplemented');
    }
});

