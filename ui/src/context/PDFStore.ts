import { createContext } from 'react';
import pdfjs from 'pdfjs-dist';

import { Token } from '../api';
import { TokenId } from './AnnotationStore';

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
    getIntersectingTokenIds(selection: Bounds): TokenId[] {
        if (this.bounds === undefined) {
            throw new Error('Unknown Page Bounds');
        }
        const ids: TokenId[] = [];
        for(let i = 0; i < this.tokens.length; i++) {
            if (doOverlap(
                this.getScaledTokenBounds(this.tokens[i]),
                relativeTo(selection, this.bounds))
            ) {
                ids.push({ pageIndex: this.page.pageNumber - 1, tokenIndex: i });
            }
        }
        return ids;
    }
    getIntersectingTokens(selection: Bounds): Token[] {
        const ids = this.getIntersectingTokenIds(selection);
        return ids.map(id => this.tokens[id.tokenIndex]);
    }
    getScaledTokenBounds(t: Token): Bounds {
        const b = {
            left: t.x,
            top: t.y,
            right: t.x + t.width,
            bottom: t.y + t.height
        };
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
    doc?: pdfjs.PDFDocumentProxy;
    setError: (err: Error) => void;
}

export const PDFStore = createContext<_PDFStore>({
    setError: (_: Error) => {
        throw new Error('Unimplemented');
    }
});

