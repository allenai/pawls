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
                    // We have to use the message because minification in production obfuscates
                    // the error name.
                    if (err.message.indexOf('Rendering cancelled')) {
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

interface Bounds {
    left: number;
    top: number;
    right: number;
    bottom: number;
}

/**
 * Returns the provided bounds adjusted to be relative to the top-left corner of the provided
 * element.
 */
function relativeTo(bounds: Bounds, container: HTMLElement): Bounds {
    return {
        left: bounds.left - container.offsetLeft,
        top: bounds.top - container.offsetTop,
        right: bounds.right - container.offsetLeft,
        bottom: bounds.bottom - container.offsetTop
    };
}

/**
 * Returns the provided bounds scaled by the provided factor.
 */
function scaled(bounds: Bounds, scale: number): Bounds {
    return {
        left: bounds.left * scale,
        top: bounds.top * scale,
        right: bounds.right * scale,
        bottom: bounds.bottom * scale
    };
}

/**
 * Returns the provided bounds in their normalized form. Normalized means that the left
 * coordinate is always less than the right coordinate, and that the top coordinate is always
 * left than the bottom coordinate.
 *
 * This is required because objects in the DOM are positioned and sized by setting their top-left
 * corner, width and height. This means that when a user composes a selection and moves to the left,
 * or up, from where they started might result in a negative width and/or height. We don't normalize
 * these values as we're tracking the mouse as it'd result in the wrong visual effect. Instead we
 * rotate the bounds we render on the appropriate axis. This means we need to account for this
 * later when calculating what tokens the bounds intersect with.
 */
function normalizeBounds(b: Bounds): Bounds {
    const normalized = Object.assign({}, b);
    if (b.right < b.left) {
        const l = b.left;
        normalized.left = b.right;
        normalized.right = l;
    }
    if (b.bottom < b.top) {
        const t = b.top;
        normalized.top = b.bottom;
        normalized.bottom = t;
    }
    return normalized;
}

/**
 * Returns true if the provided bounds overlap.
 */
function doOverlap(a: Bounds, b: Bounds): boolean {
    if (a.left >= b.right || a.right <= b.left) {
        return false;
    } else if (a.bottom <= b.top || a.top >= b.bottom) {
        return false;
    }
    return true;
}

interface WithErrorCallback {
    onError: (e: Error) => void;
}

interface PageProps extends WithErrorCallback {
    page: PDFPageProxy;
    tokens: Token[];
    selection?: Bounds;
}

const Page = ({ page, tokens, selection, onError }: PageProps) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
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
        <PageAnnotationsContainer ref={containerRef}>
            <PageCanvas ref={canvasRef} />
            {// We only render the tokens if the page is visible, as rendering them all makes the
             // page slow and/or crash.
                isVisible && tokens.map((t, i) => {
                    // Calculate the bounds of the token. We have to scale the bounds so that
                    // they're relative to the viewport, as the values are relative to the PDF
                    // document.
                    const tokenBounds = scaled({
                        left: t.x,
                        top: t.y,
                        right: t.x + t.width,
                        bottom: t.y + t.height
                    }, scale);

                    const isSelected = (selection && containerRef.current) ? (
                        doOverlap(
                            normalizeBounds(relativeTo(selection, containerRef.current)),
                            tokenBounds
                        )
                    ) : false;
                    return (
                        <TokenSpan
                            key={i}
                            isSelected={isSelected}
                            style={{
                                left: `${tokenBounds.left}px`,
                                top: `${tokenBounds.top}px`,
                                width: `${tokenBounds.right - tokenBounds.left}px`,
                                height: `${tokenBounds.bottom - tokenBounds.top}px`
                            }} />
                        )
                })}
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

interface SelectionProps {
   bounds: Bounds;
}

const Selection = ({ bounds }: SelectionProps) => {
    const width = bounds.right - bounds.left;
    const height = bounds.bottom - bounds.top;
    const rotateY = width < 0 ? -180 : 0;
    const rotateX = height < 0 ? -180 : 0;
    return (
        <SelectionBounds
            style={{
                left: `${bounds.left}px`,
                top: `${bounds.top}px`,
                width: `${Math.abs(width)}px`,
                height: `${Math.abs(height)}px`,
                transform: `rotateY(${rotateY}deg) rotateX(${rotateX}deg)`,
                transformOrigin: 'top left'
            }} />
    );
}

interface PDFProps extends WithDoc {
    tokens: TokensBySourceId;
}

export const PDF = (props: PDFProps) => {
    const [ err, setError ] = useState<Error>();
    if (err) {
        console.error(`Error rendering PDF: `, err);
    }

    const containerRef = useRef<HTMLDivElement>(null);
    const [ selection, setSelection ] = useState<Bounds>();

    const pageNos = [];
    const grobidTokensByPage: Token[][] = [];
    for (let i = 0; i < props.doc.numPages; i++) {
        pageNos.push(i + 1);
        const pageTokens = (
            i in props.tokens[SourceId.GROBID].pages
                ? props.tokens[SourceId.GROBID].pages[i].tokens
                : []
        );
        grobidTokensByPage.push(pageTokens);
    }

    return (
        err ? (
            <Result
                status="warning"
                title="Unable to Render PDF" />
        ) : (
            <PDFAnnotationsContainer
                ref={containerRef}
                onMouseDown={(event) => {
                    if (containerRef.current === null) {
                        throw new Error('No Container');
                    }
                    if (!selection) {
                        const left = event.pageX - containerRef.current.offsetLeft;
                        const top = event.pageY - containerRef.current.offsetTop;
                        setSelection({
                            left,
                            top,
                            right: left + 10,
                            bottom: top + 10
                        });
                    }
                }}
                onMouseMove={selection ? (
                    (event) => {
                        if (containerRef.current === null) {
                            throw new Error('No Container');
                        }
                        setSelection({
                            ...selection,
                            right: event.pageX - containerRef.current.offsetLeft,
                            bottom: event.pageY - containerRef.current.offsetTop
                        });
                    }
                ) : undefined}
                onMouseUp={selection ? (
                    () => {
                        // TODO (@codeviking): Capture the current selection and save it.
                        setSelection(undefined);
                    }
                ) : undefined}
            >
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
                                selection={selection}
                                onError={setError} />
                        )}
                    </WithPage>
                ))}
                {selection ? <Selection bounds={selection} /> : null}
            </PDFAnnotationsContainer>
        )
    );
};



const PDFAnnotationsContainer = styled.div`
    position: relative;
`;

const SelectionBounds = styled.div(({ theme }) => `
    position: absolute;
    border: 1px dotted ${theme.color.G4};
`);

interface TokenSpanProps {
    isSelected?: boolean;
}

const TokenSpan = styled.span<TokenSpanProps>(({ theme, isSelected }) =>`
    position: absolute;
    background: ${isSelected ? theme.color.B6 : 'none'};
    opacity: 0.4;
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

