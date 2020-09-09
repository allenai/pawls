import React, { useContext, useRef, useEffect, useState }  from 'react';
import styled from 'styled-components';
import { PDFPageProxy, PDFRenderTask } from 'pdfjs-dist';

import { Token } from '../api';
import { merge, TokenSpanAnnotation, PDFPageInfo, AnnotationStore, PDFStore, Bounds } from '../context';

class PDFPageRenderer {
    private currentRenderTask?: PDFRenderTask;
    constructor(
        readonly page: PDFPageProxy,
        readonly canvas: HTMLCanvasElement,
        readonly onError: (e: Error) => void
    ) {}
    cancelCurrentRender() {
        if (this.currentRenderTask === undefined) {
            return;
        }
        this.currentRenderTask.promise.then(
            () => {},
            (err: any) => {
                if (
                    err instanceof Error
                    && err.message.indexOf('Rendering cancelled') !== -1
                ) {
                    // Swallow the error that's thrown when the render is canceled.
                    return;
                }
                const e = err instanceof Error ? err : new Error(err);
                this.onError(e);
            }
        );
        this.currentRenderTask.cancel();
    }
    render(scale: number) {
        const viewport = this.page.getViewport({ scale });

        this.canvas.height = viewport.height;
        this.canvas.width = viewport.width;

        const canvasContext = this.canvas.getContext('2d');
        if (canvasContext === null) {
            throw new Error('No canvas context');
        }
        this.currentRenderTask = this.page.render({ canvasContext, viewport });
        return this.currentRenderTask;
    }
    rescaleAndRender(scale: number) {
        this.cancelCurrentRender();
        return this.render(scale);
    }
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

function getPageBoundsFromCanvas(canvas: HTMLCanvasElement): Bounds {
    if (canvas.parentElement === null) {
        throw new Error('No canvas parent');
    }
    const parent = canvas.parentElement;
    const parentStyles = getComputedStyle(canvas.parentElement);

    const leftPadding = parseFloat(parentStyles.paddingLeft || "0");
    const left = parent.offsetLeft + leftPadding;

    const topPadding = parseFloat(parentStyles.paddingTop || "0");
    const top = parent.offsetTop + topPadding;

    const parentWidth =
        parent.clientWidth - leftPadding - parseFloat(parentStyles.paddingRight || "0");
    const parentHeight =
        parent.clientHeight - topPadding - parseFloat(parentStyles.paddingBottom || "0");
    return {
        left,
        top,
        right: left + parentWidth,
        bottom: top + parentHeight
    };
}

interface PageProps {
    pageInfo: PDFPageInfo;
    selection?: Bounds;
    selectedTokens?: Token[];
    onError: (e: Error) => void;
}

const Page = ({ pageInfo, selectedTokens, onError }: PageProps) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
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

            if (canvasRef.current === null) {
                onError(new Error('No canvas element'));
                return;
            }

            pageInfo.bounds = getPageBoundsFromCanvas(canvasRef.current);
            const renderer = new PDFPageRenderer(pageInfo.page, canvasRef.current, onError);
            renderer.render(pageInfo.scale);

            determinePageVisiblity();

            const handleResize = () => {
                if (canvasRef.current === null) {
                    onError(new Error('No canvas element'));
                    return;
                }
                pageInfo.bounds = getPageBoundsFromCanvas(canvasRef.current)
                renderer.rescaleAndRender(pageInfo.scale);
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
    }, [ pageInfo, onError ]); // We deliberately only run this once.

    return (
        <PageAnnotationsContainer>
            <PageCanvas ref={canvasRef} />
            {// We only render the tokens if the page is visible, as rendering them all makes the
             // page slow and/or crash.
                isVisible && selectedTokens && selectedTokens.map((t, i) => {
                    const b = pageInfo.getScaledTokenBounds(t);
                    return (
                        <TokenSpan
                            key={i}
                            isSelected={true}
                            style={{
                                left: `${b.left}px`,
                                top: `${b.top}px`,
                                width: `${b.right - b.left}px`,
                                height: `${b.bottom - b.top}px`
                            }} />
                        )
                })}
        </PageAnnotationsContainer>
    );
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

export const PDF = () => {
    const containerRef = useRef<HTMLDivElement>(null);
    const [ selection, setSelection ] = useState<Bounds>();

    const pdfStore = useContext(PDFStore);
    const annotationStore = useContext(AnnotationStore);

    // TODO (@codeviking): Use error boundaries to capture these.
    if (!pdfStore.doc) {
        throw new Error('No Document');
    }
    if (!pdfStore.pages) {
        throw new Error('Document without Pages');
    }

    return (
        <PDFAnnotationsContainer
            ref={containerRef}
            onMouseDown={(event) => {
                if (containerRef.current === null) {
                    throw new Error('No Container');
                }
                // Clear the selected annotation, if there is one.
                // TODO (@codeviking): This might change.
                annotationStore.setSelectedTokenSpanAnnotation(undefined);
                if (!selection) {
                    const left = event.pageX - containerRef.current.offsetLeft;
                    const top = event.pageY - containerRef.current.offsetTop;
                    setSelection({
                        left,
                        top,
                        right: left,
                        bottom: top
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
                    if (pdfStore.doc && pdfStore.pages) {
                        const annotations: TokenSpanAnnotation[] = []

                        // Loop over all pages to find tokens that intersect with the current
                        // selection, since we allow selections to cross page boundaries.
                        for (let i = 0; i < pdfStore.doc.numPages; i++) {
                            const p = pdfStore.pages[i];
                            const annotation = p.getIntersectingTokenIds(normalizeBounds(selection))
                            annotations.push(annotation);
                        }

                        if (annotations.length > 0) {


                            const combined = annotations.reduce((prev, current, i, arr) => {
                                return merge(prev, current)
                            })
                            const withNewAnnotation =
                                annotationStore.tokenSpanAnnotations.concat([ combined ])
                            annotationStore.setTokenSpanAnnotations(withNewAnnotation);
                        }
                    }
                    setSelection(undefined);

                }
            ) : undefined}
        >
            {pdfStore.pages.map((p, pageIndex) => {
                let selectedTokens: Token[] = [];
                // If the user is selecting something, display that. Otherwise display the
                // currently selection annotation.
                // TODO (@codeviking): We probably eventually want to display both.
                if (selection) {
                    selectedTokens = p.getIntersectingTokens(normalizeBounds(selection));
                } else if (annotationStore.selectedTokenSpanAnnotation) {
                    // This is an o(n) scan over the already selected tokens for every page. If this gets too expensive we could
                    // use a dictionary to make the lookup faster. That said I bet it's fine for
                    // the scale we're talking about.
                    for (const tokenId of annotationStore.selectedTokenSpanAnnotation.tokens) {
                        if (tokenId.pageIndex === pageIndex) {
                            selectedTokens.push(p.tokens[tokenId.tokenIndex]);
                        }
                    }
                }

                return (
                    <Page
                        key={p.page.pageNumber}
                        pageInfo={p}
                        selectedTokens={selectedTokens}
                        onError={pdfStore.onError} />
                );
            })}
            {selection ? <Selection bounds={selection} /> : null}
            {annotationStore.selectedTokenSpanAnnotation ? <Selection bounds={annotationStore.selectedTokenSpanAnnotation.bounds} /> : null}
        </PDFAnnotationsContainer>
    );
};



const PDFAnnotationsContainer = styled.div`
    position: relative;
`;

const SelectionBounds = styled.div(({ theme }) => `
    position: absolute;
    border: 2px dotted ${theme.color.G4};
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
