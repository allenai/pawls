import axios from 'axios';
import { Annotation, RelationGroup, PdfAnnotations } from '../context';

export interface Token {
    x: number;
    y: number;
    height: number;
    width: number;
    text: string;
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
    return axios.get(`${docURL(sha)}/tokens`).then((r) => r.data);
}

export interface Label {
    text: string;
    color: string;
}

export async function getLabels(): Promise<Label[]> {
    return axios.get('/api/annotation/labels').then((r) => r.data);
}

export async function getRelations(): Promise<Label[]> {
    return axios.get('/api/annotation/relations').then((r) => r.data);
}

export interface PaperStatus {
    sha: string;
    name: string;
    annotations: number;
    relations: number;
    finished: boolean;
    junk: boolean;
    comments: string;
    completedAt?: Date;
}

export interface Allocation {
    papers: PaperStatus[];
    hasAllocatedPapers: boolean;
}

export async function setPdfComment(sha: string, comments: string) {
    return axios.post(`/api/doc/${sha}/comments`, comments);
}

export async function getPdfFinished(sha: string): Promise<boolean> {
    return axios.get(`/api/doc/${sha}/finished`).then((response) => {
        return Boolean(response.data);
    });
}

export async function getPdfJunk(sha: string): Promise<boolean> {
    return axios.get(`/api/doc/${sha}/junk`).then((response) => {
        return Boolean(response.data);
    });
}

export async function setPdfFinished(sha: string, finished: boolean) {
    // Have to cast `finished` to boolean otherwise when `finished`
    // is false, it results in an empty body for this POST request
    return axios.post(`/api/doc/${sha}/finished`, String(finished));
}

export async function setPdfJunk(sha: string, junk: boolean) {
    // Have to cast `junk` to boolean otherwise when `junk`
    // is false, it results in an empty body for this POST request
    return axios.post(`/api/doc/${sha}/junk`, String(junk));
}

export async function getAllocatedPaperStatus(): Promise<Allocation> {
    return axios.get('/api/annotation/allocation/info').then((r) => r.data);
}

export async function isAuthorized(): Promise<boolean> {
    return axios
        .get('/api/user')
        .then((r) => r.status === 200)
        .catch(() => false);
}

export interface UserInfo {
    user: string;
    email: string;
}

export async function getUsername(): Promise<UserInfo> {
    return axios.get('/api/user').then((response) => {
        const user: UserInfo = response.data;
        return user;
    });
}

export function saveAnnotations(sha: string, pdfAnnotations: PdfAnnotations): Promise<any> {
    return axios.post(`/api/doc/${sha}/annotations`, {
        annotations: pdfAnnotations.annotations,
        relations: pdfAnnotations.relations,
    });
}

export async function getAnnotations(sha: string): Promise<PdfAnnotations> {
    return axios.get(`/api/doc/${sha}/annotations`).then((response) => {
        const ann: PdfAnnotations = response.data;
        const annotations = ann.annotations.map((a) => Annotation.fromObject(a));
        const relations = ann.relations.map((r) => RelationGroup.fromObject(r));

        return new PdfAnnotations(annotations, relations);
    });
}
