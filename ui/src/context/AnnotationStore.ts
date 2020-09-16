import { createContext } from 'react';
import { Bounds } from "./PDFStore";
import { Label } from "../api";

export class TokenId {
    constructor(
        public readonly pageIndex: number,
        public readonly tokenIndex: number ) {}
    toString() {
        return [this.pageIndex.toString(), this.tokenIndex.toString()].join('-'); }
 }


export class TokenSpanAnnotation {
    constructor(
        public readonly tokens: TokenId[],
        public bounds: Bounds,
        public readonly page: number,
        public readonly label: Label,
        public linkedAnnotation: TokenSpanAnnotation | undefined = undefined
    ) {}

    link(a: TokenSpanAnnotation): void {
        if (a.label !== this.label) {
            throw new Error("Cannot link annotations with different labels.")
        }
        this.linkedAnnotation = a
    }

    toString() {
        return this.tokens.map(t => t.toString()).join('-');
    }
};


export type PageAnnotations = TokenSpanAnnotation[][]

interface _AnnotationStore {
    labels: Label[]
    activeLabel?: Label
    setActiveLabel: (label: Label) => void;
    pageAnnotations: PageAnnotations;
    selectedTokenSpanAnnotation?: TokenSpanAnnotation;
    setSelectedTokenSpanAnnotation: (t?: TokenSpanAnnotation) => void;
    setPageAnnotations: (t: PageAnnotations) => void;
    freeFormAnnotations: boolean;
    toggleFreeFormAnnotations: (state: boolean) => void;
}

export const AnnotationStore = createContext<_AnnotationStore>({
    pageAnnotations: [],
    labels: [],
    activeLabel: undefined,
    setActiveLabel:(_?: Label) => {
        throw new Error("Unimplemented")
    },
    setSelectedTokenSpanAnnotation: (_?: TokenSpanAnnotation) => {
        throw new Error('Unimplemented');
    },
    setPageAnnotations: (_: PageAnnotations) => {
        throw new Error('Unimplemented');
    },
    freeFormAnnotations: false,
    toggleFreeFormAnnotations: (_: boolean) => {
        throw new Error('Unimplemented');
    },
});
