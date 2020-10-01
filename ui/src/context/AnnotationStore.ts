import { createContext } from 'react';
import { v4 as uuidv4 } from 'uuid';

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
    public readonly id: string

    constructor(
        public bounds: Bounds,
        public readonly page: number,
        public readonly label: Label,
        public readonly tokens: TokenId[] | null = null,
        public linkedAnnotation: Annotation | undefined = undefined,
        id: string | undefined = undefined
    ) {
        this.id = id ? id: uuidv4()
    }

    link(a: Annotation): void {
        if (a.label !== this.label) {
            throw new Error("Cannot link annotations with different labels.")
        }
        this.linkedAnnotation = a
    }

    toString() {
        return this.id
    }

    static fromObject(obj: Annotation) {
        return new Annotation(obj.bounds, obj.page, obj.label, obj.tokens, obj.linkedAnnotation)
    }
};



export type PdfAnnotations = Annotation[][]

interface _AnnotationStore {
    labels: Label[]
    activeLabel?: Label
    setActiveLabel: (label: Label) => void;

    relations: Label[]
    activeRelation?: Label
    setActiveRelation: (label: Label) => void;

    pdfAnnotations: PdfAnnotations;
    selectedAnnotations: Annotation[]
    setSelectedAnnotations: (t: Annotation[]) => void;
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
    relations: [],
    activeRelation: undefined,
    setActiveRelation:(_?: Label) => {
        throw new Error("Unimplemented")
    },
    selectedAnnotations: [],
    setSelectedAnnotations: (_?: Annotation[]) => {
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
