import { createContext } from 'react';
import { Bounds } from "./PDFStore";

export interface TokenId {
    pageIndex: number;
    tokenIndex: number;
}

export class TokenSpanAnnotation {
    constructor(
        public readonly tokens: TokenId[],
        public bounds: Bounds[],
        public readonly pages: number[],
        public readonly label: string
    ) {}

    mergeWith(a: TokenSpanAnnotation): TokenSpanAnnotation {
        if (a.label !== this.label) {
            throw new Error("Cannot merge annotations with different labels.")
        }
        return new TokenSpanAnnotation(
            this.tokens.concat(a.tokens),
            this.bounds.concat(a.bounds),
            this.pages.concat(a.pages),
            this.label
        )
    }
    annotationsForPage(page: number): TokenSpanAnnotation {
        // An annotation might cross a page boundary.
        // In that case, we will render it as two separate
        // annotations, one on each page, with bounding boxes
        // for each. This function allows us to filter
        // tokens and bounds to those on a single page.
        return new TokenSpanAnnotation(
            this.tokens.filter(t => t.pageIndex === page),
            this.bounds.filter((b, i) => this.pages[i] === page),
            this.pages.filter(p => p === page),
            this.label
        )

    }

};


interface _AnnotationStore {
    labels: string[]
    activeLabel: string
    setActiveLabel: (label: string) => void;
    tokenSpanAnnotations: TokenSpanAnnotation[];
    selectedTokenSpanAnnotation?: TokenSpanAnnotation;
    setSelectedTokenSpanAnnotation: (t?: TokenSpanAnnotation) => void;
    setTokenSpanAnnotations: (t: TokenSpanAnnotation[]) => void;
}

export const AnnotationStore = createContext<_AnnotationStore>({
    tokenSpanAnnotations: [],
    labels: [],
    activeLabel: "",
    setActiveLabel:(_?: string) => {
        throw new Error("Unimplemented")
    },
    setSelectedTokenSpanAnnotation: (_?: TokenSpanAnnotation) => {
        throw new Error('Unimplemented');
    },
    setTokenSpanAnnotations: (_: TokenSpanAnnotation[]) => {
        throw new Error('Unimplemented');
    }
});
