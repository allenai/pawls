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

    remove(a: Annotation) {
        const sourceEmpty = this.source.length === 0 
        const targetEmpty = this.target.length === 0 
        this.source = this.source.filter((id) => id !== a.id)
        this.target = this.target.filter((id) => id !== a.id)
        const nowSourceEmpty = this.source.length === 0 
        const nowTargetEmpty = this.target.length === 0 
        // TODO(Mark): Finish logic here for if the relation group
        // should be deleted. Probably delete if target is empty
        // , source is empty but target is not, etc.
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
