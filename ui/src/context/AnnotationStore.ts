import { createContext } from 'react';
import { Bounds } from "./PDFStore";

export interface TokenId {
    pageIndex: number;
    tokenIndex: number;
}

export class TokenSpanAnnotation {
    constructor(
        public readonly tokens: TokenId[],
        public readonly bounds: Bounds[],
        public readonly pages: number[]
    ) {}

    mergeWith(a: TokenSpanAnnotation): TokenSpanAnnotation {
        return new TokenSpanAnnotation(
            this.tokens.concat(a.tokens),
            this.bounds.concat(a.bounds),
            this.pages.concat(a.pages)
        )
    }

};


interface _AnnotationStore {
    tokenSpanAnnotations: TokenSpanAnnotation[];
    selectedTokenSpanAnnotation?: TokenSpanAnnotation;
    setSelectedTokenSpanAnnotation: (t?: TokenSpanAnnotation) => void;
    setTokenSpanAnnotations: (t: TokenSpanAnnotation[]) => void;
}

export const AnnotationStore = createContext<_AnnotationStore>({
    tokenSpanAnnotations: [],
    setSelectedTokenSpanAnnotation: (_?: TokenSpanAnnotation) => {
        throw new Error('Unimplemented');
    },
    setTokenSpanAnnotations: (_: TokenSpanAnnotation[]) => {
        throw new Error('Unimplemented');
    }
});
