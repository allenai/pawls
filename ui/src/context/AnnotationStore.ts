import { createContext } from 'react';
import { Bounds } from "./PDFStore";
import { Token } from "../api";

export interface TokenWithId extends Token {
    pageIndex: number;
    tokenIndex: number;
}

export interface TokenSpanAnnotation {
    tokens: TokenWithId[]
    bounds: Bounds[]
    pages: number[]
};


export function largest(a: number, b: number): number {
    return a >= b ? a : b
}

export function smallest(a: number, b: number): number {
    return a <= b ? a : b
}

export function merge(a: TokenSpanAnnotation, b: TokenSpanAnnotation): TokenSpanAnnotation {

    const newTokens = a.tokens.concat(b.tokens)
    return {
        tokens: newTokens,
        bounds: a.bounds.concat(b.bounds),
        pages: a.pages.concat(b.pages)
    }
}


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
