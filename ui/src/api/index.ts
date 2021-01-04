import axios from 'axios';
import { Annotation, RelationGroup, PdfAnnotations } from '../context';

export interface Token {
    x: number;
    y: number;
    height: number;
    width: number;
    text: string;
    style_name: string;
}

interface Page {
    index: number;
    width: number;
    height: number;
}

export interface PageTokens {
    page: Page;
    tokens: Token[];
}

function docURL(sha: string): string {
    return `/api/doc/${sha}`;
}

export function pdfURL(sha: string): string {
    return `${docURL(sha)}/pdf`;
}

export async function getTokens(sha: string): Promise<PageTokens[]> {
    return axios.get(`${docURL(sha)}/tokens`)
                .then(r => r.data);
}

export interface Label {
    text: string,
    color: string
}

export async function getLabels(): Promise<Label[]> {
    return axios.get("/api/annotation/labels")
                .then(r => r.data)
}

export async function getRelations(): Promise<Label[]> {
    return axios.get("/api/annotation/relations")
                .then(r => r.data)
}


export interface PaperStatus {
    sha: string,
    name: string,
    annotations: number,
    relations: number,
    finished: boolean,
    junk: boolean,
    comments: string,
    completedAt?: Date
}

export async function setPdfComment(sha: string, comments: string) {
    return axios.post(`/api/doc/${sha}/comments`, comments)
}

export async function setPdfFinished(sha: string, finished: boolean) {
    return axios.post(`/api/doc/${sha}/finished`, finished)
}

export async function setPdfJunk(sha: string, junk: boolean) {
    return axios.post(`/api/doc/${sha}/junk`, junk)
}

export async function getAllocatedPaperStatus(): Promise<PaperStatus[]> {
    return axios.get("/api/annotation/allocation/info")
                .then(r => r.data)
}

export function saveAnnotations(
    sha: string,
    pdfAnnotations: PdfAnnotations
): Promise<any> {
    return axios.post(
        `/api/doc/${sha}/annotations`,
        {
            annotations: pdfAnnotations.annotations,
            relations: pdfAnnotations.relations
        }
    )
}

export async function getAnnotations(sha: string): Promise<PdfAnnotations> {
    return axios.get(`/api/doc/${sha}/annotations`)
                .then(response => {
                    const ann: PdfAnnotations = response.data
                    const annotations = ann.annotations.map(a => Annotation.fromObject(a))
                    const relations = ann.relations.map(r => RelationGroup.fromObject(r))

                    return  new PdfAnnotations(
                        annotations,
                        relations
                    )               
                }
            )
        }
