import React, { useContext, useState, useEffect } from 'react';
import styled, { ThemeContext } from 'styled-components';
import { useParams } from 'react-router-dom';
import pdfjs from 'pdfjs-dist';
import { Result, Progress } from '@allenai/varnish';
import { QuestionCircleOutlined } from '@ant-design/icons';

import { PDF, CenterOnPage } from '../components';
import { SourceId, pdfURL, getTokens, Token, TokensResponse } from '../api';
import { PDFPageInfo, TokenSpanAnnotation, AnnotationStore, PDFStore } from '../context';

// This tells PDF.js the URL the code to load for it's webworker, which handles heavy-handed
// tasks in a background thread. Ideally we'd load this from the application itself rather
// than from the CDN to keep things local.
// TODO (@codeviking): Figure out how to get webpack to package up the PDF.js webworker code.
pdfjs.GlobalWorkerOptions.workerSrc =
    `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.js`;

// This callback exists in the source code, but not in the TypeScript types. So we mix it in
// to make TypeScript happy.
// See: https://github.com/mozilla/pdf.js/blob/master/src/display/api.js#L510
interface PDFLoadingTask extends pdfjs.PDFLoadingTask<pdfjs.PDFDocumentProxy> {
    onProgress?: (p: pdfjs.PDFProgressData) => void;
}

enum ViewState {
    LOADING, LOADED, NOT_FOUND, ERROR
}

export const PDFPage = () => {
    const { sha } = useParams<{ sha: string }>();
    const [ viewState, setViewState ] = useState<ViewState>(ViewState.LOADING);

    const [ doc, setDocument ] = useState<pdfjs.PDFDocumentProxy>();
    const [ progress, setProgress ] = useState(0);
    const [ pages, setPages ] = useState<PDFPageInfo[]>();
    const [ tokenSpanAnnotations, setTokenSpanAnnotations ] = useState<TokenSpanAnnotation[]>([]);
    const [ selectedTokenSpanAnnotation, setSelectedTokenSpanAnnotation ] =
        useState<TokenSpanAnnotation>();

    const theme = useContext(ThemeContext);

    useEffect(() => {
        setDocument(undefined);
        const loadingTask: PDFLoadingTask = pdfjs.getDocument(pdfURL(sha))
        loadingTask.onProgress = (p: pdfjs.PDFProgressData) => {
            setProgress(Math.round(p.loaded / p.total * 100));
        };
        Promise.all([
            // PDF.js uses their own `Promise` type, which according to TypeScript doesn't overlap
            // with the base `Promise` interface. To resolve this we (unsafely) cast the PDF.js
            // specific `Promise` back to a generic one. This works, but might have unexpected
            // side-effects, so we should remain wary of this code.
            loadingTask.promise as unknown as Promise<pdfjs.PDFDocumentProxy>,
            getTokens(sha)
        ]).then(([ doc, resp ]: [ pdfjs.PDFDocumentProxy, TokensResponse ]) => {
            setDocument(doc);

            // Load all the pages too. In theory this makes things a little slower to startup,
            // as fetching and rendering them asynchronously would make it faster to render the
            // first, visible page. That said it makes the code simpler, so we're ok with it for
            // now.
            const loadPages: Promise<PDFPageInfo>[] = [];
            for (let i = 1; i <= doc.numPages; i++) {
                // See line 50 for an explanation of the cast here.
                loadPages.push(
                    doc.getPage(i).then(p => {
                        let pageTokens: Token[] = [];
                        if (resp.tokens) {
                            const grobidTokensByPage = resp.tokens.sources[SourceId.GROBID].pages;
                            const pageIndex = p.pageNumber - 1;
                            if (pageIndex in grobidTokensByPage) {
                                pageTokens = grobidTokensByPage[pageIndex].tokens;
                            }
                        }
                        return new PDFPageInfo(p, pageTokens, 1);
                    }) as unknown as Promise<PDFPageInfo>
                );
            }
            return Promise.all(loadPages);
        }).then(pages => {
            setPages(pages);
            setViewState(ViewState.LOADED);
        }).catch((err: any) => {
            if (err instanceof Error) {
                // We have to use the message because minification in production obfuscates
                // the error name.
                if (err.message === 'Request failed with status code 404') {
                    setViewState(ViewState.NOT_FOUND);
                    return;
                }
            }
            console.error(`Error Loading PDF: `, err);
            setViewState(ViewState.ERROR);
        });
    }, [ sha ]);

    switch (viewState) {
        case ViewState.LOADING:
            return (
                <CenterOnPage>
                    <Progress
                        type="circle"
                        percent={progress}
                        strokeColor={{ '0%': theme.color.T6, '100%': theme.color.G6 }} />
                </CenterOnPage>
            );
        case ViewState.NOT_FOUND:
            return (
                <CenterOnPage>
                    <Result
                        icon={<QuestionCircleOutlined />}
                        title="PDF Not Found" />
                </CenterOnPage>
            );
        case ViewState.LOADED:
            if (doc) {
                const sidebarWidth = "300px";
                return (
                    <PDFStore.Provider value={{
                        doc,
                        pages,
                        setError: (err) => {
                            console.error('Unexpected Error rendering PDF', err);
                            setViewState(ViewState.ERROR);
                        }
                    }}>
                        <AnnotationStore.Provider
                            value={{
                                tokenSpanAnnotations,
                                setTokenSpanAnnotations,
                                selectedTokenSpanAnnotation,
                                setSelectedTokenSpanAnnotation
                            }}
                        >
                            <WithSidebar width={sidebarWidth}>
                                <Sidebar width={sidebarWidth}>
                                    <h4>Annotations</h4>
                                    <h5>Tokens</h5>
                                    {tokenSpanAnnotations.length === 0 ? (
                                        <>None</>
                                    ) : (
                                        <ul>
                                            {tokenSpanAnnotations.map((t, i) => (
                                                <li
                                                    key={i}
                                                    onMouseEnter={(_) => {
                                                        setSelectedTokenSpanAnnotation(t)
                                                    }}
                                                    onMouseLeave={() => {
                                                        setSelectedTokenSpanAnnotation(undefined)
                                                    }}
                                                 >
                                                    Annotation #{i + 1}
                                                </li>
                                            ))}
                                        </ul>
                                    )}
                                </Sidebar>
                                <PDFContainer>
                                    <PDF />
                                </PDFContainer>
                            </WithSidebar>
                        </AnnotationStore.Provider>
                    </PDFStore.Provider>
                );
            }
        // eslint-disable-line: no-fallthrough
        case ViewState.ERROR:
            return (
                <CenterOnPage>
                    <Result
                        status="warning"
                        title="Unable to Render Document" />
                </CenterOnPage>
            );
    }
};

interface HasWidth {
    width: string;
}

const WithSidebar = styled.div<HasWidth>(({ width }) =>`
    display: grid;
    flex-grow: 1;
    grid-template-columns: minmax(0, 1fr);
    padding-left: ${width};
`);

const Sidebar = styled.div<HasWidth>(({ theme, width }) => `
    width: ${width};
    position: fixed;
    left: 0;
    overflow-y: scroll;
    background: ${theme.color.N10};
    color: ${theme.color.N1};
    padding: ${theme.spacing.lg} ${theme.spacing.xl};
    height: 100vh;
`);


const PDFContainer = styled.div(({ theme }) => `
    background: ${theme.color.N4};
    padding: ${theme.spacing.sm};
`);
