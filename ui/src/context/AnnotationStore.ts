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


export class RelationGroup {

    constructor(
        public source: string[],
        public target: string[],
        public label: Label
    ){}

    updateForAnnotationDeletion(a: Annotation): RelationGroup | undefined {
        const sourceEmpty = this.source.length === 0 
        const targetEmpty = this.target.length === 0

        this.source = this.source.filter((id) => id !== a.id)
        this.target = this.target.filter((id) => id !== a.id)

        const nowSourceEmpty = this.source.length === 0 
        const nowTargetEmpty = this.target.length === 0 

        // Only target had any annotations, now it has none,
        // so delete.
        if (sourceEmpty && nowTargetEmpty) {
            return undefined
        }
        // Only source had any annotations, now it has none,
        // so delete.
        if (targetEmpty && nowSourceEmpty) {
            return undefined
        }
        // Source was not empty, but now it is, so delete.
        if (!sourceEmpty && nowSourceEmpty) {
            return undefined
        }
        // Target was not empty, but now it is, so delete.
        if (!targetEmpty && nowTargetEmpty) {
            return undefined
        }

        return new RelationGroup(this.source, this.target, this.label)
    }

    static fromObject(obj: RelationGroup) {
        return new RelationGroup(obj.source, obj.target, obj.label)
    }
}


export class Annotation {
    public readonly id: string

    constructor(
        public bounds: Bounds,
        public readonly page: number,
        public readonly label: Label,
        public readonly tokens: TokenId[] | null = null,
        id: string | undefined = undefined
    ) {
        this.id = id ? id: uuidv4()
    }

    toString() {
        return this.id
    }

    static fromObject(obj: Annotation) {
        return new Annotation(obj.bounds, obj.page, obj.label, obj.tokens, obj.id)
    }
};



export type PdfAnnotations = Annotation[][]

interface _AnnotationStore {
    labels: Label[]
    activeLabel?: Label
    setActiveLabel: (label: Label) => void;

    relationLabels: Label[]
    activeRelationLabel?: Label
    setActiveRelationLabel: (label: Label) => void;

    pdfRelations: RelationGroup[],
    setPdfRelations: (t: RelationGroup[]) => void,

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
    relationLabels: [],
    activeRelationLabel: undefined,
    setActiveRelationLabel:(_?: Label) => {
        throw new Error("Unimplemented")
    },
    pdfRelations: [],
    setPdfRelations: (_?: RelationGroup[]) => {
        throw new Error('Unimplemented');
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
