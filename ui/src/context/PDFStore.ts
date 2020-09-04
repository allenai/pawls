import { createContext } from 'react';
import pdfjs from 'pdfjs-dist';

import { Token } from '../api';

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
        public scale: number = 1,
        public readonly tokens: Token[] = []
    ) {}
    getIntersectingTokenIndices(selection: Bounds): number[] {
        const indices = [];
        for(let i = 0; i < this.tokens.length; i++) {
            if (doOverlap(this.getScaledTokenBounds(this.tokens[i]), selection)) {
                indices.push(i);
            }
        }
        return indices;
    }
    getIntersectingTokens(selection: Bounds): Token[] {
        const indices = this.getIntersectingTokenIndices(selection);
        return indices.map(i => this.tokens[i]);
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
}

interface _PDFStore {
    pages?: PDFPageInfo[];
    doc?: pdfjs.PDFDocumentProxy;
    setError: (err: Error) => void;
    setPageScale: (pageIndex: number, scale: number) => void;
}

export const PDFStore = createContext<_PDFStore>({
    // @ts-ignore: Ignore unread arguments.
    setPageScale: (i: number, s:number) => {
        throw new Error('Unimplemented');
    },
    setError: (_: Error) => {
        throw new Error('Unimplemented');
    }
});

