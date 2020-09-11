import { createContext } from 'react';
import { Bounds } from "./PDFStore";

export class TokenId {
    constructor(
        public readonly pageIndex: number,
        public readonly tokenIndex: number ) {}
    toString() {
        return [this.pageIndex, this.tokenIndex].join('-'); }
 }


export class TokenSpanAnnotation {
    constructor(
        public readonly tokens: TokenId[],
        public bounds: Bounds[],
        public readonly pages: number[],
        public readonly label: string,
        private readonly perPage: {[page: number]: TokenSpanAnnotation} = {}
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

    // TODO(Mark): Change the caching in this function
    // when we allow users to modify annotations.
    annotationsForPage(page: number): TokenSpanAnnotation {
        // An annotation might cross a page boundary.
        // In that case, we will render it as two separate
        // annotations, one on each page, with bounding boxes
        // for each. This function allows us to filter
        // tokens and bounds to those on a single page.

        if (page in this.perPage) {
            return this.perPage[page]
        }
        else {
            const pageSpecific =  new TokenSpanAnnotation(
                this.tokens.filter(t => t.pageIndex === page),
                this.bounds.filter((b, i) => this.pages[i] === page),
                this.pages.filter(p => p === page),
                this.label
            )
            // Computing the annotations split out per page is moderately expensive,
            // so we want to do it once when it's first called, and then cache the
            // result in the perPage attribute.
            this.perPage[page] = pageSpecific
            return pageSpecific
        }
    }
    toString() {
        return this.tokens.map(t => t.toString()).join('-');
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
