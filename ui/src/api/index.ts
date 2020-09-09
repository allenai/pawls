import axios from 'axios';

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

interface PageTokens {
    page: Page;
    tokens: Token[];
}

interface Style {
    size: number;
    font_style?: string;
    color: number;
    font_type?: string;
    family?: string;
    width?: number;
}

interface DocumentTokens {
    pages: PageTokens[];
    // TODO (@MarkN, @codeviking): I don't think we use these, so we should probably drop them
    // from the response. It might make things a little smaller.
    styles: { [name: string]: Style };
}

// There's only one right now.
export enum SourceId {
    GROBID = "grobid"
};

export interface TokensBySourceId {
    [sourceId: string]: DocumentTokens;
}

export interface TokensResponse {
    tokens: { sources: TokensBySourceId };
}

function docURL(sha: string): string {
    return `/api/doc/${sha}`;
}

export function pdfURL(sha: string): string {
    return `${docURL(sha)}/pdf`;
}

export async function getTokens(sha: string): Promise<TokensResponse> {
    return axios.get(`${docURL(sha)}/tokens`)
                .then(r => r.data);
}

export async function getLabels(): Promise<string[]> {
    return axios.get("/api/annotation/labels")
                .then(r => r.data)
}


export interface PaperMetadata {

    sha: string,
    title: string,
    venue: string,
    year: number,
    cited_by: number,
    authors: string[]
}

export async function getAssignedPapers(): Promise<PaperMetadata[]> {
    return axios.get("/api/annotation/allocation/metadata")
                .then(r => r.data)
}
