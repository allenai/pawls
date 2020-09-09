import { createContext } from 'react';
import { Bounds } from "./PDFStore";
import { Token, TokensBySourceId } from "../api";

export interface TokenWithId extends Token {
    pageIndex: number;
    tokenIndex: number;
}

export interface TokenSpanAnnotation {
    tokens: TokenWithId[]
    bounds: Bounds
}


function largest(a: number, b: number): number {
    return a >= b ? a : b
}

function smallest(a: number, b: number): number {
    return a <= b ? a : b
}

export function merge(a: TokenSpanAnnotation, b: TokenSpanAnnotation): TokenSpanAnnotation {

    const newTokens = a.tokens.concat(b.tokens)
    const newBounds: Bounds = {
        top: smallest(a.bounds.top, b.bounds.top),
        bottom: largest(a.bounds.bottom, b.bounds.bottom),
        left: smallest(a.bounds.left, b.bounds.left), 
        right: largest(a.bounds.right, b.bounds.right)
    }

    return {
        tokens: newTokens,
        bounds: newBounds
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
