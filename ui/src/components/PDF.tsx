import React, { useRef, useEffect, useState }  from 'react';
import styled from 'styled-components';
import { PDFPageProxy, PDFDocumentProxy, PDFRenderTask } from 'pdfjs-dist';
import { Result } from '@allenai/varnish';

import { Token, TokensBySourceId, SourceId } from '../api';

class PDFPageRenderer {
    private currentRenderTask?: PDFRenderTask;
    public scale: number = 1;
    constructor(
        readonly page: PDFPageProxy,
        readonly canvas: HTMLCanvasElement | null,
    ) {}
    cancelCurrentRender(onError: (e: Error) => void) {
        if (this.currentRenderTask === undefined) {
            return;
        }
        this.currentRenderTask.promise.then(
            () => {},
            (err: any) => {
                if (err instanceof Error) {
                    if (err.name !== 'RenderingCancelledException') {
                        onError(err);
                    }
                } else {
                    onError(new Error(err));
                }
            }
        );
        this.currentRenderTask.cancel();
    }
    render() {
        if (this.canvas === null) {
            throw new Error('No canvas');
        }
        if (this.canvas.parentElement === null) {
            throw new Error('The canvas element has no parent');
        }
        const width = this.page.view[2] - this.page.view[1];

        // Scale it so the user doesn't have to scroll horizontally
        const parent = this.canvas.parentElement;
        const parentStyles = getComputedStyle(parent);
        const padding =
            parseFloat(parentStyles.paddingLeft || "0") +
            parseFloat(parentStyles.paddingRight || "0");

        this.scale = Math.max((this.canvas.parentElement.clientWidth - padding) / width);
        const viewport = this.page.getViewport({ scale: this.scale });

        this.canvas.height = viewport.height;
        this.canvas.width = viewport.width;

        const canvasContext = this.canvas.getContext('2d');
        if (canvasContext === null) {
            throw new Error('No canvas context');
        }
        this.currentRenderTask = this.page.render({ canvasContext, viewport });
        return this.currentRenderTask;
    }
    rescaleAndRender(onError: (e: Error) => void) {
        this.cancelCurrentRender(onError);
        return this.render();
    }
}

interface WithErrorCallback {
    onError: (e: Error) => void;
}

interface PageProps extends WithErrorCallback {
    page: PDFPageProxy;
    tokens: Token[];
}

const Page = ({ page, tokens, onError }: PageProps) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [ scale, setScale ] = useState<number>(1);
    const [ isVisible, setIsVisible ] = useState<boolean>(false);

    useEffect(() => {
        try {
            const determinePageVisiblity = () => {
                if (canvasRef.current !== null) {
                    const windowTop = 0;
                    const windowBottom = window.innerHeight;
                    const rect = canvasRef.current.getBoundingClientRect();
                    setIsVisible(
                        (rect.top > windowTop && rect.top < windowBottom) ||
                        (rect.bottom > windowTop && rect.bottom < windowBottom) ||
                        (rect.top < windowTop && rect.bottom > windowTop)
                    );
                }
            };

            const renderer = new PDFPageRenderer(page, canvasRef.current);
            renderer.render();
            setScale(renderer.scale);
            determinePageVisiblity();

            const handleResize = () => {
                renderer.rescaleAndRender(onError)
                setScale(renderer.scale);
                determinePageVisiblity();
            };
            window.addEventListener('resize', handleResize);
            window.addEventListener('scroll', determinePageVisiblity);
            return () => {
                window.removeEventListener('resize', handleResize)
                window.removeEventListener('scroll', determinePageVisiblity);
            };
        } catch (e) {
            onError(e);
        }
    }, [ page, onError ]);

    return (
        <PageAnnotationsContainer>
            <PageCanvas ref={canvasRef} />
            {// We only render the tokens if the page is visible, as rendering them all makes the
             // page slow and/or crash.
            isVisible && tokens.map((t, i) => (
                <TokenSpan
                    key={i}
                    style={{
                        left: t.x * scale,
                        top: t.y * scale,
                        width: t.width * scale,
                        height: t.height * scale
                    }} />
            ))}
        </PageAnnotationsContainer>
    );
};

interface WithDoc {
    doc: PDFDocumentProxy;
}

interface WithPageProps extends WithDoc, WithErrorCallback {
    page: number;
    children: (page: PDFPageProxy) => React.ReactNode;
}

const WithPage = ({ doc, page, onError, children }: WithPageProps) => {
    const [ pdfPage, setPdfPage ] = useState<PDFPageProxy>();
    const pageNo = page || 1;

    useEffect(() => {
        doc.getPage(pageNo).then(
            (page: PDFPageProxy) => {
                setPdfPage(page);
            },
            reason => {
                onError(new Error(reason));
            }
        );
    }, [ doc, pageNo, onError ]);

    // TODO (@codeviking): The `getPage()` call above returns fast enough that we don't have
    // any type of interstitial display here. We probably should put one in place for slower
    // clients.
    return pdfPage ? <>{children(pdfPage)}</> : null;
};

interface PDFProps extends WithDoc {
    tokens: TokensBySourceId;
}

export const PDF = (props: PDFProps) => {
    const [ err, setError ] = useState<Error>();
    if (err) {
        console.error(`Error rendering PDF: `, err);
    }
    const pageNos = [];
    const grobidTokensByPage: Token[][] = [];
    for (let i = 0; i < props.doc.numPages; i++) {
        pageNos.push(i + 1);
        grobidTokensByPage.push(
            i in props.tokens[SourceId.GROBID].pages
                ? props.tokens[SourceId.GROBID].pages[i].tokens
                : []
        );
    }
    return (
        err ? (
            <Result
                status="warning"
                title="Unable to Render PDF" />
        ) : (
            <>
                {pageNos.map(pageNo => (
                    <WithPage
                        key={pageNo}
                        doc={props.doc}
                        page={pageNo}
                        onError={setError}
                    >
                        { page => (
                            <Page
                                page={page}
                                tokens={grobidTokensByPage[pageNo - 1]}
                                onError={setError} />
                        )}
                    </WithPage>
                ))}
            </>
        )
    );
};

const TokenSpan = styled.span(({ theme }) =>`
    position: absolute;
    border: 1px dotted ${theme.color.B4};
`);

const PageAnnotationsContainer = styled.div(({ theme }) =>`
    position: relative;
    box-shadow: 2px 2px 4px 0 rgba(0, 0, 0, 0.2);
    margin: 0 0 ${theme.spacing.xs};

    &:last-child {
        margin-bottom: 0;
    }
`);

const PageCanvas = styled.canvas`
    display: block;
`;

