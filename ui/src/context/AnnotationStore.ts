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


export class Annotation {
    constructor(
        public bounds: Bounds,
        public readonly page: number,
        public readonly label: Label,
        public readonly tokens: TokenId[] | undefined = undefined,
        public linkedAnnotation: Annotation | undefined = undefined
    ) {}

    link(a: Annotation): void {
        if (a.label !== this.label) {
            throw new Error("Cannot link annotations with different labels.")
        }
        this.linkedAnnotation = a
    }

    toString() {
        return [
            this.bounds.top.toString(),
            this.bounds.bottom.toString(),
            this.bounds.left.toString(),
            this.bounds.right.toString(),
            this.label.text,
            this.tokens ? this.tokens.map(t => t.toString()).join('-') : null
        ].join("-")
    }
};



export type PdfAnnotations = Annotation[][]

interface _AnnotationStore {
    labels: Label[]
    activeLabel?: Label
    setActiveLabel: (label: Label) => void;
    pdfAnnotations: PdfAnnotations;
    selectedAnnotation?: Annotation;
    setSelectedAnnotation: (t?: Annotation) => void;
    setPdfAnnotations: (t: PdfAnnotations) => void;
    freeFormAnnotations: boolean;
    toggleFreeFormAnnotations: (state: boolean) => void;
}

export const AnnotationStore = createContext<_AnnotationStore>({
    pdfAnnotations: [],
    labels: [],
    activeLabel: undefined,
    setActiveLabel:(_?: Label) => {
        throw new Error("Unimplemented")
    },
    setSelectedAnnotation: (_?: Annotation) => {
        throw new Error('Unimplemented');
    },
    setPdfAnnotations: (_: PdfAnnotations) => {
        throw new Error('Unimplemented');
    },
    freeFormAnnotations: false,
    toggleFreeFormAnnotations: (_: boolean) => {
        throw new Error('Unimplemented');
    },
});
