import { createContext } from 'react';
import { PDFPageProxy, PDFDocumentProxy } from 'pdfjs-dist/types/display/api';

import { Token, Label } from '../api';
import { TokenId, Annotation } from './AnnotationStore';

export type Optional<T> = T | undefined;

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
        bottom: bounds.bottom * scale,
    };
}

/**
 * Computes a bound which contains all of the bounds passed as arguments.
 */
function spanningBound(bounds: Bounds[], padding: number = 3): Bounds {
    // Start with a bounding box for which any bound would be
    // contained within, meaning we immediately update maxBound.
    const maxBound: Bounds = {
        left: Number.MAX_VALUE,
        top: Number.MAX_VALUE,
        right: 0,
        bottom: 0,
    };

    bounds.forEach((bound) => {
        maxBound.bottom = Math.max(bound.bottom, maxBound.bottom);
        maxBound.top = Math.min(bound.top, maxBound.top);
        maxBound.left = Math.min(bound.left, maxBound.left);
        maxBound.right = Math.max(bound.right, maxBound.right);
    });

    maxBound.top = maxBound.top - padding;
    maxBound.left = maxBound.left - padding;
    maxBound.right = maxBound.right + padding;
    maxBound.bottom = maxBound.bottom + padding;

    return maxBound;
}

/**
 * Returns the provided bounds in their normalized form. Normalized means that the left
 * coordinate is always less than the right coordinate, and that the top coordinate is always
 * left than the bottom coordinate.
 *
 * This is required because objects in the DOM are positioned and sized by setting their top-left
 * corner, width and height. This means that when a user composes a selection and moves to the left,
 * or up, from where they started might result in a negative width and/or height. We don't normalize
 * these values as we're tracking the mouse as it'd result in the wrong visual effect. Instead we
 * rotate the bounds we render on the appropriate axis. This means we need to account for this
 * later when calculating what tokens the bounds intersect with.
 */
export function normalizeBounds(b: Bounds): Bounds {
    const normalized = Object.assign({}, b);
    if (b.right < b.left) {
        const l = b.left;
        normalized.left = b.right;
        normalized.right = l;
    }
    if (b.bottom < b.top) {
        const t = b.top;
        normalized.top = b.bottom;
        normalized.bottom = t;
    }
    return normalized;
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

export function getNewAnnotation(
    page: PDFPageInfo,
    selection: Bounds,
    activeLabel: Label,
    freeform: boolean
): Optional<Annotation> {
    let annotation: Optional<Annotation>;

    const normalized = normalizeBounds(selection);
    if (freeform) {
        annotation = page.getFreeFormAnnotationForBounds(normalized, activeLabel);
    } else {
        annotation = page.getAnnotationForBounds(normalized, activeLabel);
    }
    return annotation;
}

export class PDFPageInfo {
    constructor(
        public readonly page: PDFPageProxy,
        public readonly tokens: Token[] = [],
        public bounds?: Bounds
    ) {}

    getFreeFormAnnotationForBounds(selection: Bounds, label: Label): Annotation {
        if (this.bounds === undefined) {
            throw new Error('Unknown Page Bounds');
        }

        // Here we invert the scale, because the user has drawn this bounding
        // box, so it is *already* scaled with respect to the client's view. For
        // the annotation, we want to remove this, because storing it with respect
        // to the PDF page's original scale means we can render it everywhere.
        const bounds = scaled(selection, 1 / this.scale);

        return new Annotation(bounds, this.page.pageNumber - 1, label);
    }

    getAnnotationForBounds(selection: Bounds, label: Label): Optional<Annotation> {
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
           the bounding box drawn by the user (selection).

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
        for (let i = 0; i < this.tokens.length; i++) {
            const tokenBound = this.getTokenBounds(this.tokens[i]);
            if (doOverlap(scaled(tokenBound, this.scale), selection)) {
                ids.push({ pageIndex: this.page.pageNumber - 1, tokenIndex: i });
                tokenBounds.push(tokenBound);
            }
        }
        if (ids.length === 0) {
            return undefined;
        }
        const bounds = spanningBound(tokenBounds);
        return new Annotation(bounds, this.page.pageNumber - 1, label, ids);
    }

    getScaledTokenBounds(t: Token): Bounds {
        return this.getScaledBounds(this.getTokenBounds(t));
    }

    getTokenBounds(t: Token): Bounds {
        const b = {
            left: t.x,
            top: t.y,
            right: t.x + t.width,
            bottom: t.y + t.height,
        };
        return b;
    }

    getScaledBounds(b: Bounds): Bounds {
        return scaled(b, this.scale);
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
    doc?: PDFDocumentProxy;
    onError: (err: Error) => void;
}

export const PDFStore = createContext<_PDFStore>({
    onError: (_: Error) => {
        throw new Error('Unimplemented');
    },
});
