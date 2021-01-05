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
        public sourceIds: string[],
        public targetIds: string[],
        public label: Label
    ){}

    updateForAnnotationDeletion(a: Annotation): RelationGroup | undefined {
        const sourceEmpty = this.sourceIds.length === 0 
        const targetEmpty = this.targetIds.length === 0

        const newSourceIds = this.sourceIds.filter((id) => id !== a.id)
        const newTargetIds = this.targetIds.filter((id) => id !== a.id)

        const nowSourceEmpty = this.sourceIds.length === 0 
        const nowTargetEmpty = this.targetIds.length === 0 

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

        return new RelationGroup(newSourceIds, newTargetIds, this.label)
    }

    static fromObject(obj: RelationGroup) {
        return new RelationGroup(obj.sourceIds, obj.targetIds, obj.label)
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

export class PdfAnnotations {

    constructor(
        public readonly annotations: Annotation[],
        public readonly relations: RelationGroup[],
        public readonly unsavedChanges: boolean = false
    ) {
    }

    saved(): PdfAnnotations {
        return new PdfAnnotations(
            this.annotations,
            this.relations,
            false
        )
    }

    withNewAnnotation(a: Annotation): PdfAnnotations {

        return new PdfAnnotations(
            this.annotations.concat([a]),
            this.relations,
            true
        )
    }
    withNewRelation(r: RelationGroup): PdfAnnotations {

        return new PdfAnnotations(
            this.annotations,
            this.relations.concat([r]),
            true
        )
    }

    deleteAnnotation(a: Annotation): PdfAnnotations {

        const newAnnotations = this.annotations.filter((ann) => ann.id !== a.id)
        const newRelations = this.relations
            .map((r) => r.updateForAnnotationDeletion(a))
            .filter(r => r !== undefined)
        return new PdfAnnotations(
            newAnnotations,
            newRelations as RelationGroup[],
            true
        )
    }

    undoAnnotation(): PdfAnnotations {

        const popped = this.annotations.pop()
        if (!popped) {
            // No annotations, nothing to update
            return this
        }
        const newRelations = this.relations
            .map((r) => r.updateForAnnotationDeletion(popped))
            .filter(r => r !== undefined)

        return new PdfAnnotations(
            this.annotations,
            newRelations as RelationGroup[],
            true
        )
    }
}


interface _AnnotationStore {
    annotator?: string
    hasAllocation: boolean
    labels: Label[]
    activeLabel?: Label
    setActiveLabel: (label: Label) => void;

    relationLabels: Label[]
    activeRelationLabel?: Label
    setActiveRelationLabel: (label: Label) => void;

    pdfAnnotations: PdfAnnotations;
    setPdfAnnotations: (t: PdfAnnotations) => void;

    selectedAnnotations: Annotation[]
    setSelectedAnnotations: (t: Annotation[]) => void;

    freeFormAnnotations: boolean;
    toggleFreeFormAnnotations: (state: boolean) => void;

    hideLabels: boolean;
    setHideLabels: (state: boolean) => void;
}

export const AnnotationStore = createContext<_AnnotationStore>({
    annotator: undefined,
    hasAllocation: false,
    pdfAnnotations: new PdfAnnotations([],[]),
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
    hideLabels: false,
    setHideLabels: (_: boolean) => {
        throw new Error('Unimplemented');
    },
});
